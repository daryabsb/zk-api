# ZK Biometric Service

A comprehensive Windows service and REST API for integrating with ZK biometric attendance devices. This solution provides real-time attendance data synchronization, device management, and a user-friendly tray interface.

## Features

- **Device Management**: Add, edit, and manage multiple ZK biometric devices
- **Real-time Sync**: Automatic synchronization of attendance records
- **REST API**: Full RESTful API for integration with HR systems
- **Windows Service**: Runs as a background service with system tray control
- **PostgreSQL + TimescaleDB**: Optimized for time-series attendance data
- **Tray Interface**: System tray icon for easy control and monitoring

## Prerequisites

### Software Requirements
1. **.NET 8.0 SDK** - [Download here](https://dotnet.microsoft.com/download/dotnet/8.0)
2. **PostgreSQL 12+** with TimescaleDB extension
3. **Windows 10/11** or **Windows Server 2016+**

### Database Setup
1. Install PostgreSQL
2. Install TimescaleDB extension:
   ```sql
   CREATE EXTENSION IF NOT EXISTS timescaledb;
   ```
3. Create database:
   ```sql
   CREATE DATABASE zk_biometric_db;
   ```

## Installation

### 1. Clone and Build
```bash
git clone <repository-url>
cd zk-api
dotnet restore
dotnet build --configuration Release
```

### 2. Database Configuration
Update `appsettings.json` with your database connection string:
```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Host=localhost;Port=5432;Database=zk_biometric_db;Username=postgres;Password=your_password;"
  }
}
```

### 3. Database Migration
```bash
cd ZKBiometricService.API
dotnet ef database update
```

### 4. Install as Windows Service
```bash
# Build the service
cd ZKBiometricService
dotnet publish --configuration Release --output ./publish

# Install service
sc create "ZKBiometricService" binPath="C:\path\to\publish\ZKBiometricService.exe" start=auto
sc start ZKBiometricService
```

### 5. Run API Service
```bash
cd ZKBiometricService.API
dotnet run --urls="http://localhost:5000"
```

## API Endpoints

### Devices
- `GET /api/devices` - List all devices
- `POST /api/devices` - Add new device
- `PUT /api/devices/{id}` - Update device
- `DELETE /api/devices/{id}` - Remove device
- `POST /api/devices/{id}/test-connection` - Test device connection
- `POST /api/devices/{id}/sync-attendance` - Manual sync

### Attendance
- `GET /api/attendance` - Get attendance records
- `GET /api/attendance/{id}` - Get specific record
- `POST /api/attendance/report` - Generate reports
- `DELETE /api/attendance/{id}` - Delete record

## Device Configuration

Add your ZK devices through the API:

```json
{
  "name": "Main Entrance Device",
  "ipAddress": "192.168.1.100",
  "port": 4370,
  "serialNumber": "DEV123456",
  "model": "ZK-Teco",
  "isEnabled": true,
  "pollingInterval": 30
}
```

## Tray Interface

The system tray icon provides:
- **Show Window**: Open management interface
- **Sync Now**: Manual synchronization
- **Exit**: Stop the service

## Troubleshooting

### Common Issues
1. **Device Connection Failed**: Check IP address and network connectivity
2. **Database Errors**: Verify PostgreSQL is running and connection string is correct
3. **Service Won't Start**: Check .NET 8.0 is installed

### Logs
Logs are stored in:
- Windows Event Viewer for service errors
- Console output for API service

## Support

For ZK device protocol specifics and advanced configuration, refer to ZK device documentation.