"""
Admin configuration for attendance app.
"""

from django.contrib import admin
from .models import Employee, AttendanceRecord


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'user', 'department', 'position', 'is_active']
    list_filter = ['department', 'position', 'is_active']
    search_fields = ['employee_id', 'user__first_name', 'user__last_name']


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['employee', 'punch_time', 'device_ip', 'status']
    list_filter = ['device_ip', 'status', 'punch_time']
    search_fields = ['employee__employee_id', 'employee__user__first_name', 'employee__user__last_name']
    date_hierarchy = 'punch_time'