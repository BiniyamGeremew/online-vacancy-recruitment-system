from django.db import models
from django.conf import settings


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    father_name = models.CharField(max_length=30)
    grand_father_name = models.CharField(max_length=30)
    phone_number = models.CharField(max_length=15, blank=True)
    department = models.ForeignKey(
        'organization.Department',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='users',
    )

    def __str__(self):
        if hasattr(self, 'department') and self.department:
            return f"{self.user.username} ({self.department.name})"
        return self.user.username
