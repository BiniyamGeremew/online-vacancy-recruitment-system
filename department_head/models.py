from django.db import models
from django.conf import settings

from organization.models import TimeStampedModel
from organization.constants import RequestStatus


class EmployeeRequest(TimeStampedModel):
    STATUS_SUBMITTED = RequestStatus.SUBMITTED
    STATUS_APPROVED_BY_DEAN = RequestStatus.APPROVED_BY_DEAN
    STATUS_REJECTED_BY_DEAN = RequestStatus.REJECTED_BY_DEAN
    STATUS_FORWARDED_TO_VP = RequestStatus.FORWARDED_TO_VP

    STATUS_CHOICES = RequestStatus.CHOICES

    department = models.ForeignKey(
        'organization.Department',
        on_delete=models.CASCADE,
        related_name='employee_requests',
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee_requests_created',
    )

    date_submitted = models.DateTimeField(auto_now_add=True)
    subject = models.CharField(max_length=255)

    request_narrative = models.TextField(blank=True)
    ai_generated = models.BooleanField(default=False)

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default=STATUS_SUBMITTED
    )

    class Meta:
        ordering = ['-date_submitted']
        verbose_name = 'Employee Request'
        verbose_name_plural = 'Employee Requests'

    def __str__(self):
        return f"{self.department.name} - {self.subject}"


class EmployeeRequestItem(TimeStampedModel):

    DEGREE = 'BSc'
    MASTERS = 'MSc'
    PHD = 'PhD'

    QUALIFICATION_CHOICES = [
        (DEGREE, 'Bachelor Degree'),
        (MASTERS, 'Master’s Degree'),
        (PHD, 'PhD'),
    ]

    LECTURER = 'LECTURER'
    ASSISTANT_PROFESSOR = 'ASST_PROF'
    ASSOCIATE_PROFESSOR = 'ASSOC_PROF'
    PROFESSOR = 'PROFESSOR'

    RANK_CHOICES = [
        (LECTURER, 'Lecturer'),
        (ASSISTANT_PROFESSOR, 'Assistant Professor'),
        (ASSOCIATE_PROFESSOR, 'Associate Professor'),
        (PROFESSOR, 'Professor'),
    ]

    request = models.ForeignKey(
        EmployeeRequest,
        on_delete=models.CASCADE,
        related_name='items',
    )

    no = models.IntegerField(null=True, blank=True)

    academic_qualification = models.CharField(
        max_length=10,
        choices=QUALIFICATION_CHOICES
    )

    academic_rank = models.CharField(
        max_length=20,
        choices=RANK_CHOICES
    )

    study_department = models.CharField(
    max_length=255,
    help_text="Department where the applicant completed their studies"
)

    experience_years = models.IntegerField(default=0)
    cgpa_requirement = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    number_of_employees = models.IntegerField(default=1)

    class Meta:
        ordering = ['request', 'no']
        verbose_name = 'Employee Request Item'
        verbose_name_plural = 'Employee Request Items'

    def __str__(self):
        return f"{self.academic_qualification} - {self.academic_rank}"