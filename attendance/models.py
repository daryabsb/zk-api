"""
Models for attendance management.
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Employee(models.Model):
    """Employee model for HR system."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    employee_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200, blank=True)  # Store employee name from device
    department = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    hire_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name or self.user.get_full_name()} ({self.employee_id})"


class AttendanceRecord(models.Model):
    """Attendance records from ZK biometric devices."""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_records')
    punch_time = models.DateTimeField()
    device_id = models.IntegerField()
    device_ip = models.GenericIPAddressField()
    verification_mode = models.IntegerField(default=0)  # 0=password, 1=fingerprint, etc.
    status = models.IntegerField(default=0)  # 0=check-in, 1=check-out, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['punch_time', 'employee']),
            models.Index(fields=['device_ip', 'punch_time']),
        ]
        ordering = ['-punch_time']
        unique_together = ['employee', 'punch_time', 'device_ip']
    
    def __str__(self):
        return f"{self.employee.employee_id} - {self.punch_time}"