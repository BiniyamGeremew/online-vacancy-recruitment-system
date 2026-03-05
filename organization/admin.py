from django.contrib import admin
from .models import College, Department


@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ('name', 'dean', 'created_at', 'updated_at')
    search_fields = ('name', 'dean__username', 'dean__email')
    ordering = ('name',)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'college', 'head', 'created_at', 'updated_at')
    search_fields = ('name', 'college__name', 'head__username', 'head__email')
    list_filter = ('college',)
    ordering = ('college__name', 'name')
