from django.db import models
from django.conf import settings
from django.utils import timezone

from organization.models import College
from department_head.models import EmployeeRequest


class DeanProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deanprofile')
    college = models.ForeignKey(College, on_delete=models.SET_NULL, null=True, blank=True, related_name='deans')
    phone = models.CharField(max_length=32, blank=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"DeanProfile: {self.user.get_full_name() or self.user.username}"


class DeanAction(models.Model):
    ACTION_APPROVED = 'approved'
    ACTION_REJECTED = 'rejected'
    ACTION_FORWARDED = 'forwarded'

    ACTION_CHOICES = [
        (ACTION_APPROVED, 'Approved'),
        (ACTION_REJECTED, 'Rejected'),
        (ACTION_FORWARDED, 'Forwarded to VP'),
    ]

    request = models.ForeignKey(EmployeeRequest, on_delete=models.CASCADE, related_name='dean_actions')
    action = models.CharField(max_length=16, choices=ACTION_CHOICES)
    reason = models.TextField(blank=True)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    performed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-performed_at']

    def __str__(self):
        return f"{self.get_action_display()} on {self.request} by {self.performed_by}"
