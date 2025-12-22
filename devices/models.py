"""
Models for ZK biometric devices management.
"""

from django.db import models


class ZKDevice(models.Model):
    """ZK biometric device configuration."""
    name = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    port = models.IntegerField(default=4370)
    serial_number = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    sync_interval = models.IntegerField(default=15, help_text="Sync interval in minutes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['ip_address', 'port']
    
    def __str__(self):
        return f"{self.name} ({self.ip_address}:{self.port})"


class DeviceSyncLog(models.Model):
    """Log for device synchronization operations."""
    device = models.ForeignKey(ZKDevice, on_delete=models.CASCADE, related_name='sync_logs')
    sync_type = models.CharField(max_length=20, choices=[
        ('attendance', 'Attendance'),
        ('users', 'Users'),
        ('status', 'Status'),
    ])
    records_synced = models.IntegerField(default=0)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.device.name} - {self.sync_type} - {self.started_at}"