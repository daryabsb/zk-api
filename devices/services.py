"""
Services for ZK device operations using the C# DLL.
"""

import clr
import os
import json
import sys
from django.conf import settings
from .models import ZKDevice, DeviceSyncLog

# Import System for reflection
import System


class ZKDeviceService:
    """Service class for ZK device operations."""
    
    def __init__(self):
        self.api = None
        self._load_dll()
    
    def _load_dll(self):
        """Load the C# DLL with proper error handling."""
        try:
            # Get the DLL path from settings
            dll_path = getattr(settings, 'DLL_PATH', None)
            if not dll_path:
                # Fallback: auto-detect DLL path
                dll_path = os.path.join(os.path.dirname(__file__), '..', '..', 'TempDLL', 'output', 'ZKBiometricDLL.dll')
            
            dll_path = os.path.abspath(dll_path)
            
            if not os.path.exists(dll_path):
                raise ImportError(f"DLL not found at {dll_path}")
            
            # Load the DLL using reflection only - avoid clr.AddReference issues
            from System.Reflection import Assembly
            assembly = Assembly.LoadFrom(dll_path)
            
            # Get the type using reflection
            api_type = assembly.GetType("ZKBiometricDLL.ZKBiometricAPI")
            if api_type is None:
                raise ImportError("ZKBiometricAPI type not found in DLL")
            
            # Create instance using reflection
            self.api = System.Activator.CreateInstance(api_type)
            print(f"Successfully loaded DLL using reflection from {dll_path}")
            
        except Exception as e:
            print(f"Error loading DLL: {e}")
            print(f"DLL path attempted: {dll_path}")
            print(f"Current working directory: {os.getcwd()}")
            self.api = None
    
    def test_connection(self, device):
        """Test connection to a ZK device."""
        if not self.api:
            return False, "DLL not loaded"
        
        device_json = json.dumps({
            'IpAddress': device.ip_address,
            'Port': device.port
        })
        
        try:
            # Use reflection to call the method
            result = self.api.GetType().GetMethod("TestConnection").Invoke(self.api, [device_json])
            result_data = json.loads(result)
            return result_data.get('success', False), result_data.get('message', '')
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
        """Get users from a ZK device."""
        if not self.api:
            return [], "DLL not loaded"
        
        device_json = json.dumps({'IpAddress': device.ip_address, 'Port': device.port})
        
        try:
            # Use reflection to call the method
            result = self.api.GetType().GetMethod("GetEmployees").Invoke(self.api, [device_json])
            result_data = json.loads(result)
            return result_data.get('employees', []), ""
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