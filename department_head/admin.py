from django.contrib import admin
from .models import EmployeeRequest, EmployeeRequestItem


@admin.register(EmployeeRequest)
class EmployeeRequestAdmin(admin.ModelAdmin):
    list_display = ('subject', 'department', 'created_by', 'status', 'date_submitted')
    list_filter = ('status', 'department')
    search_fields = ('subject', 'description', 'closing_note', 'created_by__username', 'created_by__email')
    raw_id_fields = ('created_by', 'department')


@admin.register(EmployeeRequestItem)
class EmployeeRequestItemAdmin(admin.ModelAdmin):
    list_display = ('academic_qualification', 'academic_rank', 'request', 'number_of_employees')
    search_fields = ('academic_qualification', 'academic_rank', 'area_of_specialization')
    raw_id_fields = ('request',)
