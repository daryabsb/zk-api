namespace ZKBiometricService.Core.Models;

public class Device
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
    public DeviceStatus Status { get; set; } = DeviceStatus.Disconnected;
}

public enum DeviceStatus
{
    Disconnected,
    Connected,
    Syncing,
    Error
}