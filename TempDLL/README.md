# ZK Biometric DLL for Django

A .NET DLL that provides ZK biometric device integration for Python Django projects. This library allows you to communicate with ZK attendance devices directly from your Django application without needing a separate service.

## Features

-   **Direct Device Communication**: TCP/IP communication with ZK biometric devices
-   **Python.NET Integration**: Seamless integration with Django using Python.NET
-   **JSON API**: Simple JSON-based interface for easy Python consumption
-   **Thread-Safe**: Proper async/await implementation with thread safety
-   **Error Handling**: Comprehensive error handling with JSON error responses
-   **Multiple Device Support**: Connect to and manage multiple ZK devices simultaneously
-   **Real-time Data Sync**: Fetch attendance records with configurable time ranges
-   **Cross-Platform Ready**: Built on .NET 8.0 for modern compatibility

## Prerequisites

### For Building the DLL

1. **.NET 8.0 SDK** - [Download here](https://dotnet.microsoft.com/download/dotnet/8.0)
2. **Windows OS** (for building and device communication)

### For Django Integration

1. **Python 3.8+**
2. **Django 3.2+**
3. **Python.NET** (`pythonnet` package)

## Installation

### 1. Build the DLL

```bash
cd TempDLL
./build.bat
```

The built DLL files will be in the `output/` folder.

### 2. Install Python Dependencies

```bash
pip install pythonnet
```

### 3. Django App Setup

Create a new Django app for biometric integration:

```bash
python manage.py startapp biometric_integration
```

## Project Structure

```
biometric_integration/
├── __init__.py
├── models.py          # Your Django models
├── views.py           # API endpoints
├── tasks.py           # Celery tasks for background sync
├── utils.py           # Helper functions
└── zk_integration.py  # DLL integration wrapper
```

## DLL API Reference

### Core Methods

#### `TestConnection(device_json: str) -> str`

Tests connection to a ZK device.

**Parameters:**

-   `device_json`: JSON string containing device configuration

**Returns:** JSON response with success status

#### `ConnectDevice(device_json: str) -> str`

Connects to a ZK device and performs handshake.

**Parameters:**

-   `device_json`: JSON string containing device configuration

**Returns:** JSON response with connection status

#### `GetAttendanceRecords(device_json: str, start_time: str, end_time: str) -> str`

Fetches attendance records from a ZK device for a specific time range.

**Parameters:**

-   `device_json`: JSON string containing device configuration
-   `start_time`: Start time in ISO format (e.g., "2024-01-01T00:00:00")
-   `end_time`: End time in ISO format (e.g., "2024-01-31T23:59:59")

**Returns:** JSON response containing attendance records

### Device JSON Format

```json
{
    "ip_address": "192.168.1.201",
    "port": 4370,
    "password": "",
    "timeout": 5000,
    "device_name": "Main Entrance Device",
    "device_id": "ZK001"
}
```

## Django Integration Example

### 1. Create Django Models

In `biometric_integration/models.py`:

```python
from django.db import models

class ZKDevice(models.Model):
    name = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    port = models.IntegerField(default=4370)
    password = models.CharField(max_length=50, blank=True)
    timeout = models.IntegerField(default=5000)
    is_active = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.ip_address}:{self.port})"

class AttendanceRecord(models.Model):
    device = models.ForeignKey(ZKDevice, on_delete=models.CASCADE)
    user_id = models.CharField(max_length=50)
    timestamp = models.DateTimeField()
    status = models.IntegerField(default=0)  # 0: Check-in, 1: Check-out, etc.
    verify_mode = models.IntegerField(default=0)
    work_code = models.IntegerField(default=0)
    raw_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user_id', 'timestamp']),
        ]
```

### 2. Create DLL Integration Wrapper

In `biometric_integration/zk_integration.py`:

```python
import json
import clr
import os
from django.conf import settings

# Load the DLL
zk_dll_path = os.path.join(settings.BASE_DIR, 'biometric_integration', 'lib', 'ZKBiometricDLL.dll')
clr.AddReference(zk_dll_path)

from ZKBiometricDLL import ZKBiometricAPI

class ZKDeviceIntegration:
    def __init__(self):
        self.api = ZKBiometricAPI()

    def test_connection(self, device_config):
        """Test connection to a ZK device"""
        device_json = json.dumps(device_config)
        result = self.api.TestConnection(device_json)
        return json.loads(result)

    def connect_device(self, device_config):
        """Connect to a ZK device"""
        device_json = json.dumps(device_config)
        result = self.api.ConnectDevice(device_json)
        return json.loads(result)

    def get_attendance_records(self, device_config, start_time, end_time):
        """Get attendance records from device"""
        device_json = json.dumps(device_config)
        result = self.api.GetAttendanceRecords(device_json, start_time, end_time)
        return json.loads(result)

    def sync_device_records(self, device):
        """Sync records from a device to Django database"""
        from .models import AttendanceRecord
        from django.utils import timezone

        device_config = {
            'ip_address': device.ip_address,
            'port': device.port,
            'password': device.password,
            'timeout': device.timeout,
            'device_name': device.name,
            'device_id': str(device.id)
        }

        # Calculate time range (last sync to now, or last 24 hours if first sync)
        if device.last_sync:
            start_time = device.last_sync.isoformat()
        else:
            start_time = (timezone.now() - timezone.timedelta(hours=24)).isoformat()

        end_time = timezone.now().isoformat()

        try:
            result = self.get_attendance_records(device_config, start_time, end_time)

            if result['success']:
                records = result['records']
                for record in records:
                    AttendanceRecord.objects.create(
                        device=device,
                        user_id=record['user_id'],
                        timestamp=record['timestamp'],
                        status=record['status'],
                        verify_mode=record['verify_mode'],
                        work_code=record['work_code'],
                        raw_data=record
                    )

                # Update last sync time
                device.last_sync = timezone.now()
                device.save()

                return {
                    'success': True,
                    'records_synced': len(records),
                    'message': f'Synced {len(records)} records from {device.name}'
                }
            else:
                return {
                    'success': False,
                    'error': result['error'],
                    'message': f'Failed to sync from {device.name}: {result["error"]}'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Exception during sync from {device.name}: {str(e)}'
            }
```

### 3. Create Django Views

In `biometric_integration/views.py`:

```python
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .zk_integration import ZKDeviceIntegration
from .models import ZKDevice

@csrf_exempt
@require_http_methods(["POST"])
def test_device_connection(request):
    """Test connection to a ZK device"""
    try:
        data = json.loads(request.body)
        integration = ZKDeviceIntegration()
        result = integration.test_connection(data)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def sync_device_records(request, device_id):
    """Sync records from a specific device"""
    try:
        device = ZKDevice.objects.get(id=device_id)
        integration = ZKDeviceIntegration()
        result = integration.sync_device_records(device)
        return JsonResponse(result)
    except ZKDevice.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Device not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["GET"])
def get_attendance_data(request):
    """Get attendance data from database"""
    from .models import AttendanceRecord
    from django.utils import timezone
    from datetime import timedelta

    # Get query parameters
    user_id = request.GET.get('user_id')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    records = AttendanceRecord.objects.all()

    if user_id:
        records = records.filter(user_id=user_id)

    if start_date:
        records = records.filter(timestamp__gte=start_date)

    if end_date:
        records = records.filter(timestamp__lte=end_date)

    data = [{
        'user_id': record.user_id,
        'timestamp': record.timestamp.isoformat(),
        'status': record.status,
        'device': record.device.name,
        'verify_mode': record.verify_mode,
        'work_code': record.work_code
    } for record in records.order_by('-timestamp')[:100]]  # Limit to 100 records

    return JsonResponse({'success': True, 'records': data})
```

### 4. Configure URLs

In `biometric_integration/urls.py`:

```python
from django.urls import path
from . import views

urlpatterns = [
    path('test-connection/', views.test_device_connection, name='test_device_connection'),
    path('sync-device/<int:device_id>/', views.sync_device_records, name='sync_device_records'),
    path('attendance-data/', views.get_attendance_data, name='get_attendance_data'),
]
```

### 5. Add to Main URLs

In your project's `urls.py`:

```python
from django.urls import include, path

urlpatterns = [
    path('api/biometric/', include('biometric_integration.urls')),
    # ... other URLs
]
```

## Celery Background Tasks

For automatic background synchronization, create Celery tasks:

In `biometric_integration/tasks.py`:

```python
from celery import shared_task
from .zk_integration import ZKDeviceIntegration
from .models import ZKDevice

@shared_task
def sync_all_devices():
    """Sync all active ZK devices"""
    devices = ZKDevice.objects.filter(is_active=True)
    integration = ZKDeviceIntegration()

    results = []
    for device in devices:
        result = integration.sync_device_records(device)
        results.append({
            'device': device.name,
            'success': result['success'],
            'records_synced': result.get('records_synced', 0),
            'error': result.get('error')
        })

    return results

@shared_task
def sync_single_device(device_id):
    """Sync a specific device"""
    try:
        device = ZKDevice.objects.get(id=device_id)
        integration = ZKDeviceIntegration()
        result = integration.sync_device_records(device)
        return result
    except ZKDevice.DoesNotExist:
        return {'success': False, 'error': 'Device not found'}
```

## Usage Examples

### 1. Test Device Connection

```python
import requests
import json

# Test device connection
device_config = {
    "ip_address": "192.168.1.201",
    "port": 4370,
    "password": "",
    "timeout": 5000
}

response = requests.post(
    'http://localhost:8000/api/biometric/test-connection/',
    json=device_config
)

print(json.dumps(response.json(), indent=2))
```

### 2. Sync Device Records

```python
# Sync records from device ID 1
response = requests.post(
    'http://localhost:8000/api/biometric/sync-device/1/'
)

print(json.dumps(response.json(), indent=2))
```

### 3. Get Attendance Data

```python
# Get attendance data for a specific user
params = {
    'user_id': '123',
    'start_date': '2024-01-01',
    'end_date': '2024-01-31'
}

response = requests.get(
    'http://localhost:8000/api/biometric/attendance-data/',
    params=params
)

print(json.dumps(response.json(), indent=2))
```

## Error Handling

The DLL returns JSON responses with consistent error format:

```json
{
    "success": false,
    "error": "Error message description"
}
```

Common error scenarios:

-   **Connection timeout**: Device not responding
-   **Invalid credentials**: Incorrect password for device
-   **Network issues**: Unable to reach device IP
-   **Protocol errors**: Device communication protocol mismatch

## Building and Deployment

### Build Script

The `build.bat` script automates the build process:

```bash
@echo off
echo Building ZK Biometric DLL...

# Restore NuGet packages
dotnet restore

# Build in Release mode
dotnet build --configuration Release

# Create output directory
if not exist "output" mkdir output

# Copy DLL and dependencies
copy "bin\Release\net8.0\ZKBiometricDLL.dll" output\
copy "bin\Release\net8.0\Newtonsoft.Json.dll" output\

echo Build completed! Files are in the output/ folder.
echo.
echo To use in Python, copy the DLL files to your Django project:
echo copy output\\*.* your_django_project\\biometric_integration\\lib\
```

### Manual Build

```bash
cd TempDLL
dotnet restore
dotnet build --configuration Release
```

## Troubleshooting

### Common Issues

1. **Python.NET Installation Issues**

    ```bash
    # Try installing with specific version
    pip install pythonnet==3.0.0
    ```

2. **DLL Load Errors**

    - Ensure .NET 8.0 Runtime is installed
    - Check DLL file paths in your Python code

3. **Device Connection Issues**

    - Verify device IP address and port
    - Check network connectivity
    - Ensure device is powered on and network configured

4. **Permission Issues**
    - Run Django with appropriate permissions
    - Check firewall settings for device communication

### Debug Mode

Enable detailed logging by setting environment variable:

```bash
set ZK_DEBUG=true
```

## Performance Considerations

-   **Batch Processing**: The DLL processes records in batches for efficiency
-   **Connection Pooling**: Reuses device connections when possible
-   **Memory Management**: Proper disposal of resources after operations
-   **Async Operations**: Non-blocking operations for better responsiveness

## Security Considerations

-   **Network Security**: Ensure device communication happens over secure networks
-   **Authentication**: Use device passwords when available
-   **Input Validation**: Validate all inputs before passing to DLL
-   **Error Handling**: Never expose raw error messages to end users

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Verify device network connectivity
3. Ensure .NET 8.0 runtime is installed
4. Check Python.NET compatibility with your Python version

## License

This project is provided as-is for ZK biometric device integration with Django applications.

## Changelog

### Version 1.0.0

-   Initial release with basic device connectivity
-   Attendance record fetching functionality
-   Python.NET integration support
-   JSON-based API interface
-   Comprehensive error handling
