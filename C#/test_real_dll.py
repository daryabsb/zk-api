#!/usr/bin/env python3
"""
Test script to verify real ZK DLL loading and functionality
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

# Try to import the .NET classes
try:
    # Method 1: Direct import (may not work due to namespace issues)
    from ZKBiometricDLL import ZKBiometricAPI
    print("SUCCESS: ZKBiometricAPI imported directly")
    
    # Test the API
    api = ZKBiometricAPI()
    print("API instance created successfully")
    
    # Test a simple method
    result = api.GetDeviceInfo()
    print(f"GetDeviceInfo result: {result}")
    
except Exception as e:
    print(f"Direct import failed: {e}")
    
    # Method 2: Try using reflection
    try:
        import System
        # Get the assembly
        assembly = clr.LoadAssemblyFrom(os.path.join(dll_path, 'ZKBiometricDLL.dll'))
        print(f"Assembly loaded: {assembly}")
        
        # Try to create instance via reflection
        api_type = assembly.GetType("ZKBiometricDLL.ZKBiometricAPI")
        if api_type:
            print(f"Found API type: {api_type}")
            api_instance = System.Activator.CreateInstance(api_type)
            print(f"API instance created via reflection: {api_instance}")
            
            # Test a method
            result = api_type.GetMethod("GetDeviceInfo").Invoke(api_instance, None)
            print(f"GetDeviceInfo result: {result}")
        else:
            print("Could not find ZKBiometricAPI type")
            
    except Exception as e2:
        print(f"Reflection approach also failed: {e2}")

print("Test completed")