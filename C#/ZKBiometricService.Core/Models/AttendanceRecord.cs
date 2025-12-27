namespace ZKBiometricService.Core.Models;

public class AttendanceRecord
{
    public long Id { get; set; }
    public int DeviceId { get; set; }
    public string EmployeeId { get; set; } = string.Empty;
    public DateTime RecordTime { get; set; }
    public AttendanceType Type { get; set; }
    public int VerifyMode { get; set; }
    public int WorkCode { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public bool IsSynced { get; set; } = false;
    
    public Device Device { get; set; } = null!;
    public Employee Employee { get; set; } = null!;
}

public enum AttendanceType
{
    CheckIn,
    CheckOut,
    BreakStart,
    BreakEnd,
    Unknown
}