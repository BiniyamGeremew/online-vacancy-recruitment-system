from django.db import models
from django.conf import settings
from django.utils import timezone

from department_head.models import EmployeeRequest
from applicant.models import ApplicantProfile
from organization.models import Department


class HRProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hrprofile'
    )
    phone_number = models.CharField(max_length=32, blank=True)
    office_location = models.CharField(max_length=128, blank=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - HR Officer"


class HRAction(models.Model):

    ACTION_VACANCY = 'vacancy'
    ACTION_SCREENING = 'screening'
    ACTION_INTERVIEW = 'interview'
    ACTION_HIRED = 'hired'

    ACTION_CHOICES = [
        (ACTION_VACANCY, 'Vacancy Announced'),
        (ACTION_SCREENING, 'Screening'),
        (ACTION_INTERVIEW, 'Interview'),
        (ACTION_HIRED, 'Hiring Completed'),
    ]

    request = models.ForeignKey(
        EmployeeRequest,
        on_delete=models.CASCADE,
        related_name='hr_actions'
    )

    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES
    )

    note = models.TextField(blank=True)

    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='hr_actions'
    )

    performed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-performed_at']

    def __str__(self):
        return f"{self.get_action_display()} on {self.request}"


class Vacancy(models.Model):

    STATUS_DRAFT = 'draft'
    STATUS_PUBLISHED = 'published'
    STATUS_CLOSED = 'closed'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PUBLISHED, 'Published'),
        (STATUS_CLOSED, 'Closed'),
    ]

    VACANCY_INTERNAL = 'internal'
    VACANCY_EXTERNAL = 'external'

    VACANCY_TYPE_CHOICES = [
        (VACANCY_INTERNAL, 'Internal'),
        (VACANCY_EXTERNAL, 'External'),
    ]

    employee_request = models.OneToOneField(
        EmployeeRequest,
        on_delete=models.CASCADE,
        related_name='vacancy'
    )

    vacancy_type = models.CharField(
        max_length=20,
        choices=VACANCY_TYPE_CHOICES
    )

    experience_requirement = models.CharField(
        max_length=255,
        blank=True
    )

    required_skills = models.TextField(blank=True)

    salary_info = models.CharField(
        max_length=255,
        blank=True
    )

    announcement_text = models.TextField(
        blank=True,
        help_text="AI generated + HR edited final vacancy text"
    )

    application_instructions = models.TextField(blank=True)

    announcement_date = models.DateField(default=timezone.now)
    deadline = models.DateField()
    shortlist_finalized = models.BooleanField(default=False)

    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='vacancies_posted'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT
    )

    closed_reason = models.TextField(blank=True, null=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='closed_vacancies'
    )
    closed_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-announcement_date', '-created_at']

    def __str__(self):
        return f"{self.employee_request.subject} ({self.get_status_display()})"


class VacancyPosition(models.Model):

    vacancy = models.ForeignKey(
        Vacancy,
        on_delete=models.CASCADE,
        related_name='positions'
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='vacancy_positions'
    )

    academic_rank = models.CharField(max_length=128)
    field_of_education = models.CharField(max_length=255)
    minimum_cgpa = models.DecimalField(max_digits=4, decimal_places=2)
    positions = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.department.name} - {self.academic_rank} ({self.positions})"


class JobApplication(models.Model):

    STATUS_SUBMITTED = 'submitted'
    STATUS_UNDER_REVIEW = 'under_review'
    STATUS_SHORTLISTED = 'shortlisted'
    STATUS_INTERVIEWED = 'interviewed'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_UNDER_REVIEW, 'Under Review'),
        (STATUS_SHORTLISTED, 'Shortlisted'),
        (STATUS_INTERVIEWED, 'Interviewed'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_applications'
    )

    applicant_profile = models.ForeignKey(
        ApplicantProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_applications'
    )

    vacancy_position = models.ForeignKey(
        VacancyPosition,
        on_delete=models.CASCADE,
        related_name='applications'
    )

    applied_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_SUBMITTED
    )

    class Meta:
        unique_together = ('applicant', 'vacancy_position')
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.applicant.username} - {self.vacancy_position}"