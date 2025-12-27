#!/usr/bin/env python3
"""
Enhanced FastAPI service for ZK device communication
Supports multiple endpoints with filtering and lazy communication
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

app = FastAPI(title="ZK Device API", version="2.0.0")

import argparse
parser = argparse.ArgumentParser(description='ZK Device API Server')
parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
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
    card_number: str = ""
    privilege: int = 0
    department: str = ""
    position: str = ""

class GetEmployeesResponse(BaseModel):
    success: bool
    employees: List[Employee]
    total_count: int
    filtered_count: int
    error: str = ""

class AttendanceRecord(BaseModel):
    EmployeeID: str
    PunchTime: str
    DeviceID: int
    VerificationMode: int
    Status: int
    Department: str = ""

class GetAttendanceResponse(BaseModel):
    success: bool
    records: List[AttendanceRecord]
    total_count: int
    filtered_count: int
    error: str = ""

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
    result: Optional[Dict] = None

class DeviceInfoResponse(BaseModel):
    success: bool
    device_info: Dict[str, Any]
    error: str = ""

# Simulate large dataset for testing
async def generate_large_employee_dataset():
    """Generate realistic employee data"""
    departments = ["HR", "IT", "Finance", "Operations", "Sales", "Marketing"]
    positions = ["Manager", "Developer", "Analyst", "Specialist", "Coordinator"]
    
    employees = []
    for i in range(1, 101):  # 100 employees
        dept = departments[i % len(departments)]
        pos = positions[i % len(positions)]
        
        employees.append({
            "pin": f"{i:03d}",
            "name": f"Employee {i}",
            "card_number": f"{1000 + i}",
            "privilege": 0 if i % 5 == 0 else 1,
            "department": dept,
            "position": pos
        })
    
    return employees

async def generate_large_attendance_dataset():
    """Generate realistic attendance data for 3 months"""
    records = []
    start_date = datetime.now() - timedelta(days=90)
    
    for day in range(90):
        current_date = start_date + timedelta(days=day)
        
        # Generate records for each employee
        for emp_id in range(1, 101):
            # 70% chance of having attendance record
            if emp_id % 10 != 0:  # Skip some employees occasionally
                # Generate 1-2 records per day per employee
                for record_num in range(1, 3):
                    punch_time = current_date.replace(
                        hour=8 + record_num * 4,
                        minute=30 if record_num == 1 else 0
                    )
                    
                    records.append({
                        "EmployeeID": f"{emp_id:03d}",
                        "PunchTime": punch_time.isoformat(),
                        "DeviceID": 1,
                        "VerificationMode": 1 if emp_id % 2 == 0 else 0,
                        "Status": 0 if record_num == 1 else 1,
                        "Department": f"Dept{(emp_id % 6) + 1}"
                    })
    
    return records

# Enhanced ZK device simulation with realistic data
async def simulate_zk_communication_enhanced(device: DeviceRequest, endpoint: str, filters: Optional[FilterRequest] = None):
    """Enhanced ZK device communication with filtering support"""
    
    # Simulate network delay based on data size
    await asyncio.sleep(0.5)
    
    if endpoint == "test-connection":
        return {
            "success": True,
            "message": f"Connected to {device.ip_address}:{device.port}"
        }
    
    elif endpoint == "get-device-info":
        return {
            "success": True,
            "device_info": {
                "ip_address": device.ip_address,
                "port": device.port,
                "serial_number": "ZK2024123456",
                "model": "ZK-Teco",
                "firmware_version": "V6.60",
                "platform": "ARM",
                "user_count": 100,
                "attendance_count": 5000,
                "connected": True
            }
        }
    
    elif endpoint == "get-employees":
        employees = await generate_large_employee_dataset()
        
        # Apply filters
        filtered_employees = employees
        if filters:
            if filters.employee_ids:
                filtered_employees = [e for e in filtered_employees if e["pin"] in filters.employee_ids]
            if filters.departments:
                filtered_employees = [e for e in filtered_employees if e["department"] in filters.departments]
            
            # Apply pagination
            if filters.limit is not None:
                start = filters.offset or 0
                filtered_employees = filtered_employees[start:start + filters.limit]
        
        return {
            "success": True,
            "employees": filtered_employees,
            "total_count": len(employees),
            "filtered_count": len(filtered_employees)
        }
    
    elif endpoint == "get-attendance":
        records = await generate_large_attendance_dataset()
        
        # Apply filters
        filtered_records = records
        if filters:
            if filters.start_time:
                filtered_records = [r for r in filtered_records 
                                  if r["PunchTime"] >= filters.start_time]
            if filters.end_time:
                filtered_records = [r for r in filtered_records 
                                  if r["PunchTime"] <= filters.end_time]
            if filters.employee_ids:
                filtered_records = [r for r in filtered_records 
                                  if r["EmployeeID"] in filters.employee_ids]
            if filters.departments:
                filtered_records = [r for r in filtered_records 
                                  if r["Department"] in filters.departments]
            
            # Apply pagination
            if filters.limit is not None:
                start = filters.offset or 0
                filtered_records = filtered_records[start:start + filters.limit]
        
        return {
            "success": True,
            "records": filtered_records,
            "total_count": len(records),
            "filtered_count": len(filtered_records)
        }
    
    return {"success": False, "error": "Unknown endpoint"}

# Async operation handling
async def process_async_operation(operation_id: str, device: DeviceRequest, 
                                 endpoint: str, filters: Optional[FilterRequest] = None):
    """Process long-running operation asynchronously"""
    try:
        operation_status[operation_id] = {
            "status": OperationStatus.PROCESSING,
            "progress": 0,
            "message": "Starting operation"
        }
        
        # Simulate progress for large operations
        total_steps = 10
        for step in range(total_steps):
            await asyncio.sleep(1)  # Simulate work
            progress = int((step + 1) / total_steps * 100)
            
            operation_status[operation_id] = {
                "status": OperationStatus.PROCESSING,
                "progress": progress,
                "message": f"Processing step {step + 1}/{total_steps}"
            }
        
        # Get final result
        result = await simulate_zk_communication_enhanced(device, endpoint, filters)
        
        operation_status[operation_id] = {
            "status": OperationStatus.COMPLETED,
            "progress": 100,
            "message": "Operation completed successfully",
            "result": result
        }
        
    except Exception as e:
        operation_status[operation_id] = {
            "status": OperationStatus.FAILED,
            "progress": 0,
            "message": f"Operation failed: {str(e)}",
            "result": None
        }

# FastAPI endpoints
@app.post("/test-connection", response_model=TestConnectionResponse)
async def test_connection(device: DeviceRequest):
    """Test connection to a ZK device"""
    try:
        result = await simulate_zk_communication_enhanced(device, "test-connection")
        return TestConnectionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")

@app.post("/get-device-info", response_model=DeviceInfoResponse)
async def get_device_info(device: DeviceRequest):
    """Get detailed device information"""
    try:
        result = await simulate_zk_communication_enhanced(device, "get-device-info")
        return DeviceInfoResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get device info: {str(e)}")

@app.post("/get-employees", response_model=GetEmployeesResponse)
async def get_employees(device_data: DeviceDataWithFilters):
    """Get employees from ZK device with filtering support"""
    try:
        result = await simulate_zk_communication_enhanced(
            device_data, "get-employees", device_data.filters
        )
        return GetEmployeesResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get employees: {str(e)}")

@app.post("/get-attendance", response_model=GetAttendanceResponse)
async def get_attendance(device_data: DeviceDataWithFilters):
    """Get attendance records from ZK device with filtering support"""
    try:
        result = await simulate_zk_communication_enhanced(
            device_data, "get-attendance", device_data.filters
        )
        return GetAttendanceResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get attendance: {str(e)}")

@app.post("/async/get-employees", response_model=AsyncOperationResponse)
async def async_get_employees(
    device_data: DeviceDataWithFilters, 
    background_tasks: BackgroundTasks
):
    """Start async employee data retrieval"""
    operation_id = str(uuid.uuid4())
    
    operation_status[operation_id] = {
        "status": OperationStatus.PENDING,
        "progress": 0,
        "message": "Operation queued"
    }
    
    background_tasks.add_task(
        process_async_operation, 
        operation_id, device_data, "get-employees", device_data.filters
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
    """Start async attendance data retrieval"""
    operation_id = str(uuid.uuid4())
    
    operation_status[operation_id] = {
        "status": OperationStatus.PENDING,
        "progress": 0,
        "message": "Operation queued"
    }
    
    background_tasks.add_task(
        process_async_operation, 
        operation_id, device_data, "get-attendance", device_data.filters
    )
    
    return AsyncOperationResponse(
        operation_id=operation_id,
        status=OperationStatus.PENDING,
        progress=0,
        message="Operation started"
    )

@app.get("/async/status/{operation_id}", response_model=AsyncOperationResponse)
async def get_async_status(operation_id: str):
    """Check status of async operation"""
    if operation_id not in operation_status:
        raise HTTPException(status_code=404, detail="Operation not found")
    
    status_data = operation_status[operation_id]
    return AsyncOperationResponse(
        operation_id=operation_id,
        status=status_data["status"],
        progress=status_data["progress"],
        message=status_data["message"],
        result=status_data.get("result")
    )

@app.get("/")
async def root():
    return {
        "message": "Enhanced ZK Device API is running", 
        "version": "2.0.0",
        "endpoints": [
            "POST /test-connection",
            "POST /get-device-info", 
            "POST /get-employees",
            "POST /get-attendance",
            "POST /async/get-employees",
            "POST /async/get-attendance",
            "GET /async/status/{operation_id}"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=args.port)