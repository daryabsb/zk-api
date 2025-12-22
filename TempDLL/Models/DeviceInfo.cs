using System;

namespace ZKBiometricDLL.Models
{
    public class DeviceInfo
    {
        public int Id { get; set; }
        public string Name { get; set; } = string.Empty;
        public string IpAddress { get; set; } = string.Empty;
        public int Port { get; set; } = 4370;
        public string SerialNumber { get; set; } = string.Empty;
        public string Model { get; set; } = string.Empty;
        public bool IsEnabled { get; set; } = true;
        public int PollingInterval { get; set; } = 30;
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
        public DateTime? LastSync { get; set; }
        public string Status { get; set; } = "Disconnected";
    }

    public class AttendanceRecord
    {
        public long Id { get; set; }
        public int DeviceId { get; set; }
        public string EmployeeId { get; set; } = string.Empty;
        public DateTime RecordTime { get; set; }
        public string Type { get; set; } = "Unknown";
        public int VerifyMode { get; set; }
        public int WorkCode { get; set; }
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
        public bool IsSynced { get; set; } = false;
    }

    public class EmployeeInfo
    {
        public int Id { get; set; }
        public string EmployeeId { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public string Department { get; set; } = string.Empty;
        public string Position { get; set; } = string.Empty;
        public bool IsActive { get; set; } = true;
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    }
}