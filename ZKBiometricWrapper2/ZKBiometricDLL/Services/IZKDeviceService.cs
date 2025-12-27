using System.Collections.Generic;
using System.Threading.Tasks;
using ZKBiometricDLL.Models;

namespace ZKBiometricDLL.Services
{
    public interface IZKDeviceService
    {
        Task<bool> ConnectAsync(DeviceInfo device);
        Task DisconnectAsync(DeviceInfo device);
        Task<List<AttendanceRecord>> GetAttendanceRecordsAsync(DeviceInfo device, System.DateTime startTime, System.DateTime endTime);
        Task<List<EmployeeInfo>> GetEmployeesAsync(DeviceInfo device);
        Task<string> GetDeviceStatusAsync(DeviceInfo device);
        Task<bool> TestConnectionAsync(DeviceInfo device);
    }
}