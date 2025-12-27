#!/usr/bin/env python3
"""
Debug script to investigate DLL loading issues.
"""

import clr
import sys
import os

def debug_dll_loading():
    """Debug DLL loading issues."""
    
    # Add the output directory to Python path
    output_dir = os.path.join(os.path.dirname(__file__), 'TempDLL', 'output')
    if output_dir not in sys.path:
        sys.path.append(output_dir)
    
    dll_path = os.path.join(output_dir, 'ZKBiometricDLL.dll')
    
    print(f"DLL path: {dll_path}")
    print(f"DLL exists: {os.path.exists(dll_path)}")
    
    try:
        # Load the assembly
        clr.AddReference(dll_path)
        print("SUCCESS: DLL referenced via clr.AddReference")
        
        # Try to import the module
        from ZKBiometricDLL import ZKBiometricAPI
        print("SUCCESS: Module imported successfully")
        
        # Test creating an instance
        api = ZKBiometricAPI()
        print("SUCCESS: API instance created")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # For ReflectionTypeLoadException, get loader exceptions
        if hasattr(e, 'LoaderExceptions'):
            print("\nLoader exceptions:")
            for loader_ex in e.LoaderExceptions:
                print(f"  - {loader_ex}")
        
        return False

def check_dll_dependencies():
    """Check what dependencies the DLL has."""
    
    try:
        from System.Reflection import Assembly
        from System.IO import File
        
        dll_path = os.path.join(os.path.dirname(__file__), 'TempDLL', 'output', 'ZKBiometricDLL.dll')
        
        if not File.Exists(dll_path):
            print("DLL not found")
            return
        
        # Load assembly and check dependencies
        assembly = Assembly.LoadFrom(dll_path)
        print(f"Assembly: {assembly.FullName}")
        
        # Get referenced assemblies
        ref_assemblies = assembly.GetReferencedAssemblies()
        print(f"\nReferenced assemblies ({len(ref_assemblies)}):")
        for ref in ref_assemblies:
            print(f"  - {ref.Name} (Version: {ref.Version})")
        
    except Exception as e:
        print(f"Error checking dependencies: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("DEBUGGING DLL LOADING ISSUES")
    print("=" * 60)
    
    print("\n1. Testing DLL loading:")
    success = debug_dll_loading()
    
    print("\n2. Checking DLL dependencies:")
    check_dll_dependencies()
    
    print("\n" + "=" * 60)
    if success:
        print("DEBUG COMPLETED - DLL LOADING SUCCESSFUL!")
    else:
        print("DEBUG COMPLETED - DLL LOADING ISSUES DETECTED!")