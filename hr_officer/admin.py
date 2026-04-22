
from django.contrib import admin
from .models import HRProfile, HRAction, Vacancy, VacancyPosition, JobApplication

@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
	list_display = ('employee_request', 'announcement_date', 'deadline', 'status', 'posted_by')
	list_filter = ('status', 'announcement_date', 'deadline')
	search_fields = ('employee_request__subject', 'description')
	date_hierarchy = 'announcement_date'

@admin.register(VacancyPosition)
class VacancyPositionAdmin(admin.ModelAdmin):
	list_display = ('vacancy', 'department', 'academic_rank', 'field_of_education', 'positions')
	search_fields = ('academic_rank', 'field_of_education', 'department__name')
	list_filter = ('department',)

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
	list_display = ('applicant', 'vacancy_position', 'applied_at', 'status')
	search_fields = ('applicant__username', 'vacancy_position__academic_rank', 'vacancy_position__department__name')
	list_filter = ('status', 'applied_at')
