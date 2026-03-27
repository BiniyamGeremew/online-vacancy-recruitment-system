from django.db import models
from django.conf import settings
from django.utils import timezone

from department_head.models import EmployeeRequest


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
        verbose_name = 'HR Action'
        verbose_name_plural = 'HR Actions'

    def __str__(self):
        return f"{self.get_action_display()} on {self.request}"