"""
Services for ZK device operations using HTTP API instead of Python.NET.
This avoids the .NET compatibility issues.
"""

import requests
import json
from django.conf import settings
from django.utils import timezone
from .models import ZKDevice, DeviceSyncLog


class ZKAPIService:
    """Service class for ZK device operations using HTTP API."""
    
    def __init__(self):
        self.base_url = getattr(settings, 'ZK_API_URL', 'http://localhost:5000')
    
    def test_connection(self, device):
        """Test connection to a ZK device via API."""
        try:
            response = requests.post(
                f"{self.base_url}/test-connection",
                json={
                    "ip_address": device.ip_address,
                    "port": device.port,
                    "serial_number": device.serial_number or "",
                    "model": device.model or ""
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            return result.get('success', False), result.get('message', '')
            
        except requests.exceptions.RequestException as e:
            return False, f"API request failed: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def get_employees(self, device):
        """Get employees from a ZK device via API."""
        try:
            response = requests.post(
                f"{self.base_url}/get-employees",
                json={
                    "ip_address": device.ip_address,
                    "port": device.port,
                    "serial_number": device.serial_number or "",
                    "model": device.model or ""
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('success'):
                return result.get('employees', []), ""
            else:
                return [], result.get('error', 'Unknown error')
                
        except requests.exceptions.RequestException as e:
            return [], f"API request failed: {str(e)}"
        except Exception as e:
            return [], f"Unexpected error: {str(e)}"
    
    def get_attendance_records(self, device, start_time, end_time):
        """Get attendance records from device via API."""
        try:
            response = requests.post(
                f"{self.base_url}/get-attendance",
                json={
                    "ip_address": device.ip_address,
                    "port": device.port,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat()
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('success'):
                return result.get('records', []), ""
            else:
                return [], result.get('error', 'Unknown error')
                
        except requests.exceptions.RequestException as e:
            return [], f"API request failed: {str(e)}"
        except Exception as e:
            return [], f"Unexpected error: {str(e)}"
    
    def sync_employees(self, device):
        """Sync employees from device to HR system."""
        log = DeviceSyncLog(device=device, sync_type='employees')
        
        try:
            employees, error = self.get_employees(device)
            
            if error:
                log.success = False
                log.error_message = error
                log.save()
                return 0, error
            
            # Process employees and save to HR database
            from attendance.models import Employee
            from django.contrib.auth.models import User
            
            synced_count = 0
            for emp_data in employees:
                try:
                    # Create or get user
                    username = f"emp_{emp_data.get('pin')}"
                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'first_name': emp_data.get('name', '').split(' ')[0] if ' ' in emp_data.get('name', '') else emp_data.get('name', ''),
                            'last_name': emp_data.get('name', '').split(' ')[1] if ' ' in emp_data.get('name', '') else '',
                            'email': f"{username}@company.com"
                        }
                    )
                    
                    # Create or update employee
                    employee, created = Employee.objects.update_or_create(
                        employee_id=emp_data.get('pin'),
                        defaults={
                            'user': user,
                            'department': 'Unknown',
                            'position': 'Employee',
                            'hire_date': '2023-01-01'  # Default date
                        }
                    )
                    synced_count += 1
                    
                except Exception as e:
                    continue
            
            log.records_synced = synced_count
            log.success = True
            log.completed_at = timezone.now()
            log.save()
            
            return synced_count, ""
            
        except Exception as e:
            log.success = False
            log.error_message = str(e)
            log.completed_at = timezone.now()
            log.save()
            return 0, str(e)
    
    def sync_attendance(self, device):
        """Sync attendance records from device."""
        log = DeviceSyncLog(device=device, sync_type='attendance')
        
        try:
            from django.utils import timezone
            from attendance.models import AttendanceRecord, Employee
            
            end_time = timezone.now()
            start_time = device.last_sync or (end_time - timezone.timedelta(days=7))
            
            records, error = self.get_attendance_records(device, start_time, end_time)
            
            if error:
                log.success = False
                log.error_message = error
                log.completed_at = timezone.now()
                log.save()
                return 0, error
            
            synced_count = 0
            for record in records:
                try:
                    employee_id = record.get('EmployeeID')
                    punch_time = record.get('PunchTime')
                    
                    if employee_id and punch_time:
                        # Check if record already exists to avoid duplicates
                        if not AttendanceRecord.objects.filter(
                            employee__employee_id=employee_id,
                            punch_time=punch_time,
                            device_ip=device.ip_address
                        ).exists():
                            
                            employee = Employee.objects.get(employee_id=employee_id)
                            AttendanceRecord.objects.create(
                                employee=employee,
                                punch_time=punch_time,
                                device_id=record.get('DeviceID', 0),
                                device_ip=device.ip_address,
                                verification_mode=record.get('VerificationMode', 0),
                                status=record.get('Status', 0)
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
            log.completed_at = timezone.now()
            log.save()
            
            return synced_count, ""
            
        except Exception as e:
            log.success = False
            log.error_message = str(e)
            log.completed_at = timezone.now()
            log.save()
            return 0, str(e)


def get_api_service():
    """Factory function to get the API service instance."""
    return ZKAPIService()