"""
Celery tasks for automatic synchronization of attendance data from ZK biometric devices.
This module handles periodic syncing of attendance records to the AttendanceData model.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from celery import shared_task
from celery.schedules import crontab
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.db.models import Q

# Import your models - adjust these imports based on your actual app structure
from biometric_integration.models import ZKDevice, AttendanceRecord
from employee_management.models import Employee  # Adjust this import to your Employee model
from attendance.models import AttendanceData  # Adjust this import to your AttendanceData model

# Import the ZK biometric utility
from biometric_integration.utils.zk_biometric import get_attendance_records

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def sync_attendance_from_devices():
    """
    Periodic task to sync attendance records from all active ZK devices.
    This task runs every 15 minutes by default.
    """
    try:
        logger.info("Starting automatic attendance sync from ZK devices...")
        
        # Get all active devices
        devices = ZKDevice.objects.filter(is_active=True)
        
        if not devices.exists():
            logger.warning("No active ZK devices found for syncing")
            return {"success": True, "message": "No active devices", "records_synced": 0}
        
        total_records_synced = 0
        sync_time = timezone.now()
        
        for device in devices:
            try:
                records_synced = sync_device_attendance(device, sync_time)
                total_records_synced += records_synced
                
                logger.info(
                    f"Synced {records_synced} records from device {device.name} ({device.ip_address})"
                )
                
            except Exception as e:
                logger.error(
                    f"Failed to sync device {device.name} ({device.ip_address}): {str(e)}",
                    exc_info=True
                )
                # Continue with other devices even if one fails
                continue
        
        logger.info(f"Attendance sync completed. Total records synced: {total_records_synced}")
        
        return {
            "success": True,
            "message": f"Synced {total_records_synced} records from {devices.count()} devices",
            "records_synced": total_records_synced,
            "sync_time": sync_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Critical error in attendance sync task: {str(e)}", exc_info=True)
        raise sync_attendance_from_devices.retry(exc=e)

def sync_device_attendance(device: ZKDevice, sync_time: datetime) -> int:
    """
    Sync attendance records from a single ZK device to AttendanceData model.
    
    Args:
        device: The ZKDevice instance to sync from
        sync_time: The current sync time for tracking
        
    Returns:
        Number of records successfully synced
    """
    records_synced = 0
    
    # Calculate time range for sync (last sync time or default 24 hours)
    if device.last_sync:
        start_time = device.last_sync
    else:
        start_time = sync_time - timedelta(hours=24)
    
    end_time = sync_time
    
    # Get attendance records from the device
    result = get_attendance_records(
        device.ip_address,
        start_time,
        end_time,
        device.port
    )
    
    if not result.get('success'):
        logger.error(f"Failed to get records from device {device.name}: {result.get('error')}")
        return 0
    
    device_records = result.get('records', [])
    
    if not device_records:
        logger.info(f"No new records found for device {device.name}")
        # Still update last_sync to avoid missing data in case of device issues
        device.last_sync = sync_time
        device.save()
        return 0
    
    logger.info(f"Processing {len(device_records)} records from device {device.name}")
    
    # Process each record in a transaction
    with transaction.atomic():
        for record_data in device_records:
            try:
                if process_attendance_record(device, record_data, sync_time):
                    records_synced += 1
                    
            except Exception as e:
                logger.error(
                    f"Failed to process record from device {device.name}: {str(e)}",
                    exc_info=True
                )
                # Continue with other records
                continue
        
        # Update device sync time
        device.last_sync = sync_time
        device.save()
    
    return records_synced

def process_attendance_record(device: ZKDevice, record_data: Dict[str, Any], sync_time: datetime) -> bool:
    """
    Process a single attendance record and save it to AttendanceData model.
    
    Args:
        device: The ZKDevice that provided the record
        record_data: Raw record data from the device
        sync_time: When this sync is occurring
        
    Returns:
        True if record was processed successfully, False otherwise
    """
    # Extract data from device record
    employee_id = record_data.get('EmployeeId', '').strip()
    record_time = record_data.get('RecordTime')
    record_type = record_data.get('Type', 'Unknown')
    verify_mode = record_data.get('VerifyMode', 0)
    work_code = record_data.get('WorkCode', 0)
    
    # Validate required fields
    if not employee_id or not record_time:
        logger.warning(f"Invalid record data from device {device.name}: missing employee_id or record_time")
        return False
    
    # Convert record_time to timezone-aware datetime if needed
    if isinstance(record_time, str):
        record_time = datetime.fromisoformat(record_time.replace('Z', '+00:00'))
    
    if record_time.tzinfo is None:
        record_time = timezone.make_aware(record_time)
    
    # Find the employee
    try:
        # Adjust this query based on your Employee model structure
        employee = Employee.objects.get(
            Q(employee_id=employee_id) | 
            Q(biometric_id=employee_id) |
            Q(alternate_id=employee_id)
        )
    except Employee.DoesNotExist:
        logger.warning(
            f"Employee with ID '{employee_id}' not found for record from device {device.name} "
            f"at {record_time}"
        )
        # You might want to create a placeholder or handle missing employees differently
        return False
    except Employee.MultipleObjectsReturned:
        logger.error(
            f"Multiple employees found for ID '{employee_id}' from device {device.name}"
        )
        return False
    
    # Map device record type to your AttendanceData model
    attendance_type = map_attendance_type(record_type)
    
    # Create or update AttendanceData record
    attendance_data, created = AttendanceData.objects.update_or_create(
        device=device,
        employee=employee,
        punch_time=record_time,
        defaults={
            'attendance_type': attendance_type,
            'verify_mode': verify_mode,
            'work_code': work_code,
            'device_ip': device.ip_address,
            'device_name': device.name,
            'raw_data': record_data,  # Store raw data for reference
            'sync_time': sync_time,
            'is_processed': False,  # Mark for later processing if needed
            'data_source': 'ZK_Device',
        }
    )
    
    if created:
        logger.debug(
            f"Created new attendance record for {employee.employee_id} "
            f"at {record_time} from device {device.name}"
        )
    else:
        logger.debug(
            f"Updated existing attendance record for {employee.employee_id} "
            f"at {record_time} from device {device.name}"
        )
    
    return True

def map_attendance_type(device_record_type: str) -> str:
    """
    Map ZK device record types to your AttendanceData model types.
    Adjust this mapping based on your specific requirements.
    """
    type_mapping = {
        'CheckIn': 'CHECK_IN',
        'CheckOut': 'CHECK_OUT',
        'BreakStart': 'BREAK_START',
        'BreakEnd': 'BREAK_END',
        'Unknown': 'UNKNOWN'
    }
    
    return type_mapping.get(device_record_type, 'UNKNOWN')

@shared_task
def cleanup_old_attendance_records(days_to_keep: int = 90):
    """
    Clean up old attendance records from the raw records table.
    This helps manage database size while keeping AttendanceData.
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        # Clean up raw attendance records older than specified days
        deleted_count, _ = AttendanceRecord.objects.filter(
            record_time__lt=cutoff_date
        ).delete()
        
        logger.info(f"Cleaned up {deleted_count} old attendance records older than {days_to_keep} days")
        
        return {
            "success": True,
            "message": f"Cleaned up {deleted_count} old records",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up old attendance records: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "deleted_count": 0
        }

@shared_task
def retry_failed_syncs():
    """
    Task to retry failed sync operations for devices that had errors.
    """
    try:
        # Find devices that haven't synced successfully in the last 2 hours
        cutoff_time = timezone.now() - timedelta(hours=2)
        
        failed_devices = ZKDevice.objects.filter(
            is_active=True,
            last_sync__lt=cutoff_time
        )
        
        retry_count = 0
        
        for device in failed_devices:
            try:
                logger.info(f"Retrying sync for device {device.name} ({device.ip_address})")
                sync_device_attendance(device, timezone.now())
                retry_count += 1
                
            except Exception as e:
                logger.error(
                    f"Retry failed for device {device.name}: {str(e)}",
                    exc_info=True
                )
        
        logger.info(f"Retry task completed. Attempted retry for {retry_count} devices")
        
        return {
            "success": True,
            "retry_count": retry_count,
            "total_failed": failed_devices.count()
        }
        
    except Exception as e:
        logger.error(f"Error in retry task: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "retry_count": 0
        }

# Celery beat schedule configuration
# Add this to your CELERY_BEAT_SCHEDULE in settings.py
CELERY_BEAT_SCHEDULE = {
    'sync-attendance-every-15-minutes': {
        'task': 'biometric_integration.tasks.sync_attendance_from_devices',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
        'options': {'expires': 300}  # Expire after 5 minutes
    },
    'cleanup-old-records-daily': {
        'task': 'biometric_integration.tasks.cleanup_old_attendance_records',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        'kwargs': {'days_to_keep': 90}
    },
    'retry-failed-syncs-hourly': {
        'task': 'biometric_integration.tasks.retry_failed_syncs',
        'schedule': crontab(minute=0),  # Hourly
        'options': {'expires': 3600}
    },
}

# Health check task
@shared_task
def attendance_sync_health_check():
    """
    Health check task to monitor the attendance sync system.
    """
    try:
        # Check if any active devices haven't synced in the last 4 hours
        cutoff_time = timezone.now() - timedelta(hours=4)
        
        stale_devices = ZKDevice.objects.filter(
            is_active=True,
            last_sync__lt=cutoff_time
        ).count()
        
        total_devices = ZKDevice.objects.filter(is_active=True).count()
        
        health_status = {
            'timestamp': timezone.now().isoformat(),
            'total_active_devices': total_devices,
            'stale_devices': stale_devices,
            'status': 'HEALTHY' if stale_devices == 0 else 'WARNING',
            'message': f"{stale_devices} devices haven't synced in 4 hours" if stale_devices > 0 else "All devices syncing normally"
        }
        
        logger.info(f"Attendance sync health check: {health_status}")
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return {
            'timestamp': timezone.now().isoformat(),
            'status': 'ERROR',
            'error': str(e)
        }