"""
Celery tasks for device operations.
"""

from celery import shared_task
from celery.utils.log import get_task_logger
from .models import ZKDevice
from .services import ZKDeviceService

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def sync_device_attendance_task(self, device_id):
    """Celery task to sync attendance from a specific device."""
    try:
        device = ZKDevice.objects.get(id=device_id)
        service = ZKDeviceService()
        
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