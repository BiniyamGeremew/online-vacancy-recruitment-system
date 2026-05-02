from typing import Dict, Any, Optional
from django.db import transaction, models

from ..models import Exam, Question, Choice


class ManualQuestionService:
    """Service for handling manual question creation."""

    @staticmethod
    def add_question_to_exam(exam: Exam, question_data: Dict[str, Any]) -> Question:
        """Add a single question to exam as draft."""
        with transaction.atomic():
            # Get next order
            max_order = exam.questions.aggregate(max_order=models.Max('order'))['max_order'] or 0
            next_order = max_order + 1

            question = Question.objects.create(
                exam=exam,
                question_text=question_data["question_text"],
                question_type=question_data["question_type"],
                marks=question_data.get("marks", 1),
                order=next_order,
                status=Question.STATUS_DRAFT
            )

            # Create choices if MCQ
            if question.question_type == Question.TYPE_MCQ:
                choices = question_data.get("choices", [])
                correct_choice = question_data.get("correct_choice")

                for choice_text in choices:
                    is_correct = (choice_text.strip() == correct_choice.strip()) if correct_choice else False
                    Choice.objects.create(
                        question=question,
                        option_text=choice_text.strip(),
                        is_correct=is_correct
                    )

            return question

    @staticmethod
    def update_question(question: Question, question_data: Dict[str, Any]) -> Question:
        """Update an existing draft question."""
        with transaction.atomic():
            question.question_text = question_data["question_text"]
            question.question_type = question_data["question_type"]
            question.marks = question_data.get("marks", 1)
            question.save()

            # Update choices if MCQ
            if question.question_type == Question.TYPE_MCQ:
                # Clear existing choices
                question.choices.all().delete()

                choices = question_data.get("choices", [])
                correct_choice = question_data.get("correct_choice")

                for choice_text in choices:
                    is_correct = (choice_text.strip() == correct_choice.strip()) if correct_choice else False
                    Choice.objects.create(
                        question=question,
                        option_text=choice_text.strip(),
                        is_correct=is_correct
                    )

            return question

    @staticmethod
    def delete_question(question: Question) -> None:
        """Delete a draft question."""
        if question.status == Question.STATUS_DRAFT:
            question.delete()

    @staticmethod
    def reorder_questions(exam: Exam, question_orders: Dict[int, int]) -> None:
        """Reorder questions in exam."""
        with transaction.atomic():
            for question_id, new_order in question_orders.items():
                Question.objects.filter(id=question_id, exam=exam).update(order=new_order)

    @staticmethod
    def get_draft_questions(exam: Exam) -> list:
        """Get all draft questions for exam."""
        return list(exam.questions.filter(status=Question.STATUS_DRAFT).order_by('order'))

    @staticmethod
    def can_publish_exam(exam: Exam) -> bool:
        """Check if exam can be published."""
        return exam.questions.filter(status__in=[Question.STATUS_DRAFT, Question.STATUS_PUBLISHED]).exists()