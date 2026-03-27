from django.db import models
from django.conf import settings
from django.utils import timezone

from organization.constants import RequestStatus


class VPProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vpprofile'
    )
    phone_number = models.CharField(max_length=32, blank=True)
    office_location = models.CharField(max_length=128, blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - Academic VP"


class VPAction(models.Model):
    ACTION_APPROVED = RequestStatus.APPROVED_BY_VP
    ACTION_REJECTED = RequestStatus.REJECTED_BY_VP
    ACTION_FORWARDED = RequestStatus.FORWARDED_TO_HR

    ACTION_CHOICES = [
        (ACTION_APPROVED, 'Approved by VP'),
        (ACTION_REJECTED, 'Rejected by VP'),
        (ACTION_FORWARDED, 'Forwarded to HR'),
    ]

    request = models.ForeignKey(
        'department_head.EmployeeRequest',
        on_delete=models.CASCADE,
        related_name='vp_actions'
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    comment = models.TextField(blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    performed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-performed_at']

    def __str__(self):
        return f"{self.get_action_display()} on {self.request} by {self.performed_by}"