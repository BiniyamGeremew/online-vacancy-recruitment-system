import json
from decimal import Decimal
from typing import List, Dict, Any

from django.core.cache import cache
from django.conf import settings

from .ai_exam_generator import generate_exam_questions
from ..models import Exam, Question, Choice


class AIQuestionService:
    """Service for handling AI-generated questions workflow."""

    LETTERS = ["A", "B", "C", "D"]

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

        ai_questions = generate_exam_questions(
            vacancy,
            num_questions=total_questions,
            difficulty=difficulty,
            mcq_count=mcq_count,
            short_answer_count=short_answer_count,
        )

        if len(ai_questions) != total_questions:
            return []

        questions_data = []

        for i, q in enumerate(ai_questions, 1):

            question_type = q.get("question_type", Question.TYPE_MCQ)

            question_data = {
                "question_text": q["text"],
                "question_type": question_type,
                "marks": q.get("marks", 1),
                "order": i,
                "status": Question.STATUS_DRAFT,
            }

            # Handle MCQ questions
            if question_type == Question.TYPE_MCQ:

                choices = q.get("choices", [])

                # Ensure exactly 4 choices
                while len(choices) < 4:
                    choices.append(f"Option {len(choices)+1}")

                choices = choices[:4]

                correct_answer = q.get("correct_answer")
                correct_letter = "A"

                if isinstance(correct_answer, str):
                    normalized_answer = correct_answer.strip()
                    if normalized_answer.upper() in AIQuestionService.LETTERS:
                        correct_letter = normalized_answer.upper()
                    else:
                        for index, choice in enumerate(choices):
                            if choice.strip().lower() == normalized_answer.lower():
                                correct_letter = AIQuestionService.LETTERS[index]
                                break

                question_data["choices"] = choices
                question_data["correct_answer"] = correct_letter

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

        exam.questions.filter(status=Question.STATUS_DRAFT).delete()

        total_marks = 0
        current_order = 0

        for q_data in questions_data:

            current_order += 1

            marks = q_data.get("marks", 1)

            order = (
                q_data.get("order")
                if isinstance(q_data.get("order"), int) and q_data.get("order") > 0
                else current_order
            )

            question = Question.objects.create(
                exam=exam,
                question_text=q_data["question_text"],
                question_type=q_data["question_type"],
                marks=marks,
                order=order,
                status=Question.STATUS_DRAFT,
            )

            total_marks += marks

            # Create MCQ choices
            if question.question_type == Question.TYPE_MCQ:

                choices = q_data.get("choices", [])[:4]
                correct_answer = q_data.get("correct_answer", "A")

                # Determine correct index
                if isinstance(correct_answer, str) and correct_answer.upper() in AIQuestionService.LETTERS:
                    correct_index = AIQuestionService.LETTERS.index(correct_answer.upper())
                else:
                    # Find the index of the choice that matches the correct_answer text
                    correct_index = 0
                    for index, choice_text in enumerate(choices):
                        if choice_text.strip().lower() == str(correct_answer).strip().lower():
                            correct_index = index
                            break

                for index, choice_text in enumerate(choices):
                    Choice.objects.create(
                        question=question,
                        option_text=choice_text,
                        is_correct=index == correct_index,
                    )

        exam.total_marks = total_marks
        exam.pass_mark = int(Decimal(total_marks) * Decimal("0.5")) if total_marks else 0
        exam.save(update_fields=["total_marks", "pass_mark"])

    @staticmethod
    def clear_session_questions(request, exam_id: int) -> None:
        """Clear questions from session."""
        session_key = f"exam_{exam_id}_ai_questions"

        if session_key in request.session:
            del request.session[session_key]
            request.session.modified = True