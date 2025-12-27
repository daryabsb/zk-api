#!/usr/bin/env python3
"""
Simple test to verify ZKBiometricDLL loading
"""

import clr
import os
import sys

# Add the DLL directory to the CLR path
dll_path = os.path.join(os.path.dirname(__file__), 'TempDLL', 'output')
print(f"DLL path: {dll_path}")

# Load the DLL
clr.AddReference(os.path.join(dll_path, 'ZKBiometricDLL.dll'))
print("DLL loaded successfully")

# Try to import using the exact namespace from the C# code
try:
    # Import the .NET classes using the full namespace
    from ZKBiometricDLL import ZKBiometricAPI
    print("SUCCESS: ZKBiometricAPI imported")
    
    # Create an instance
    api = ZKBiometricAPI()
    print("API instance created")
    
    # Test a simple method
    result = api.GetDeviceInfo()
    print(f"GetDeviceInfo result: {result}")
    
    # Parse the JSON result
    import json
    device_info = json.loads(result)
    print(f"Parsed result: {device_info}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("Test completed")