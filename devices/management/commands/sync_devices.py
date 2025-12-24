"""
Django management command to sync ZK devices.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from devices.models import ZKDevice
from devices.api_services import get_api_service


class Command(BaseCommand):
    help = 'Sync data from ZK biometric devices (attendance and employees)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--device-id',
            type=int,
            help='Sync specific device by ID',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Sync all active devices',
        )
        parser.add_argument(
            '--employees',
            action='store_true',
            help='Sync employees instead of attendance',
        )
        parser.add_argument(
            '--complete',
            action='store_true',
            help='Complete sync: employees first, then attendance',
        )

    def handle(self, *args, **options):
        device_id = options.get('device_id')
        sync_all = options.get('all')
        sync_employees = options.get('employees')
        sync_complete = options.get('complete')
        
        service = get_api_service()
        
        if sync_complete:
            # Complete sync: employees first, then attendance
            self.stdout.write("Starting complete sync (employees + attendance)...")
            
            # Sync employees
            employees_result = self._sync_employees(service, device_id, sync_all)
            
            # Sync attendance
            attendance_result = self._sync_attendance(service, device_id, sync_all)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Complete sync completed! "
                    f"Employees: {employees_result['total']} synced, "
                    f"Attendance: {attendance_result['total']} records"
                )
            )
            return
        
        if sync_employees:
            # Sync employees only
            result = self._sync_employees(service, device_id, sync_all)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Employee sync completed! {result['total']} employees synced"
                )
            )
        else:
            # Sync attendance only (default)
            result = self._sync_attendance(service, device_id, sync_all)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Attendance sync completed! {result['total']} records synced"
                )
            )
    
    def _sync_employees(self, service, device_id, sync_all):
        """Sync employees from devices."""
        total_employees = 0
        
        if device_id:
            # Sync specific device
            try:
                device = ZKDevice.objects.get(id=device_id)
                self.stdout.write(f"Syncing employees from: {device.name} ({device.ip_address})")
                
                employees_synced, error = service.sync_employees(device)
                
                if error:
                    self.stderr.write(f"Error: {error}")
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Successfully synced {employees_synced} employees from {device.name}"
                        )
                    )
                    total_employees += employees_synced
                    
            except ZKDevice.DoesNotExist:
                self.stderr.write(f"Device with ID {device_id} not found")
            except Exception as e:
                self.stderr.write(f"Error: {str(e)}")
                
        elif sync_all:
            # Sync all active devices
            devices = ZKDevice.objects.filter(is_active=True)
            
            self.stdout.write(f"Syncing employees from {devices.count()} active devices...")
            
            for device in devices:
                try:
                    self.stdout.write(f"Syncing employees from {device.name}...")
                    employees_synced, error = service.sync_employees(device)
                    
                    if error:
                        self.stderr.write(f"Error with {device.name}: {error}")
                    else:
                        self.stdout.write(
                            f"✓ {device.name}: {employees_synced} employees"
                        )
                        total_employees += employees_synced
                        
                except Exception as e:
                    self.stderr.write(f"Error with {device.name}: {str(e)}")
                    continue
        
        return {'total': total_employees}
    
    def _sync_attendance(self, service, device_id, sync_all):
        """Sync attendance records from devices."""
        total_records = 0
        
        if device_id:
            # Sync specific device
            try:
                device = ZKDevice.objects.get(id=device_id)
                self.stdout.write(f"Syncing attendance from: {device.name} ({device.ip_address})")
                
                records_synced, error = service.sync_attendance(device)
                
                if error:
                    self.stderr.write(f"Error: {error}")
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Successfully synced {records_synced} records from {device.name}"
                        )
                    )
                    total_records += records_synced
                    
            except ZKDevice.DoesNotExist:
                self.stderr.write(f"Device with ID {device_id} not found")
            except Exception as e:
                self.stderr.write(f"Error: {str(e)}")
                
        elif sync_all:
            # Sync all active devices
            devices = ZKDevice.objects.filter(is_active=True)
            
            self.stdout.write(f"Syncing attendance from {devices.count()} active devices...")
            
            for device in devices:
                try:
                    self.stdout.write(f"Syncing attendance from {device.name}...")
                    records_synced, error = service.sync_attendance(device)
                    
                    if error:
                        self.stderr.write(f"Error with {device.name}: {error}")
                    else:
                        self.stdout.write(
                            f"✓ {device.name}: {records_synced} records"
                        )
                        total_records += records_synced
                        
                except Exception as e:
                    self.stderr.write(f"Error with {device.name}: {str(e)}")
                    continue
        
        return {'total': total_records}