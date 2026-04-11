from django.contrib import admin

from .models import (
    ApplicantProfile,
    ApplicantDocument,
    EducationQualification,
    EmploymentHistory,
)


@admin.register(ApplicantProfile)
class ApplicantProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'mobile_number', 'country', 'region', 'profile_is_complete')
    search_fields = ('user__username', 'user__email', 'mobile_number')


@admin.register(ApplicantDocument)
class ApplicantDocumentAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'document_type', 'file', 'created_at')
    list_filter = ('document_type',)


@admin.register(EducationQualification)
class EducationQualificationAdmin(admin.ModelAdmin):
    list_display = ('profile', 'institution_name',    'start_date','end_date',)
    search_fields = ('institution_name', 'department')


@admin.register(EmploymentHistory)
class EmploymentHistoryAdmin(admin.ModelAdmin):
    list_display = ('profile', 'employer', 'job_title', 'start_date', 'end_date')
    search_fields = ('employer', 'job_title', 'job_category')
