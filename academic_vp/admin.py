from django.contrib import admin
from .models import VPProfile, VPAction


@admin.register(VPProfile)
class VPProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'office_location', 'phone_number')
    search_fields = ('user__username', 'user__email')


@admin.register(VPAction)
class VPActionAdmin(admin.ModelAdmin):
    list_display = ('request', 'action', 'performed_by', 'performed_at')
    list_filter = ('action', 'performed_at')
    search_fields = ('request__subject', 'performed_by__username')
