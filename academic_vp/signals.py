from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import VPProfile


@receiver(post_save, sender=get_user_model())
def ensure_vp_profile(sender, instance, created, **kwargs):
    # Do not auto-create profiles for all users; leave creation to admin or explicit assignment.
    return
