"""
Services for ZK device operations using the C# DLL.
"""

import clr
import os
import json
from django.conf import settings
from .models import ZKDevice, DeviceSyncLog

# Load the C# DLL
try:
    dll_path = str(settings.DLL_PATH)
    if os.path.exists(dll_path):
        clr.AddReference(dll_path)
        from ZKBiometricDLL import ZKBiometricAPI
    else:
        raise ImportError(f"DLL not found at {dll_path}")
except Exception as e:
    print(f"Error loading DLL: {e}")
    ZKBiometricAPI = None


class ZKDeviceService:
    """Service class for ZK device operations."""
    
    def __init__(self):
        self.api = ZKBiometricAPI() if ZKBiometricAPI else None
    
    def test_connection(self, device):
        """Test connection to a ZK device."""
        if not self.api:
            return False, "DLL not loaded"
        
        device_json = json.dumps({
            'IpAddress': device.ip_address,
            'Port': device.port,
            'SerialNumber': device.serial_number or '',
            'Model': device.model or ''
        })
        
        try:
            result = self.api.TestConnection(device_json)
            result_data = json.loads(result)
            return result_data.get('success', False), result_data.get('error', '')
        except Exception as e:
            return False, str(e)
    
    def get_attendance_records(self, device, start_time, end_time):
        """Get attendance records from device."""
        if not self.api:
            return [], "DLL not loaded"
        
        device_json = json.dumps({
            'IpAddress': device.ip_address,
            'Port': device.port
        })
        
        try:
            result = self.api.GetAttendanceRecords(
                device_json, 
                start_time.isoformat(), 
                end_time.isoformat()
            )
            result_data = json.loads(result)
            
            if result_data.get('success'):
                return result_data.get('records', []), ""
            else:
                return [], result_data.get('error', 'Unknown error')
                
        except Exception as e:
            return [], str(e)
    
    def get_users(self, device):
        """Get users from device."""
        if not self.api:
            return [], "DLL not loaded"
        
        device_json = json.dumps({
            'IpAddress': device.ip_address,
            'Port': device.port
        })
        
        try:
            result = self.api.GetEmployees(device_json)
            result_data = json.loads(result)
            
            if result_data.get('success'):
                return result_data.get('employees', []), ""
            else:
                return [], result_data.get('error', 'Unknown error')
                
        except Exception as e:
            return [], str(e)
    
    def sync_attendance(self, device):
        """Sync attendance records from device and create log."""
        log = DeviceSyncLog(device=device, sync_type='attendance')
        
        try:
            from django.utils import timezone
            end_time = timezone.now()
            start_time = device.last_sync or (end_time - timezone.timedelta(days=7))
            
            records, error = self.get_attendance_records(device, start_time, end_time)
            
            if error:
                log.success = False
                log.error_message = error
                log.save()
                return 0, error
            
            # Process records and save to database
            from attendance.models import AttendanceRecord, Employee
            
            synced_count = 0
            for record in records:
                try:
                    employee_id = record.get('EmployeeID')
                    punch_time = record.get('PunchTime')
                    
                    if employee_id and punch_time:
                        employee = Employee.objects.get(employee_id=employee_id)
                        AttendanceRecord.objects.create(
                            employee=employee,
                            punch_time=punch_time,
                            device_ip=device.ip_address,
                            device_id=record.get('DeviceID', 0),
                            verification_mode=record.get('VerificationMode', 0),
                            status=record.get('Status', 0),
                        )
                        synced_count += 1
                        
                except Employee.DoesNotExist:
                    continue
                except Exception as e:
                    continue
            
            device.last_sync = end_time
            device.save()
            
            log.records_synced = synced_count
            log.success = True
            log.save()
            
            return synced_count, ""
            
        except Exception as e:
            log.success = False
            log.error_message = str(e)
            log.save()
            return 0, str(e)