from django.contrib import admin
from .models import DeanProfile, DeanAction


@admin.register(DeanProfile)
class DeanProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'college', 'phone')
    search_fields = ('user__username', 'user__email', 'college__name')


@admin.register(DeanAction)
class DeanActionAdmin(admin.ModelAdmin):
    list_display = ('request', 'action', 'performed_by', 'performed_at')
    list_filter = ('action', 'performed_at')
    search_fields = ('request__subject', 'performed_by__username')
