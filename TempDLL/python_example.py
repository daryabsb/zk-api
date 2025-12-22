#!/usr/bin/env python3
"""
Example Python script showing how to use the ZKBiometricDLL from Python
using Python.NET (pythonnet).

Prerequisites:
1. Install Python.NET: pip install pythonnet
2. Build the DLL: run build.bat
3. Copy the DLL files to your Python project
"""

import clr
import os
import json
from datetime import datetime, timedelta

# Add the DLL directory to the CLR path
dll_path = os.path.join(os.path.dirname(__file__), 'output')
clr.AddReference(os.path.join(dll_path, 'ZKBiometricDLL.dll'))

# Import the .NET classes
from ZKBiometricDLL import ZKBiometricAPI

def test_zk_biometric():
    """Example usage of the ZK Biometric DLL from Python"""
    
    # Create an instance of the API
    api = ZKBiometricAPI()
    
    try:
        print("=== Testing ZK Biometric DLL from Python ===")
        
        # 1. Get sample device info
        print("\n1. Getting device info...")
        result = api.GetDeviceInfo()
        device_info = json.loads(result)
        
        if device_info['success']:
            device = device_info['device']
            print(f"   Device: {device['Name']} at {device['IpAddress']}:{device['Port']}")
            
            # 2. Test connection
            print("\n2. Testing connection...")
            device_json = json.dumps(device)
            result = api.TestConnection(device_json)
            conn_result = json.loads(result)
            
            if conn_result['success']:
                print(f"   Connection: {'Connected' if conn_result['connected'] else 'Disconnected'}")
                
                # 3. Get device status
                print("\n3. Getting device status...")
                result = api.GetDeviceStatus(device_json)
                status_result = json.loads(result)
                
                if status_result['success']:
                    print(f"   Status: {status_result['status']}")
                    
                    # 4. Connect to device
                    print("\n4. Connecting to device...")
                    result = api.ConnectDevice(device_json)
                    connect_result = json.loads(result)
                    
                    if connect_result['success'] and connect_result['connected']:
                        print("   Connected successfully!")
                        
                        # 5. Get attendance records
                        print("\n5. Fetching attendance records...")
                        end_time = datetime.now()
                        start_time = end_time - timedelta(hours=24)
                        
                        result = api.GetAttendanceRecords(
                            device_json,
                            start_time.isoformat(),
                            end_time.isoformat()
                        )
                        records_result = json.loads(result)
                        
                        if records_result['success']:
                            records = records_result['records']
                            print(f"   Found {len(records)} attendance records:")
                            for record in records[:3]:  # Show first 3 records
                                print(f"     - {record['EmployeeId']} at {record['RecordTime']} ({record['Type']})")
                            if len(records) > 3:
                                print(f"     ... and {len(records) - 3} more records")
                        else:
                            print(f"   Error: {records_result['error']}")
                        
                        # 6. Get employees
                        print("\n6. Fetching employees...")
                        result = api.GetEmployees(device_json)
                        employees_result = json.loads(result)
                        
                        if employees_result['success']:
                            employees = employees_result['employees']
                            print(f"   Found {len(employees)} employees:")
                            for emp in employees:
                                print(f"     - {emp['EmployeeId']}: {emp['Name']} ({emp['Department']})")
                        else:
                            print(f"   Error: {employees_result['error']}")
                        
                        # 7. Disconnect
                        print("\n7. Disconnecting from device...")
                        result = api.DisconnectDevice(device_json)
                        disconnect_result = json.loads(result)
                        
                        if disconnect_result['success']:
                            print("   Disconnected successfully!")
                        else:
                            print(f"   Error: {disconnect_result['error']}")
                        
                    else:
                        print(f"   Connection failed: {connect_result.get('error', 'Unknown error')}")
                        
                else:
                    print(f"   Status check failed: {status_result['error']}")
                    
            else:
                print(f"   Connection test failed: {conn_result['error']}")
                
        else:
            print(f"   Device info failed: {device_info['error']}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        # Clean up
        api.Dispose()
        print("\n=== Test completed ===")

def django_integration_example():
    """
    Example of how you might use this in a Django view
    """
    
    # This would typically be in your Django views.py
    
    def get_attendance_data(request, device_ip):
        """
        Django view function to get attendance data from ZK device
        """
        try:
            # Initialize the API
            api = ZKBiometricAPI()
            
            # Create device configuration
            device_config = {
                'IpAddress': device_ip,
                'Port': 4370,
                'Name': f'Device-{device_ip}',
                'IsEnabled': True
            }
            
            device_json = json.dumps(device_config)
            
            # Get attendance records for the last 24 hours
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            result = api.GetAttendanceRecords(
                device_json,
                start_time.isoformat(),
                end_time.isoformat()
            )
            
            api.Dispose()
            
            result_data = json.loads(result)
            
            if result_data['success']:
                return JsonResponse({
                    'success': True,
                    'records': result_data['records'],
                    'count': len(result_data['records'])
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result_data['error']
                }, status=400)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

if __name__ == "__main__":
    test_zk_biometric()