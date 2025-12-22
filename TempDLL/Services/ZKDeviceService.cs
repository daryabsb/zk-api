using System;
using System.Collections.Generic;
using System.IO.Ports;
using System.Net.Sockets;
using System.Threading.Tasks;
using ZKBiometricDLL.Models;

namespace ZKBiometricDLL.Services
{
    public class ZKDeviceService : IZKDeviceService, IDisposable
    {
        private TcpClient? _tcpClient;
        private NetworkStream? _networkStream;
        private readonly object _lock = new object();

        public ZKDeviceService()
        {
        }

        public async Task<bool> ConnectAsync(DeviceInfo device)
        {
            try
            {
                lock (_lock)
                {
                    _tcpClient?.Dispose();
                    _tcpClient = new TcpClient();
                }

                await _tcpClient.ConnectAsync(device.IpAddress, device.Port);
                _networkStream = _tcpClient.GetStream();
                
                return await AuthenticateAsync(device);
            }
            catch (Exception)
            {
                return false;
            }
        }

        public Task DisconnectAsync(DeviceInfo device)
        {
            lock (_lock)
            {
                _networkStream?.Dispose();
                _tcpClient?.Dispose();
                _networkStream = null;
                _tcpClient = null;
            }
            
            return Task.CompletedTask;
        }

        public async Task<List<AttendanceRecord>> GetAttendanceRecordsAsync(DeviceInfo device, DateTime startTime, DateTime endTime)
        {
            if (!await EnsureConnected(device))
                return new List<AttendanceRecord>();

            try
            {
                // Simulate fetching records - in real implementation, this would communicate with the device
                await Task.Delay(1000);
                
                var records = new List<AttendanceRecord>
                {
                    new AttendanceRecord
                    {
                        DeviceId = device.Id,
                        EmployeeId = "1001",
                        RecordTime = DateTime.Now.AddMinutes(-30),
                        Type = "CheckIn",
                        VerifyMode = 1,
                        WorkCode = 0
                    },
                    new AttendanceRecord
                    {
                        DeviceId = device.Id,
                        EmployeeId = "1002", 
                        RecordTime = DateTime.Now.AddMinutes(-25),
                        Type = "CheckIn",
                        VerifyMode = 1,
                        WorkCode = 0
                    }
                };
                
                return records;
            }
            catch (Exception)
            {
                return new List<AttendanceRecord>();
            }
        }

        public async Task<List<EmployeeInfo>> GetEmployeesAsync(DeviceInfo device)
        {
            if (!await EnsureConnected(device))
                return new List<EmployeeInfo>();

            try
            {
                await Task.Delay(500);
                
                var employees = new List<EmployeeInfo>
                {
                    new EmployeeInfo
                    {
                        EmployeeId = "1001",
                        Name = "John Doe",
                        Department = "IT",
                        Position = "Developer"
                    },
                    new EmployeeInfo
                    {
                        EmployeeId = "1002",
                        Name = "Jane Smith", 
                        Department = "HR",
                        Position = "Manager"
                    }
                };
                
                return employees;
            }
            catch (Exception)
            {
                return new List<EmployeeInfo>();
            }
        }

        public async Task<string> GetDeviceStatusAsync(DeviceInfo device)
        {
            try
            {
                var isConnected = await TestConnectionAsync(device);
                return isConnected ? "Connected" : "Disconnected";
            }
            catch
            {
                return "Error";
            }
        }

        public async Task<bool> TestConnectionAsync(DeviceInfo device)
        {
            try
            {
                using var testClient = new TcpClient();
                await testClient.ConnectAsync(device.IpAddress, device.Port);
                testClient.Close();
                return true;
            }
            catch
            {
                return false;
            }
        }

        private async Task<bool> EnsureConnected(DeviceInfo device)
        {
            lock (_lock)
            {
                if (_tcpClient?.Connected == true && _networkStream != null)
                    return true;
            }

            return await ConnectAsync(device);
        }

        private async Task<bool> AuthenticateAsync(DeviceInfo device)
        {
            try
            {
                await Task.Delay(100);
                return true;
            }
            catch
            {
                return false;
            }
        }

        public void Dispose()
        {
            lock (_lock)
            {
                _networkStream?.Dispose();
                _tcpClient?.Dispose();
            }
        }
    }
}