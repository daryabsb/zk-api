"""
Admin configuration for devices app.
"""

from django.contrib import admin
from .models import ZKDevice, DeviceSyncLog


@admin.register(ZKDevice)
class ZKDeviceAdmin(admin.ModelAdmin):
    list_display = ['name', 'ip_address', 'port', 'is_active', 'last_sync']
    list_filter = ['is_active', 'model']
    list_editable = ['is_active']
    search_fields = ['name', 'ip_address', 'serial_number']


@admin.register(DeviceSyncLog)
class DeviceSyncLogAdmin(admin.ModelAdmin):
    list_display = ['device', 'sync_type', 'records_synced', 'success', 'started_at']
    list_filter = ['sync_type', 'success', 'started_at']
    search_fields = ['device__name', 'device__ip_address']
    readonly_fields = ['started_at', 'completed_at']