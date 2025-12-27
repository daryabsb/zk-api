#!/usr/bin/env python3
"""
Real ZK SDK Integration - FastAPI service for ZK device communication
Uses the official ZKBiometricDLL for real device data
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import aiohttp
import json
import uuid
from enum import Enum
import time
import os
import sys

# Add the DLL directory to the CLR path
dll_path = os.path.join(os.path.dirname(__file__), 'TempDLL', 'output')
sys.path.append(dll_path)

# Import .NET CLR and load the ZK Biometric DLL
import clr
clr.AddReference(os.path.join(dll_path, 'ZKBiometricDLL.dll'))

# Import the .NET classes with error handling
real_dll_available = False
api_instance = None

try:
    from ZKBiometricDLL import ZKBiometricAPI
    real_dll_available = True
    api_instance = ZKBiometricAPI()
    print("SUCCESS: Real ZK Biometric DLL loaded and API instance created")
except Exception as e:
    print(f"WARNING: Real ZK Biometric DLL not available: {e}")
    print("Falling back to simulation mode for testing")
    real_dll_available = False

app = FastAPI(title="ZK Device API - Real SDK", version="3.0.0")

import argparse
parser = argparse.ArgumentParser(description='ZK Device API Server with Real SDK')
parser.add_argument('--port', type=int, default=5002, help='Port to run the server on')
parser.add_argument('--simulate', action='store_true', help='Use simulation mode instead of real DLL')
args = parser.parse_args()

# In-memory storage for async operation status
operation_status = {}

class DeviceRequest(BaseModel):
    ip_address: str
    port: int = 4370
    serial_number: str = ""
    model: str = ""

class FilterRequest(BaseModel):
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    employee_ids: Optional[List[str]] = None
    departments: Optional[List[str]] = None
    limit: Optional[int] = None
    offset: Optional[int] = None

class DeviceDataWithFilters(DeviceRequest):
    filters: Optional[FilterRequest] = None

class TestConnectionResponse(BaseModel):
    success: bool
    message: str

class Employee(BaseModel):
    pin: str
    name: str
    card_number: str
    privilege: int
    department: str
    position: str

class AttendanceRecord(BaseModel):
    EmployeeID: str
    PunchTime: str
    DeviceID: int
    VerificationMode: int
    Status: int
    Department: str

class OperationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class AsyncOperationResponse(BaseModel):
    operation_id: str
    status: OperationStatus
    progress: int
    message: str

class OperationResultResponse(BaseModel):
    operation_id: str
    status: OperationStatus
    progress: int
    message: str
    result: Optional[Any] = None

# Create ZK API instance only if real DLL is available
if real_dll_available:
    zk_api = ZKBiometricAPI()
    print("Real ZK API instance created successfully")
else:
    zk_api = None
    print("Using simulation mode - no real ZK API instance")

@app.get("/")
async def root():
    return {
        "message": "ZK Device API with Real SDK Integration",
        "version": "3.0.0",
        "status": "running"
    }

@app.post("/test-connection", response_model=TestConnectionResponse)
async def test_connection(device_data: DeviceRequest):
    """Test connection to ZK device using real SDK"""
    try:
        device_json = json.dumps({
            "IpAddress": device_data.ip_address,
            "Port": device_data.port,
            "SerialNumber": device_data.serial_number,
            "Model": device_data.model
        })
        
        result = zk_api.TestConnection(device_json)
        result_data = json.loads(result)
        
        if result_data['success']:
            return TestConnectionResponse(
                success=True,
                message=f"Device {device_data.ip_address}:{device_data.port} - {'Connected' if result_data['connected'] else 'Disconnected'}"
            )
        else:
            return TestConnectionResponse(
                success=False,
                message=f"Connection failed: {result_data.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        return TestConnectionResponse(
            success=False,
            message=f"Error testing connection: {str(e)}"
        )

@app.post("/get-device-info")
async def get_device_info():
    """Get device information using real SDK"""
    try:
        if not real_dll_available:
            # Return simulation data
            return {
                "success": True,
                "device": {
                    "Name": "ZK Device Simulation",
                    "IpAddress": "192.168.1.201",
                    "Port": 4370,
                    "SerialNumber": "SIM123456",
                    "Model": "ZK-Test",
                    "FirmwareVersion": "v2.0.0"
                }
            }
        
        result = zk_api.GetDeviceInfo()
        return json.loads(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting device info: {str(e)}")

@app.post("/get-employees")
async def get_employees(device_data: DeviceRequest):
    """Get employees from ZK device using real SDK"""
    try:
        if not real_dll_available:
            # Return simulation data
            return {
                "success": True,
                "employees": [
                    {
                        "pin": "001",
                        "name": "John Doe",
                        "card_number": "1001",
                        "privilege": 1,
                        "department": "IT",
                        "position": "Developer"
                    },
                    {
                        "pin": "002", 
                        "name": "Jane Smith",
                        "card_number": "1002",
                        "privilege": 1,
                        "department": "HR",
                        "position": "Manager"
                    },
                    {
                        "pin": "003",
                        "name": "Bob Johnson",
                        "card_number": "1003",
                        "privilege": 2,
                        "department": "Finance",
                        "position": "Analyst"
                    }
                ]
            }
        
        device_json = json.dumps({
            "IpAddress": device_data.ip_address,
            "Port": device_data.port,
            "SerialNumber": device_data.serial_number,
            "Model": device_data.model
        })
        
        result = zk_api.GetEmployees(device_json)
        result_data = json.loads(result)
        
        if result_data['success']:
            return result_data
        else:
            raise HTTPException(status_code=500, detail=result_data.get('error', 'Unknown error'))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting employees: {str(e)}")

@app.post("/get-attendance")
async def get_attendance(device_data: DeviceDataWithFilters):
    """Get attendance records from ZK device using real SDK"""
    try:
        device_json = json.dumps({
            "IpAddress": device_data.ip_address,
            "Port": device_data.port,
            "SerialNumber": device_data.serial_number,
            "Model": device_data.model
        })
        
        # Use default date range if not specified
        end_time = datetime.now().isoformat()
        start_time = (datetime.now() - timedelta(days=7)).isoformat()
        
        if device_data.filters:
            if device_data.filters.start_time:
                start_time = device_data.filters.start_time
            if device_data.filters.end_time:
                end_time = device_data.filters.end_time
        
        result = zk_api.GetAttendanceRecords(device_json, start_time, end_time)
        result_data = json.loads(result)
        
        if result_data['success']:
            records = result_data.get('records', [])
            
            # Apply additional filters if specified
            if device_data.filters:
                filtered_records = records
                
                if device_data.filters.employee_ids:
                    filtered_records = [r for r in filtered_records 
                                      if r.get("EmployeeID") in device_data.filters.employee_ids]
                
                if device_data.filters.departments:
                    filtered_records = [r for r in filtered_records 
                                      if r.get("Department") in device_data.filters.departments]
                
                # Apply pagination
                if device_data.filters.limit is not None:
                    start = device_data.filters.offset or 0
                    filtered_records = filtered_records[start:start + device_data.filters.limit]
                
                result_data['records'] = filtered_records
                result_data['filtered_count'] = len(filtered_records)
            
            return result_data
        else:
            raise HTTPException(status_code=500, detail=result_data.get('error', 'Unknown error'))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting attendance: {str(e)}")

@app.post("/connect-device")
async def connect_device(device_data: DeviceRequest):
    """Connect to ZK device using real SDK"""
    try:
        device_json = json.dumps({
            "IpAddress": device_data.ip_address,
            "Port": device_data.port,
            "SerialNumber": device_data.serial_number,
            "Model": device_data.model
        })
        
        result = zk_api.ConnectDevice(device_json)
        return json.loads(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error connecting device: {str(e)}")

@app.post("/disconnect-device")
async def disconnect_device(device_data: DeviceRequest):
    """Disconnect from ZK device using real SDK"""
    try:
        device_json = json.dumps({
            "IpAddress": device_data.ip_address,
            "Port": device_data.port,
            "SerialNumber": device_data.serial_number,
            "Model": device_data.model
        })
        
        result = zk_api.DisconnectDevice(device_json)
        return json.loads(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error disconnecting device: {str(e)}")

# Async endpoints for long-running operations
@app.post("/async/get-employees", response_model=AsyncOperationResponse)
async def async_get_employees(
    device_data: DeviceRequest, 
    background_tasks: BackgroundTasks
):
    """Start async employee data retrieval using real SDK"""
    operation_id = str(uuid.uuid4())
    operation_status[operation_id] = {
        "status": OperationStatus.PENDING,
        "progress": 0,
        "message": "Operation queued"
    }
    
    background_tasks.add_task(
        process_real_async_operation, 
        operation_id, device_data, "get-employees"
    )
    
    return AsyncOperationResponse(
        operation_id=operation_id,
        status=OperationStatus.PENDING,
        progress=0,
        message="Operation started"
    )

@app.post("/async/get-attendance", response_model=AsyncOperationResponse)
async def async_get_attendance(
    device_data: DeviceDataWithFilters, 
    background_tasks: BackgroundTasks
):
    """Start async attendance data retrieval using real SDK"""
    operation_id = str(uuid.uuid4())
    operation_status[operation_id] = {
        "status": OperationStatus.PENDING,
        "progress": 0,
        "message": "Operation queued"
    }
    
    background_tasks.add_task(
        process_real_async_operation, 
        operation_id, device_data, "get-attendance", device_data.filters
    )
    
    return AsyncOperationResponse(
        operation_id=operation_id,
        status=OperationStatus.PENDING,
        progress=0,
        message="Operation started"
    )

@app.get("/async/status/{operation_id}", response_model=OperationResultResponse)
async def get_async_status(operation_id: str):
    """Get status of async operation"""
    if operation_id not in operation_status:
        raise HTTPException(status_code=404, detail="Operation not found")
    
    status = operation_status[operation_id]
    return OperationResultResponse(
        operation_id=operation_id,
        status=status["status"],
        progress=status["progress"],
        message=status["message"],
        result=status.get("result")
    )

async def process_real_async_operation(operation_id: str, device: DeviceRequest, 
                                     endpoint: str, filters: Optional[FilterRequest] = None):
    """Process long-running operation asynchronously using real SDK"""
    try:
        operation_status[operation_id] = {
            "status": OperationStatus.PROCESSING,
            "progress": 10,
            "message": "Connecting to device"
        }
        
        device_json = json.dumps({
            "IpAddress": device.ip_address,
            "Port": device.port,
            "SerialNumber": device.serial_number,
            "Model": device.model
        })
        
        # Connect to device
        connect_result = zk_api.ConnectDevice(device_json)
        connect_data = json.loads(connect_result)
        
        if not connect_data['success']:
            raise Exception(f"Failed to connect: {connect_data.get('error', 'Unknown error')}")
        
        operation_status[operation_id] = {
            "status": OperationStatus.PROCESSING,
            "progress": 30,
            "message": "Connected to device, fetching data"
        }
        
        # Process based on endpoint
        if endpoint == "get-employees":
            result = zk_api.GetEmployees(device_json)
            result_data = json.loads(result)
            
        elif endpoint == "get-attendance":
            # Use default date range if not specified
            end_time = datetime.now().isoformat()
            start_time = (datetime.now() - timedelta(days=7)).isoformat()
            
            if filters:
                if filters.start_time:
                    start_time = filters.start_time
                if filters.end_time:
                    end_time = filters.end_time
            
            result = zk_api.GetAttendanceRecords(device_json, start_time, end_time)
            result_data = json.loads(result)
            
            # Apply additional filters
            if result_data['success'] and filters:
                records = result_data.get('records', [])
                
                if filters.employee_ids:
                    records = [r for r in records 
                              if r.get("EmployeeID") in filters.employee_ids]
                
                if filters.departments:
                    records = [r for r in records 
                              if r.get("Department") in filters.departments]
                
                # Apply pagination
                if filters.limit is not None:
                    start = filters.offset or 0
                    records = records[start:start + filters.limit]
                
                result_data['records'] = records
                result_data['filtered_count'] = len(records)
        
        else:
            raise Exception(f"Unknown endpoint: {endpoint}")
        
        # Disconnect from device
        zk_api.DisconnectDevice(device_json)
        
        if result_data['success']:
            operation_status[operation_id] = {
                "status": OperationStatus.COMPLETED,
                "progress": 100,
                "message": "Operation completed successfully",
                "result": result_data
            }
        else:
            raise Exception(result_data.get('error', 'Unknown error'))
            
    except Exception as e:
        operation_status[operation_id] = {
            "status": OperationStatus.FAILED,
            "progress": 0,
            "message": f"Operation failed: {str(e)}",
            "result": None
        }

if __name__ == "__main__":
    import uvicorn
    print(f"Starting ZK Device API with Real SDK on port {args.port}")
    print(f"DLL path: {dll_path}")
    print("Available endpoints:")
    print("  - POST /test-connection")
    print("  - POST /get-device-info") 
    print("  - POST /get-employees")
    print("  - POST /get-attendance")
    print("  - POST /connect-device")
    print("  - POST /disconnect-device")
    print("  - POST /async/get-employees")
    print("  - POST /async/get-attendance")
    print("  - GET  /async/status/{operation_id}")
    
    uvicorn.run(app, host="0.0.0.0", port=args.port)