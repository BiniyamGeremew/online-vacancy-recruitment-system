from decimal import Decimal

from django.db import models
from django.utils import timezone

from organization.models import TimeStampedModel
from applicant.models import ApplicantProfile
from hr_officer.models import VacancyPosition


class Application(TimeStampedModel):
    STATUS_SUBMITTED = 'submitted'
    STATUS_ELIGIBLE = 'eligible'
    STATUS_SHORTLISTED = 'shortlisted'
    STATUS_EXAM = 'exam'
    STATUS_REJECTED = 'rejected'
    STATUS_INTERVIEW = 'interview'
    STATUS_FINAL_SELECTION = 'final_selection'

    STATUS_CHOICES = [
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_ELIGIBLE, 'Eligible'),
        (STATUS_SHORTLISTED, 'Shortlisted'),
        (STATUS_EXAM, 'Exam'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_INTERVIEW, 'Interview'),
        (STATUS_FINAL_SELECTION, 'Final Selection'),
    ]

    applicant = models.ForeignKey(
        ApplicantProfile,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    position = models.ForeignKey(
        VacancyPosition,
        on_delete=models.CASCADE,
        related_name='application_applications'
    )
    profile_snapshot = models.JSONField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_SUBMITTED
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    cover_letter = models.TextField(blank=True)
    hr_notes = models.TextField(blank=True)
    ai_summary = models.TextField(blank=True)  # AI-generated candidate evaluation summary
    ranking_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ('applicant', 'position')
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.applicant.user.get_full_name()} - {self.position}"

    def save(self, *args, **kwargs):
        if self.status == self.STATUS_SUBMITTED and not self.submitted_at:
            self.submitted_at = timezone.now()
            self.create_profile_snapshot()

        if self.ranking_score is None:
            self.ranking_score = Decimal('0.00')

        super().save(*args, **kwargs)

    def create_profile_snapshot(self):
        """Create a snapshot of the applicant's profile at submission time."""
        profile = self.applicant
        user = profile.user

        # Personal info
        personal_info = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'mobile_number': profile.mobile_number,
            'father_name': profile.father_name,
            'birth_date': str(profile.birth_date) if profile.birth_date else None,
            'marital_status': profile.marital_status,
            'gender': profile.gender,
            'title': profile.title,
            'country': profile.country,
            'region': profile.region,
            'zone': profile.zone,
            'wereda': profile.wereda,
            'kebele': profile.kebele,
            'house_number': profile.house_number,
            'postal_code': profile.postal_code,
        }

        # Education qualifications
        education = []
        for qual in profile.qualifications.all():
            education.append({
                'institution_name': qual.institution_name,
                'qualification_category': qual.qualification_category,
                'qualification_type': qual.qualification_type,
                'department': qual.department,
                'grade': str(qual.grade),
                'start_date': str(qual.start_date) if qual.start_date else None,
                'end_date': str(qual.end_date) if qual.end_date else None,
                'diploma_certificate': qual.diploma_certificate.url if qual.diploma_certificate else None,
                'transcript': qual.transcript.url if qual.transcript else None,
                'cost_sharing_document': qual.cost_sharing_document.url if qual.cost_sharing_document else None,
            })

        # Employment history
        employment = []
        for emp in profile.employments.all():
            employment.append({
                'job_category': emp.job_category,
                'employer': emp.employer,
                'job_title': emp.job_title,
                'start_date': str(emp.start_date),
                'end_date': str(emp.end_date) if emp.end_date else None,
                'experience_letter': emp.experience_letter.url if emp.experience_letter else None,
            })

        # Documents
        documents = []
        for doc in profile.documents.all():
            documents.append({
                'document_type': doc.document_type,
                'file_url': doc.file.url,
            })

        self.profile_snapshot = {
            'personal_info': personal_info,
            'education': education,
            'employment': employment,
            'documents': documents,
        }
