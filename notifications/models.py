from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_APPLICATION_SUBMITTED = 'application_submitted'
    TYPE_ELIGIBLE = 'eligible'
    TYPE_REJECTED = 'rejected'
    TYPE_SHORTLISTED = 'shortlisted'
    TYPE_VACANCY_MATCH = 'vacancy_match'
    TYPE_EXAM_SCHEDULED = 'exam_scheduled'
    TYPE_EXAM_STARTED = 'exam_started'
    TYPE_EXAM_RESULT = 'exam_result'
    TYPE_EXAM_COMPLETED = 'exam_completed'
    TYPE_SHORTLIST_FINALIZED = 'shortlist_finalized'

    NOTIFICATION_TYPE_CHOICES = [
        (TYPE_APPLICATION_SUBMITTED, 'Application Submitted'),
        (TYPE_ELIGIBLE, 'Eligible'),
        (TYPE_REJECTED, 'Rejected'),
        (TYPE_SHORTLISTED, 'Shortlisted'),
        (TYPE_VACANCY_MATCH, 'Vacancy Match'),
        (TYPE_EXAM_SCHEDULED, 'Exam Scheduled'),
        (TYPE_EXAM_STARTED, 'Exam Started'),
        (TYPE_EXAM_RESULT, 'Exam Result'),
        (TYPE_EXAM_COMPLETED, 'Exam Completed'),
        (TYPE_SHORTLIST_FINALIZED, 'Shortlist Finalized'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=512, blank=True)
    is_read = models.BooleanField(default=False)
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPE_CHOICES,
        default=TYPE_APPLICATION_SUBMITTED
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.user})"
