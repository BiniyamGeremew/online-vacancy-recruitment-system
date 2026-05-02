from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from hr_officer.models import Vacancy
from applications.models import Application


class Exam(models.Model):
    vacancy = models.ForeignKey(
        Vacancy,
        on_delete=models.CASCADE,
        related_name='exams'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_exams'
    )
    title = models.CharField(max_length=255)
    total_marks = models.PositiveIntegerField(default=0)
    pass_mark = models.PositiveIntegerField(default=0)
    duration_minutes = models.PositiveIntegerField(default=30)
    is_published = models.BooleanField(default=False)
    finalized = models.BooleanField(default=False)
    finalized_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.vacancy.employee_request.subject})"

    @property
    def question_count(self):
        return self.questions.count()


class Question(models.Model):
    TYPE_MCQ = 'MCQ'
    TYPE_SHORT_ANSWER = 'SHORT_ANSWER'

    QUESTION_TYPE_CHOICES = [
        (TYPE_MCQ, 'MCQ'),
        (TYPE_SHORT_ANSWER, 'Short Answer'),
    ]

    STATUS_DRAFT = 'DRAFT'
    STATUS_PUBLISHED = 'PUBLISHED'

    QUESTION_STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PUBLISHED, 'Published'),
    ]

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question_text = models.TextField()
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default=TYPE_MCQ
    )
    marks = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=QUESTION_STATUS_CHOICES,
        default=STATUS_DRAFT
    )

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:60]}"


class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='choices'
    )
    option_text = models.CharField(max_length=512)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.option_text[:60]}{' (correct)' if self.is_correct else ''}"


class ExamSession(models.Model):
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='exam_sessions'
    )
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exam_sessions'
    )
    start_time = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_submitted = models.BooleanField(default=False)
    device_fingerprint = models.CharField(max_length=255, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    ip_address = models.CharField(max_length=64, blank=True)
    tab_switch_count = models.PositiveIntegerField(default=0)
    security_flags = models.JSONField(default=dict, blank=True)
    question_order = models.JSONField(default=list, blank=True)
    choice_order = models.JSONField(default=dict, blank=True)
    activity_log = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-start_time']
        constraints = [
            models.UniqueConstraint(fields=['exam', 'application'], name='unique_exam_application_session')
        ]

    def __str__(self):
        return f"Session for {self.applicant} on {self.exam.title}"

    def is_expired(self):
        if not self.start_time:
            return False
        return timezone.now() > self.start_time + timedelta(minutes=self.exam.duration_minutes)


class ExamSessionActivity(models.Model):
    session = models.ForeignKey(
        'ExamSession',
        on_delete=models.CASCADE,
        related_name='activities'
    )
    activity_type = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.activity_type} @ {self.timestamp} for {self.session}"


class Answer(models.Model):
    session = models.ForeignKey(
        ExamSession,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    selected_choice = models.ForeignKey(
        Choice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='selected_answers'
    )
    text_answer = models.TextField(blank=True)
    score_awarded = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    class Meta:
        unique_together = ('session', 'question')

    def __str__(self):
        return f"Answer for {self.question}"


class ExamResult(models.Model):
    session = models.OneToOneField(
        ExamSession,
        on_delete=models.CASCADE,
        related_name='result'
    )
    total_score = models.DecimalField(max_digits=6, decimal_places=2)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    passed = models.BooleanField(default=False)
    evaluated_at = models.DateTimeField(auto_now_add=True)
    sent_to_hr = models.BooleanField(default=False)

    class Meta:
        ordering = ['-evaluated_at']

    def __str__(self):
        return f"Result for {self.session.applicant} - {self.percentage}%"
