"""
Django management command to sync ZK devices.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from devices.models import ZKDevice
from devices.services import ZKDeviceService


class Command(BaseCommand):
    help = 'Sync attendance records from ZK biometric devices'

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

    def handle(self, *args, **options):
        device_id = options.get('device_id')
        sync_all = options.get('all')
        
        service = ZKDeviceService()
        
        if device_id:
            # Sync specific device
            try:
                device = ZKDevice.objects.get(id=device_id)
                self.stdout.write(f"Syncing device: {device.name} ({device.ip_address})")
                
                records_synced, error = service.sync_attendance(device)
                
                if error:
                    self.stderr.write(f"Error: {error}")
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Successfully synced {records_synced} records from {device.name}"
                        )
                    )
                    
            except ZKDevice.DoesNotExist:
                self.stderr.write(f"Device with ID {device_id} not found")
            except Exception as e:
                self.stderr.write(f"Error: {str(e)}")
                
        elif sync_all:
            # Sync all active devices
            devices = ZKDevice.objects.filter(is_active=True)
            total_records = 0
            
            self.stdout.write(f"Syncing {devices.count()} active devices...")
            
            for device in devices:
                try:
                    self.stdout.write(f"Syncing {device.name}...")
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
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Completed! Total records synced: {total_records}"
                )
            )
            
        else:
            self.stderr.write(
                "Please specify --device-id <id> to sync a specific device "
                "or --all to sync all active devices"
            )