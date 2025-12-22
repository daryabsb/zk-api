using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading.Tasks;
using ZKBiometricDLL.Models;
using ZKBiometricDLL.Services;

namespace ZKBiometricDLL
{
    public class ZKBiometricAPI : IDisposable
    {
        private readonly IZKDeviceService _deviceService;
        
        public ZKBiometricAPI()
        {
            _deviceService = new ZKDeviceService();
        }

        public ZKBiometricAPI(IZKDeviceService deviceService)
        {
            _deviceService = deviceService;
        }

        public string TestConnection(string deviceJson)
        {
            try
            {
                var device = JsonSerializer.Deserialize<DeviceInfo>(deviceJson);
                if (device == null)
                    return "{\"success\": false, \"error\": \"Invalid device JSON\"}";

                var result = _deviceService.TestConnectionAsync(device).Result;
                return $"{{\"success\": true, \"connected\": {result.ToString().ToLower()}}}";
            }
            catch (Exception ex)
            {
                return $"{{\"success\": false, \"error\": \"{EscapeJsonString(ex.Message)}\"}}";
            }
        }

        public string GetAttendanceRecords(string deviceJson, string startTime, string endTime)
        {
            try
            {
                var device = JsonSerializer.Deserialize<DeviceInfo>(deviceJson);
                if (device == null)
                    return "{\"success\": false, \"error\": \"Invalid device JSON\"}";

                var start = DateTime.Parse(startTime);
                var end = DateTime.Parse(endTime);
                var records = _deviceService.GetAttendanceRecordsAsync(device, start, end).Result;
                var json = JsonSerializer.Serialize(records);
                return $"{{\"success\": true, \"records\": {json}}}";
            }
            catch (Exception ex)
            {
                return $"{{\"success\": false, \"error\": \"{EscapeJsonString(ex.Message)}\"}}";
            }
        }

        public string GetEmployees(string deviceJson)
        {
            try
            {
                var device = JsonSerializer.Deserialize<DeviceInfo>(deviceJson);
                if (device == null)
                    return "{\"success\": false, \"error\": \"Invalid device JSON\"}";

                var employees = _deviceService.GetEmployeesAsync(device).Result;
                var json = JsonSerializer.Serialize(employees);
                return $"{{\"success\": true, \"employees\": {json}}}";
            }
            catch (Exception ex)
            {
                return $"{{\"success\": false, \"error\": \"{EscapeJsonString(ex.Message)}\"}}";
            }
        }

        public string GetDeviceStatus(string deviceJson)
        {
            try
            {
                var device = JsonSerializer.Deserialize<DeviceInfo>(deviceJson);
                if (device == null)
                    return "{\"success\": false, \"error\": \"Invalid device JSON\"}";

                var status = _deviceService.GetDeviceStatusAsync(device).Result;
                return $"{{\"success\": true, \"status\": \"{status}\"}}";
            }
            catch (Exception ex)
            {
                return $"{{\"success\": false, \"error\": \"{EscapeJsonString(ex.Message)}\"}}";
            }
        }

        public string ConnectDevice(string deviceJson)
        {
            try
            {
                var device = JsonSerializer.Deserialize<DeviceInfo>(deviceJson);
                if (device == null)
                    return "{\"success\": false, \"error\": \"Invalid device JSON\"}";

                var result = _deviceService.ConnectAsync(device).Result;
                return $"{{\"success\": true, \"connected\": {result.ToString().ToLower()}}}";
            }
            catch (Exception ex)
            {
                return $"{{\"success\": false, \"error\": \"{EscapeJsonString(ex.Message)}\"}}";
            }
        }

        public string DisconnectDevice(string deviceJson)
        {
            try
            {
                var device = JsonSerializer.Deserialize<DeviceInfo>(deviceJson);
                if (device == null)
                    return "{\"success\": false, \"error\": \"Invalid device JSON\"}";

                _deviceService.DisconnectAsync(device).Wait();
                return "{\"success\": true}";
            }
            catch (Exception ex)
            {
                return $"{{\"success\": false, \"error\": \"{EscapeJsonString(ex.Message)}\"}}";
            }
        }

        public string GetDeviceInfo()
        {
            try
            {
                var device = new DeviceInfo
                {
                    Id = 1,
                    Name = "Sample Device",
                    IpAddress = "192.168.1.100",
                    Port = 4370,
                    SerialNumber = "ZK123456",
                    Model = "ZK-Teco",
                    IsEnabled = true
                };

                var json = JsonSerializer.Serialize(device);
                return $"{{\"success\": true, \"device\": {json}}}";
            }
            catch (Exception ex)
            {
                return $"{{\"success\": false, \"error\": \"{EscapeJsonString(ex.Message)}\"}}";
            }
        }

        private string EscapeJsonString(string input)
        {
            return input.Replace("\\", "\\\\").Replace("\"", "\\\"");
        }

        public void Dispose()
        {
            (_deviceService as IDisposable)?.Dispose();
        }
    }
}