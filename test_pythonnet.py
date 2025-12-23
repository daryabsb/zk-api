#!/usr/bin/env python3
"""
Test script to verify Python.NET installation and basic functionality.
"""

import clr
import sys
import os

def test_pythonnet():
    """Test if Python.NET is working correctly."""
    
    print("Testing Python.NET installation...")
    
    # Test basic clr functionality
    try:
        # Try to load a simple .NET assembly
        clr.AddReference("System")
        from System import DateTime
        
        now = DateTime.Now
        print(f"SUCCESS: Python.NET is working! Current time: {now}")
        
        # Test basic .NET types
        from System import String, Int32
        test_string = String("Hello from .NET")
        test_int = Int32(42)
        
        print(f"String test: {test_string}")
        print(f"Int test: {test_int}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Python.NET test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

def test_dll_specific():
    """Test specific DLL loading issues."""
    
    print("\nTesting DLL specific loading...")
    
    # Add the output directory to Python path
    output_dir = os.path.join(os.path.dirname(__file__), 'TempDLL', 'output')
    if output_dir not in sys.path:
        sys.path.append(output_dir)
    
    dll_path = os.path.join(output_dir, 'ZKBiometricDLL.dll')
    
    print(f"DLL path: {dll_path}")
    print(f"DLL exists: {os.path.exists(dll_path)}")
    
    if not os.path.exists(dll_path):
        print("ERROR: DLL file not found!")
        return False
    
    try:
        # Try to get assembly info first
        import System
        from System.Reflection import Assembly
        
        # Load the assembly
        assembly = Assembly.LoadFrom(dll_path)
        print(f"Assembly loaded: {assembly.FullName}")
        
        # Try to get types from the assembly
        types = assembly.GetTypes()
        print(f"Found {len(types)} types in assembly")
        
        for t in types:
            print(f"  - {t.FullName}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to load assembly: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    success1 = test_pythonnet()
    success2 = test_dll_specific()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED!")
        sys.exit(1)