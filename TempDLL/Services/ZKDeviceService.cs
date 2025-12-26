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
        public string? LastError { get; private set; }

        public ZKDeviceService()
        {
        }

        public async Task<bool> ConnectAsync(DeviceInfo device)
        {
            try
            {
                LastError = null;
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
                LastError = "Failed to open TCP connection to device";
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
            {
                if (LastError == null)
                    LastError = "Device not reachable over TCP";
                return new List<AttendanceRecord>();
            }

            try
            {
                var records = await GetAttendanceRecordsFromDeviceAsync(device, startTime, endTime);
                return records;
            }
            catch
            {
                if (LastError == null)
                    LastError = "Unexpected error while reading attendance records";
                return new List<AttendanceRecord>();
            }
        }

        public async Task<List<EmployeeInfo>> GetEmployeesAsync(DeviceInfo device)
        {
            if (!await EnsureConnected(device))
            {
                if (LastError == null)
                    LastError = "Device not reachable over TCP";
                return new List<EmployeeInfo>();
            }

            try
            {
                var employees = await GetEmployeesFromDeviceAsync(device);
                return employees;
            }
            catch
            {
                if (LastError == null)
                    LastError = "Unexpected error while reading employees";
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

        private Task<List<AttendanceRecord>> GetAttendanceRecordsFromDeviceAsync(DeviceInfo device, DateTime startTime, DateTime endTime)
        {
            return Task.Run(() =>
            {
                var records = new List<AttendanceRecord>();

                try
                {
                    LastError = null;
                    var comType = GetZkComType();
                    if (comType == null)
                    {
                        LastError = "ZKTeco SDK (zkemkeeper) is not installed or not registered on this machine";
                        return records;
                    }

                    dynamic zk = Activator.CreateInstance(comType);
                    bool connected = zk.Connect_Net(device.IpAddress, device.Port);
                    if (!connected)
                    {
                        LastError = "ZKTeco SDK Connect_Net failed for device";
                        return records;
                    }

                    try
                    {
                        int machineNumber = 1;
                        bool readOk = zk.ReadGeneralLogData(machineNumber);
                        if (!readOk)
                        {
                            LastError = "ZKTeco SDK ReadGeneralLogData returned false (no logs or command failed)";
                            return records;
                        }

                        string dwEnrollNumber = string.Empty;
                        int dwVerifyMode = 0;
                        int dwInOutMode = 0;
                        int dwYear = 0;
                        int dwMonth = 0;
                        int dwDay = 0;
                        int dwHour = 0;
                        int dwMinute = 0;
                        int dwSecond = 0;
                        int dwWorkCode = 0;

                        while (true)
                        {
                            bool hasData = zk.SSR_GetGeneralLogData(
                                machineNumber,
                                out dwEnrollNumber,
                                out dwVerifyMode,
                                out dwInOutMode,
                                out dwYear,
                                out dwMonth,
                                out dwDay,
                                out dwHour,
                                out dwMinute,
                                out dwSecond,
                                ref dwWorkCode);

                            if (!hasData)
                                break;

                            var recordTime = new DateTime(dwYear, dwMonth, dwDay, dwHour, dwMinute, dwSecond);
                            if (recordTime < startTime || recordTime > endTime)
                                continue;

                            var record = new AttendanceRecord
                            {
                                DeviceId = device.Id,
                                EmployeeId = dwEnrollNumber,
                                RecordTime = recordTime,
                                Type = dwInOutMode == 0 ? "CheckIn" : "CheckOut",
                                VerifyMode = dwVerifyMode,
                                WorkCode = dwWorkCode
                            };

                            records.Add(record);
                        }
                    }
                    finally
                    {
                        zk.Disconnect();
                    }
                }
                catch
                {
                    if (LastError == null)
                        LastError = "Exception while talking to device via ZKTeco SDK";
                    return records;
                }

                return records;
            });
        }

        private Task<List<EmployeeInfo>> GetEmployeesFromDeviceAsync(DeviceInfo device)
        {
            return Task.Run(() =>
            {
                var employees = new List<EmployeeInfo>();

                try
                {
                    LastError = null;
                    var comType = GetZkComType();
                    if (comType == null)
                    {
                        LastError = "ZKTeco SDK (zkemkeeper) is not installed or not registered on this machine";
                        return employees;
                    }

                    dynamic zk = Activator.CreateInstance(comType);
                    bool connected = zk.Connect_Net(device.IpAddress, device.Port);
                    if (!connected)
                    {
                        LastError = "ZKTeco SDK Connect_Net failed for device";
                        return employees;
                    }

                    try
                    {
                        int machineNumber = 1;
                        zk.ReadAllUserID(machineNumber);

                        string dwEnrollNumber = string.Empty;
                        string name = string.Empty;
                        string password = string.Empty;
                        int privilege = 0;
                        bool enabled = false;

                        while (true)
                        {
                            bool hasUser = zk.SSR_GetAllUserInfo(
                                machineNumber,
                                out dwEnrollNumber,
                                out name,
                                out password,
                                out privilege,
                                out enabled);

                            if (!hasUser)
                                break;

                            if (!enabled)
                                continue;

                            var employee = new EmployeeInfo
                            {
                                EmployeeId = dwEnrollNumber,
                                Name = name,
                                Department = string.Empty,
                                Position = string.Empty,
                                IsActive = true
                            };

                            employees.Add(employee);
                        }
                    }
                    finally
                    {
                        zk.Disconnect();
                    }
                }
                catch
                {
                    return employees;
                }

                return employees;
            });
        }

        public void Dispose()
        {
            lock (_lock)
            {
                _networkStream?.Dispose();
                _tcpClient?.Dispose();
            }
        }

        private Type? GetZkComType()
        {
            return Type.GetTypeFromProgID("zkemkeeper.CZKEM")
                   ?? Type.GetTypeFromProgID("zkemkeeper.ZKEM");
        }
    }
}
