#!/usr/bin/env python3
"""
Test script to access ZKBiometricDLL using reflection
"""

import clr
import os
import System
from System.Reflection import Assembly

# Add the DLL directory to the CLR path
dll_path = os.path.join(os.path.dirname(__file__), 'TempDLL', 'output')
print(f"DLL path: {dll_path}")

# Load the DLL using full path
clr.AddReference(os.path.join(dll_path, 'ZKBiometricDLL.dll'))
print("DLL loaded successfully")

# Load the assembly using reflection
assembly = Assembly.LoadFrom(os.path.join(dll_path, 'ZKBiometricDLL.dll'))
print(f"Assembly loaded: {assembly.FullName}")

# Get all types in the assembly
types = assembly.GetTypes()
print("\nAvailable types:")
for t in types:
    print(f"  - {t.FullName}")

# Try to find the ZKBiometricAPI type
api_type = None
for t in types:
    if "ZKBiometricAPI" in t.FullName:
        api_type = t
        break

if api_type:
    print(f"\nFound API type: {api_type.FullName}")
    
    # Create instance
    api_instance = System.Activator.CreateInstance(api_type)
    print(f"API instance created: {api_instance}")
    
    # Test a method
    method = api_type.GetMethod("GetDeviceInfo")
    if method:
        result = method.Invoke(api_instance, None)
        print(f"GetDeviceInfo result: {result}")
        
        # Try to parse as JSON
        try:
            import json
            parsed = json.loads(str(result))
            print(f"Parsed JSON: {parsed}")
        except Exception as e:
            print(f"JSON parse error: {e}")
    else:
        print("GetDeviceInfo method not found")
        
        # List all methods
        print("\nAvailable methods:")
        methods = api_type.GetMethods()
        for m in methods:
            if not m.Name.startswith("get_") and not m.Name.startswith("set_") and not m.Name.startswith("add_") and not m.Name.startswith("remove_"):
                print(f"  - {m.Name}")
else:
    print("ZKBiometricAPI type not found")

print("\nTest completed")