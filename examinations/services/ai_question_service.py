import json
from typing import List, Dict, Any
from django.core.cache import cache
from django.conf import settings

from .ai_exam_generator import generate_exam_questions
from ..models import Exam, Question, Choice


class AIQuestionService:
    """Service for handling AI-generated questions workflow."""

    @staticmethod
    def generate_questions_for_exam(
        exam: Exam,
        total_questions: int = 10,
        difficulty: str = 'medium',
        mcq_count: int = 10,
        short_answer_count: int = 0,
    ) -> List[Dict[str, Any]]:
        """Generate questions using AI and return structured data."""
        vacancy = exam.vacancy

        # Generate questions using existing AI service with question-type distribution.
        ai_questions = generate_exam_questions(
            vacancy,
            num_questions=total_questions,
            difficulty=difficulty,
            mcq_count=mcq_count,
            short_answer_count=short_answer_count,
        )

        questions_data = []
        for i, q in enumerate(ai_questions, 1):
            question_data = {
                "question_text": q["text"],
                "question_type": q.get("question_type", Question.TYPE_MCQ),
                "marks": q.get("marks", 1),
                "order": i,
                "status": q.get("status", Question.STATUS_DRAFT),
            }

            if question_data["question_type"] == Question.TYPE_MCQ:
                question_data["choices"] = q.get("choices", [])
                question_data["correct_choice"] = q.get("correct_answer")

            questions_data.append(question_data)

        return questions_data

    @staticmethod
    def store_questions_in_session(request, exam_id: int, questions_data: List[Dict[str, Any]]) -> None:
        """Store generated questions in session for review."""
        session_key = f"exam_{exam_id}_ai_questions"
        request.session[session_key] = questions_data
        request.session.modified = True

    @staticmethod
    def get_questions_from_session(request, exam_id: int) -> List[Dict[str, Any]]:
        """Retrieve questions from session."""
        session_key = f"exam_{exam_id}_ai_questions"
        return request.session.get(session_key, [])

    @staticmethod
    def save_questions_to_draft(exam: Exam, questions_data: List[Dict[str, Any]]) -> None:
        """Save questions as draft to database."""
        for q_data in questions_data:
            question = Question.objects.create(
                exam=exam,
                question_text=q_data["question_text"],
                question_type=q_data["question_type"],
                marks=q_data.get("marks", 1),
                order=q_data.get("order", 0),
                status=Question.STATUS_DRAFT
            )

            # Create choices for MCQ
            if question.question_type == Question.TYPE_MCQ:
                for choice_text in q_data["choices"]:
                    is_correct = (choice_text == q_data["correct_choice"])
                    Choice.objects.create(
                        question=question,
                        option_text=choice_text,
                        is_correct=is_correct
                    )

    @staticmethod
    def clear_session_questions(request, exam_id: int) -> None:
        """Clear questions from session."""
        session_key = f"exam_{exam_id}_ai_questions"
        if session_key in request.session:
            del request.session[session_key]
            request.session.modified = True