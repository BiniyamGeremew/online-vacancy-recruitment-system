from django.db import models
from django.conf import settings


class TimeStampedModel(models.Model):
    """Abstract base class with created/updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class College(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)
    dean = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='colleges_dean',
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'College'
        verbose_name_plural = 'Colleges'

    def __str__(self):
        return self.name


class Department(TimeStampedModel):
    name = models.CharField(max_length=255)
    college = models.ForeignKey(
        College,
        on_delete=models.CASCADE,
        related_name='departments',
    )
    head = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='departments_head',
    )

    class Meta:
        ordering = ['college__name', 'name']
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
        constraints = [
            models.UniqueConstraint(fields=['name', 'college'], name='unique_department_per_college')
        ]

    def __str__(self):
        return f"{self.name} ({self.college.name})"
