"""
Celery tasks for device operations using API service.
"""

from celery import shared_task
from celery.utils.log import get_task_logger
from .models import ZKDevice
from .api_services import get_api_service

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def sync_device_employees_task(self, device_id):
    """Celery task to sync employees from a specific device."""
    try:
        device = ZKDevice.objects.get(id=device_id)
        service = get_api_service()
        
        employees_synced, error = service.sync_employees(device)
        
        if error:
            logger.error(f"Failed to sync employees from device {device.name}: {error}")
            raise self.retry(exc=Exception(error))
        
        logger.info(f"Successfully synced {employees_synced} employees from {device.name}")
        return {
            'device_id': device_id,
            'device_name': device.name,
            'employees_synced': employees_synced,
            'success': True
        }
        
    except ZKDevice.DoesNotExist:
        logger.error(f"Device with ID {device_id} not found")
        return {'success': False, 'error': 'Device not found'}
    except Exception as e:
        logger.error(f"Error syncing employees from device {device_id}: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def sync_device_attendance_task(self, device_id):
    """Celery task to sync attendance from a specific device."""
    try:
        device = ZKDevice.objects.get(id=device_id)
        service = get_api_service()
        
        records_synced, error = service.sync_attendance(device)
        
        if error:
            logger.error(f"Failed to sync device {device.name}: {error}")
            raise self.retry(exc=Exception(error))
        
        logger.info(f"Successfully synced {records_synced} records from {device.name}")
        return {
            'device_id': device_id,
            'device_name': device.name,
            'records_synced': records_synced,
            'success': True
        }
        
    except ZKDevice.DoesNotExist:
        logger.error(f"Device with ID {device_id} not found")
        return {'success': False, 'error': 'Device not found'}
    except Exception as e:
        logger.error(f"Error syncing device {device_id}: {str(e)}")
        raise self.retry(exc=e)


@shared_task
def sync_all_devices_employees():
    """Sync employees from all active devices."""
    devices = ZKDevice.objects.filter(is_active=True)
    total_employees = 0
    
    for device in devices:
        try:
            result = sync_device_employees_task.delay(device.id)
            # Wait for task to complete and get result
            task_result = result.get(timeout=300)  # 5 minutes timeout
            if task_result.get('success'):
                total_employees += task_result.get('employees_synced', 0)
        except Exception as e:
            logger.error(f"Error processing device {device.name}: {str(e)}")
            continue
    
    return {
        'success': True,
        'total_employees_synced': total_employees,
        'devices_processed': devices.count()
    }


@shared_task
def sync_all_devices_attendance():
    """Sync attendance from all active devices."""
    devices = ZKDevice.objects.filter(is_active=True)
    total_records = 0
    
    for device in devices:
        try:
            result = sync_device_attendance_task.delay(device.id)
            # Wait for task to complete and get result
            task_result = result.get(timeout=300)  # 5 minutes timeout
            if task_result.get('success'):
                total_records += task_result.get('records_synced', 0)
        except Exception as e:
            logger.error(f"Error processing device {device.name}: {str(e)}")
            continue
    
    return {
        'success': True,
        'total_records_synced': total_records,
        'devices_processed': devices.count()
    }


@shared_task
def sync_all_devices_complete():
    """Complete sync: employees first, then attendance."""
    # Sync employees first
    employee_result = sync_all_devices_employees.delay()
    employee_stats = employee_result.get(timeout=600)  # 10 minutes timeout
    
    # Then sync attendance
    attendance_result = sync_all_devices_attendance.delay()
    attendance_stats = attendance_result.get(timeout=600)  # 10 minutes timeout
    
    return {
        'employee_sync': employee_stats,
        'attendance_sync': attendance_stats,
        'success': employee_stats.get('success') and attendance_stats.get('success')
    }