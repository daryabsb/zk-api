#!/usr/bin/env python3
"""
FastAPI service for ZK device communication
This avoids the Python.NET compatibility issues
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import asyncio
import aiohttp
import json

app = FastAPI(title="ZK Device API", version="1.0.0")

class DeviceRequest(BaseModel):
    ip_address: str
    port: int = 4370
    serial_number: str = ""
    model: str = ""

class TestConnectionResponse(BaseModel):
    success: bool
    message: str

class Employee(BaseModel):
    pin: str
    name: str
    card_number: str = ""
    privilege: int = 0

class GetEmployeesResponse(BaseModel):
    success: bool
    employees: List[Employee]
    error: str = ""

# Simulate ZK device communication (replace with actual ZK library)
async def simulate_zk_communication(device: DeviceRequest, endpoint: str):
    """Simulate communication with ZK device"""
    
    # Simulate network delay
    await asyncio.sleep(1)
    
    if endpoint == "test-connection":
        # Simulate connection test
        return {
            "success": True,
            "message": f"Connected to {device.ip_address}:{device.port}"
        }
    
    elif endpoint == "get-employees":
        # Simulate getting employees
        return {
            "success": True,
            "employees": [
                {"pin": "001", "name": "John Doe", "card_number": "123456", "privilege": 0},
                {"pin": "002", "name": "Jane Smith", "card_number": "654321", "privilege": 0},
                {"pin": "003", "name": "Bob Johnson", "card_number": "987654", "privilege": 0}
            ],
            "error": ""
        }
    
    return {"success": False, "error": "Unknown endpoint"}

@app.post("/test-connection", response_model=TestConnectionResponse)
async def test_connection(device: DeviceRequest):
    """Test connection to a ZK device"""
    try:
        result = await simulate_zk_communication(device, "test-connection")
        return TestConnectionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")

@app.post("/get-employees", response_model=GetEmployeesResponse)
async def get_employees(device: DeviceRequest):
    """Get employees from a ZK device"""
    try:
        result = await simulate_zk_communication(device, "get-employees")
        return GetEmployeesResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get employees: {str(e)}")

@app.get("/")
async def root():
    return {"message": "ZK Device API is running", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)