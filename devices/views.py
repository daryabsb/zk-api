"""
Views for ZK devices management.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from .models import ZKDevice
from .api_services import get_api_service
import json


@method_decorator(csrf_exempt, name='dispatch')
class DeviceAPIView(View):
    """API endpoint for device management."""
    
    def get(self, request):
        """Get list of devices."""
        devices = ZKDevice.objects.filter(is_active=True)
        
        data = [
            {
                'id': device.id,
                'name': device.name,
                'ip_address': device.ip_address,
                'port': device.port,
                'serial_number': device.serial_number,
                'model': device.model,
                'last_sync': device.last_sync.isoformat() if device.last_sync else None,
            }
            for device in devices
        ]
        
        return JsonResponse({'success': True, 'devices': data})
    
    def post(self, request):
        """Create or update a device."""
        try:
            data = json.loads(request.body)
            device_id = data.get('id')
            
            if device_id:
                device = ZKDevice.objects.get(id=device_id)
                for field in ['name', 'ip_address', 'port', 'serial_number', 'model', 'is_active']:
                    if field in data:
                        setattr(device, field, data[field])
                device.save()
                message = 'Device updated successfully'
            else:
                device = ZKDevice.objects.create(
                    name=data['name'],
                    ip_address=data['ip_address'],
                    port=data.get('port', 4370),
                    serial_number=data.get('serial_number', ''),
                    model=data.get('model', ''),
                    is_active=data.get('is_active', True)
                )
                message = 'Device created successfully'
            
            return JsonResponse({
                'success': True, 
                'message': message,
                'device_id': device.id
            })
            
        except ZKDevice.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Device not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def test_device_connection(request, device_id):
    """Test connection to a specific device."""
    try:
        device = ZKDevice.objects.get(id=device_id)
        service = get_api_service()
        
        success, error = service.test_connection(device)
        
        return JsonResponse({
            'success': success,
            'connected': success,
            'error': error if not success else ''
        })
        
    except ZKDevice.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Device not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def sync_device_attendance(request, device_id):
    """Sync attendance records from a specific device."""
    try:
        device = ZKDevice.objects.get(id=device_id)
        service = get_api_service()
        
        records_synced, error = service.sync_attendance(device)
        
        if error:
            return JsonResponse({
                'success': False,
                'error': error,
                'records_synced': records_synced
            })
        
        return JsonResponse({
            'success': True,
            'records_synced': records_synced,
            'message': f'Synced {records_synced} records from {device.name}'
        })
        
    except ZKDevice.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Device not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
