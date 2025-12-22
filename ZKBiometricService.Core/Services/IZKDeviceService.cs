using ZKBiometricService.Core.Models;

namespace ZKBiometricService.Core.Services;

public interface IZKDeviceService
{
    Task<bool> ConnectAsync(Device device);
    Task DisconnectAsync(Device device);
    Task<List<AttendanceRecord>> GetAttendanceRecordsAsync(Device device, DateTime startTime, DateTime endTime);
    Task<List<Employee>> GetEmployeesAsync(Device device);
    Task<DeviceStatus> GetDeviceStatusAsync(Device device);
    Task<bool> TestConnectionAsync(Device device);
}