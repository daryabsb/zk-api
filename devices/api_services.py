"""
Services for ZK device operations using an external HTTP API service.
The external service is provided by the BioFetcher.exe SDK (HTTP server)
and communicates with ZK biometric devices. Django talks to it over HTTP.
"""

import requests
from django.conf import settings
from django.utils import timezone
from .models import ZKDevice, DeviceSyncLog


class ZKAPIService:
    """
    High-level service used by Django to interact with ZK devices.

    It calls a separate HTTP service (BioFetcher) that exposes
    simple HTTP endpoints and handles all communication with the devices.
    """
    
    def __init__(self):
        # Base URL of the BioFetcher HTTP service, e.g. http://localhost:4000
        self.base_url = getattr(settings, "ZK_API_URL", "http://localhost:4000")
    
    def _request(self, path, params=None, timeout=60):
        """
        Helper to perform a GET request to the wrapper API and return JSON.
        """
        url = f"{self.base_url}{path}"
        try:
            response = requests.get(url, params=params or {}, timeout=timeout)
            response.raise_for_status()
            return response.json(), ""
        except requests.exceptions.RequestException as e:
            return None, f"API request failed: {str(e)}"
        except ValueError as e:
            return None, f"Invalid JSON response: {str(e)}"
    
    def test_connection(self, device):
        """
        Test connection to a ZK device using the BioFetcher API.
        """
        params = {
            "ip": str(device.ip_address),
            "port": int(device.port),
            "key": 0,
            "depId": getattr(device, "department_id", "w1"),
            "areaId": getattr(device, "area_id", 1),
            "deviceId": getattr(device, "id", 1),
        }
        data, error = self._request("/status", params=params, timeout=15)
        if error:
            return False, error
        
        return bool(data.get("success")), data.get("error", "")
    
    def get_employees(self, device):
        """
        Get employees from a ZK device via BioFetcher API.

        Returns a list of employee dicts and an error string (empty on success).
        """
        params = {
            "ip": str(device.ip_address),
            "port": int(device.port),
            "key": 0,
            "depId": getattr(device, "department_id", "w1"),
            "areaId": getattr(device, "area_id", 1),
            "deviceId": getattr(device, "id", 1),
        }
        data, error = self._request("/fetch-users", params=params, timeout=120)
        if error:
            return [], error
        
        if not data.get("success"):
            return [], data.get("error", "Unknown error from wrapper API")
        
        employees = (
            data.get("employees")
            or data.get("users")
            or data.get("data")
            or []
        )
        
        adapted = []
        for emp in employees:
            pin = (
                emp.get("EmployeeId")
                or emp.get("employee_id")
                or emp.get("EmployeeID")
                or emp.get("pin")
                or emp.get("emp_code")
            )
            adapted.append(
                {
                    "pin": pin,
                    "name": emp.get("Name") or emp.get("name") or emp.get("full_name", ""),
                    "department": emp.get("Department") or emp.get("department", ""),
                    "position": emp.get("Position") or emp.get("position", ""),
                }
            )
        
        return adapted, ""
    
    def get_attendance_records(self, device, start_time=None, end_time=None, all_records=False):
        """
        Get attendance records from device via wrapper API.

        If start_time/end_time are not provided, use last_sync or a default
        window (last 7 days) for normal sync, or a larger window when
        all_records is True.
        """
        if not start_time or not end_time:
            end_time = timezone.now()
            if all_records:
                start_time = end_time - timezone.timedelta(days=365)
            else:
                start_time = device.last_sync or (end_time - timezone.timedelta(days=7))
        
        params = {
            "ip": str(device.ip_address),
            "port": int(device.port),
            "key": 0,
            "depId": getattr(device, "department_id", "w1"),
            "areaId": getattr(device, "area_id", 1),
            "deviceId": getattr(device, "id", 1),
            "from": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "to": end_time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        data, error = self._request("/fetch-logs", params=params, timeout=180)
        if error:
            return [], error
        
        if not data.get("success"):
            return [], data.get("error", "Unknown error from wrapper API")
        
        raw_records = (
            data.get("records")
            or data.get("attendance")
            or data.get("logs")
            or data.get("data")
            or []
        )
        
        adapted_records = []
        for r in raw_records:
            employee_id = (
                r.get("EmployeeID")
                or r.get("EmployeeId")
                or r.get("employee_id")
                or r.get("emp_code")
            )
            punch_time = r.get("PunchTime") or r.get("punch_time")
            device_id = r.get("DeviceID") or r.get("device_id") or getattr(device, "id", 0)
            verify_mode = r.get("VerificationMode") or r.get("verify_type") or 0
            status = r.get("Status") or r.get("punch_state") or 0
            
            adapted_records.append(
                {
                    "EmployeeID": employee_id,
                    "PunchTime": punch_time,
                    "DeviceID": device_id,
                    "VerificationMode": verify_mode,
                    "Status": status,
                }
            )
        
        return adapted_records, ""
    
    def sync_employees(self, device, fetch_all=False):
        """Sync employees from device to HR system using wrapper API."""
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
                    
                    # Get department from device data if available
                    department = emp_data.get('department', 'Unknown')
                    position = emp_data.get('position', 'Employee')
                    
                    # Create or update employee
                    employee, created = Employee.objects.update_or_create(
                        employee_id=emp_data.get('pin'),
                        defaults={
                            'user': user,
                            'name': emp_data.get('name', ''),  # Save employee name from device
                            'department': department,
                            'position': position,
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
    
    def sync_attendance(self, device, fetch_all_from_225=False):
        """Sync attendance records from device using wrapper API."""
        log = DeviceSyncLog(device=device, sync_type='attendance')
        
        try:
            from django.utils import timezone
            from datetime import datetime
            from attendance.models import AttendanceRecord, Employee
            
            end_time = timezone.now()
            
            if fetch_all_from_225:
                start_time_225 = datetime(2024, 8, 13)
                records, error = self.get_attendance_records(device, start_time_225, end_time)
            else:
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
