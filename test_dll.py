#!/usr/bin/env python3
"""
Test script to verify DLL loading works outside of Django context
"""

import clr
import os
import sys
import json

# Add the path to the DLL
dll_path = os.path.join(os.path.dirname(__file__), 'TempDLL', 'output', 'ZKBiometricDLL.dll')
print(f"DLL path: {dll_path}")
print(f"DLL exists: {os.path.exists(dll_path)}")

if not os.path.exists(dll_path):
    print("DLL not found!")
    sys.exit(1)

try:
    # Try to load the DLL
    clr.AddReference(dll_path)
    print("DLL loaded successfully!")
    
    # Try to import and use the API
    from ZKBiometricDLL import ZKBiometricAPI
    api = ZKBiometricAPI()
    print("API instance created!")
    
    # Test a simple method
    test_device = json.dumps({
        'IpAddress': '192.168.1.201',
        'Port': 4370
    })
    
    result = api.TestConnection(test_device)
    print(f"Test connection result: {result}")
    
    # Parse the JSON result
    result_data = json.loads(result)
    print(f"Parsed result: {result_data}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()