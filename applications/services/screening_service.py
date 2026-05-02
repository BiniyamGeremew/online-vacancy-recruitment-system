from decimal import Decimal
import logging
from django.db import models

from applicant.models import ApplicantDocument
from .cv_parser import extract_text_from_cv
from .ai_parser import parse_cv_with_ai
from .tfidf_service import calculate_tfidf_similarity
from .ai_scoring_service import evaluate_candidate_with_ai


logger = logging.getLogger(__name__)


class ScreeningService:
    """
    Modern ATS screening service for job applications.
    Handles eligibility checks and AI-powered scoring.
    """

    @staticmethod
    def check_eligibility(profile, position):
        """
        Check if applicant is eligible for the position.
        Returns: (is_eligible, rejection_reason)
        """
        reasons = []

        # CGPA check
        applicant_cgpa = profile.qualifications.aggregate(
            max_cgpa=models.Max('grade')
        )['max_cgpa']

        if applicant_cgpa is None or applicant_cgpa < position.minimum_cgpa:
            reasons.append(
                "Your CGPA does not meet the minimum requirement for this position."
            )

        # Required documents
        uploaded_types = set(
            profile.documents.values_list('document_type', flat=True)
        )

        if ApplicantDocument.DOCUMENT_RESUME not in uploaded_types:
            reasons.append("CV/Resume document is required")

        is_eligible = len(reasons) == 0
        rejection_reason = "; ".join(reasons) if reasons else None

        return is_eligible, rejection_reason

    @staticmethod
    def process_application(application):
        """
        Process application through the ATS pipeline.
        Returns: (ranking_score, ai_summary)
        """
        try:
            # Extract CV text
            cv_text = ScreeningService._extract_cv_text(application.applicant)

            logger.debug(f"CV TEXT LENGTH: {len(cv_text)}")

            # Parse CV using AI
            parsed_data = ScreeningService._parse_cv_with_ai(cv_text)

            # Calculate TF-IDF similarity
            tfidf_score = ScreeningService._calculate_tfidf_score(
                application.position,
                cv_text
            )

            logger.debug(f"TFIDF SCORE: {tfidf_score}")

            # AI evaluation
            ai_score, ai_summary = ScreeningService._evaluate_with_ai(
                application.position,
                parsed_data
            )

            logger.debug(f"AI SCORE: {ai_score}")

            # Final ranking score
            final_score = ScreeningService._calculate_final_score(
                tfidf_score,
                ai_score
            )

            final_score = ScreeningService._normalize_score(final_score)

            logger.info(f"FINAL SCREENING SCORE: {final_score}")

            return final_score, ai_summary

        except Exception as e:
            logger.error(f"ATS PIPELINE ERROR: {str(e)}", exc_info=True)
            return Decimal('0.00'), f"Error during screening: {str(e)}"

    @staticmethod
    def _extract_cv_text(profile):
        """Extract text from applicant CV."""
        cv_doc = profile.documents.filter(
            document_type=ApplicantDocument.DOCUMENT_RESUME
        ).first()

        if not cv_doc:
            raise ValueError("No CV document found")

        if not getattr(cv_doc, 'file', None) or not getattr(cv_doc.file, 'name', None):
            raise ValueError("Resume file is missing or inaccessible")

        cv_text = extract_text_from_cv(cv_doc.file)

        if not cv_text or not cv_text.strip():
            raise ValueError("Extracted CV text is empty")

        return cv_text

    @staticmethod
    def _parse_cv_with_ai(cv_text):
        """Parse CV using AI."""
        return parse_cv_with_ai(cv_text)

    @staticmethod
    def _calculate_tfidf_score(position, cv_text):
        """Calculate TF-IDF similarity score."""
        job_description = ScreeningService._build_job_description(position)
        return calculate_tfidf_similarity(job_description, cv_text)

    @staticmethod
    def _evaluate_with_ai(position, parsed_data):
        """Evaluate candidate using AI."""
        vacancy = position.vacancy

        vacancy_title = ''
        if getattr(vacancy, 'employee_request', None):
            vacancy_title = getattr(vacancy.employee_request, 'subject', '') or ''

        vacancy_info = {
            'title': vacancy_title,
            'description': vacancy.announcement_text or '',
            'required_skills': vacancy.required_skills or '',
            'field_of_study': position.field_of_education or '',
            'minimum_cgpa': position.minimum_cgpa,
        }

        return evaluate_candidate_with_ai(vacancy_info, parsed_data)

    @staticmethod
    def _calculate_final_score(tfidf_score, ai_score):
        """Combine TF-IDF and AI scores."""
        try:
            return (
                Decimal('0.6') * Decimal(str(tfidf_score))
                + Decimal('0.4') * Decimal(str(ai_score))
            )
        except Exception:
            return Decimal('0.00')

    @staticmethod
    def _build_job_description(position):
        """Build job description text used for TF-IDF comparison."""
        vacancy = position.vacancy

        parts = [
            getattr(vacancy.employee_request, 'subject', '')
            if getattr(vacancy, 'employee_request', None) else '',
            vacancy.announcement_text or '',
            vacancy.required_skills or '',
            position.field_of_education or '',
            f"Minimum CGPA: {position.minimum_cgpa}"
            if position.minimum_cgpa is not None else '',
        ]

        return " ".join(
            part.strip() for part in parts if part and str(part).strip()
        )

    @staticmethod
    def _normalize_score(score):
        """Ensure final score stays between 0 and 100."""
        try:
            value = Decimal(str(score))
        except Exception:
            value = Decimal('0.00')

        if value < 0:
            value = Decimal('0.00')

        if value > 100:
            value = Decimal('100.00')

        return value.quantize(Decimal('0.01'))