from django.contrib import admin

from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'position', 'status', 'submitted_at')
    list_filter = ('status', 'submitted_at')
    search_fields = ('applicant__user__username', 'position__academic_rank')
    readonly_fields = ('profile_snapshot', 'submitted_at')
