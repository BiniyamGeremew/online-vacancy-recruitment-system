from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'phone_number')
    search_fields = ('user__username', 'user__email', 'department__name')
    raw_id_fields = ('user', 'department')
from django.contrib import admin


