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
    description = models.TextField(blank=True)
    closing_note = models.TextField(blank=True)

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
    SEX_MALE = 'M'
    SEX_FEMALE = 'F'
    SEX_ANY = 'A'

    SEX_CHOICES = [
        (SEX_MALE, 'Male'),
        (SEX_FEMALE, 'Female'),
        (SEX_ANY, 'Any'),
    ]

    request = models.ForeignKey(
        EmployeeRequest,
        on_delete=models.CASCADE,
        related_name='items',
    )
    no = models.IntegerField(null=True, blank=True)
    academic_qualification = models.CharField(max_length=255)
    academic_rank = models.CharField(max_length=255)
    area_of_specialization = models.CharField(max_length=255)
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, default=SEX_MALE)
    experience_years = models.IntegerField()
    cgpa_requirement = models.DecimalField(max_digits=4, decimal_places=2)
    number_of_employees = models.IntegerField()

    class Meta:
        ordering = ['request', 'no']
        verbose_name = 'Employee Request Item'
        verbose_name_plural = 'Employee Request Items'

    def __str__(self):
        return f"{self.academic_qualification} - {self.academic_rank}"