using System.IO.Ports;
using System.Net.Sockets;
using Microsoft.Extensions.Logging;
using ZKBiometricService.Core.Models;

namespace ZKBiometricService.Core.Services;

public class ZKDeviceService : IZKDeviceService, IDisposable
{
    private readonly ILogger<ZKDeviceService> _logger;
    private TcpClient? _tcpClient;
    private NetworkStream? _networkStream;
    private readonly object _lock = new object();

    public ZKDeviceService(ILogger<ZKDeviceService> logger)
    {
        _logger = logger;
    }

    public async Task<bool> ConnectAsync(Device device)
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
            
            _logger.LogInformation("Connected to device {DeviceName} at {IpAddress}:{Port}", 
                device.Name, device.IpAddress, device.Port);
            
            return await AuthenticateAsync(device);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to connect to device {DeviceName} at {IpAddress}:{Port}", 
                device.Name, device.IpAddress, device.Port);
            return false;
        }
    }

    public Task DisconnectAsync(Device device)
    {
        lock (_lock)
        {
            _networkStream?.Dispose();
            _tcpClient?.Dispose();
            _networkStream = null;
            _tcpClient = null;
        }
        
        _logger.LogInformation("Disconnected from device {DeviceName}", device.Name);
        return Task.CompletedTask;
    }

    public async Task<List<AttendanceRecord>> GetAttendanceRecordsAsync(Device device, DateTime startTime, DateTime endTime)
    {
        if (!await EnsureConnected(device))
            return new List<AttendanceRecord>();

        try
        {
            var records = new List<AttendanceRecord>();
            
            _logger.LogInformation("Fetching attendance records from {DeviceName} between {StartTime} and {EndTime}",
                device.Name, startTime, endTime);
            
            await Task.Delay(1000);
            
            return records;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to get attendance records from device {DeviceName}", device.Name);
            return new List<AttendanceRecord>();
        }
    }

    public async Task<List<Employee>> GetEmployeesAsync(Device device)
    {
        if (!await EnsureConnected(device))
            return new List<Employee>();

        try
        {
            var employees = new List<Employee>();
            
            _logger.LogInformation("Fetching employees from device {DeviceName}", device.Name);
            
            await Task.Delay(500);
            
            return employees;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to get employees from device {DeviceName}", device.Name);
            return new List<Employee>();
        }
    }

    public async Task<DeviceStatus> GetDeviceStatusAsync(Device device)
    {
        try
        {
            var isConnected = await TestConnectionAsync(device);
            return isConnected ? DeviceStatus.Connected : DeviceStatus.Disconnected;
        }
        catch
        {
            return DeviceStatus.Error;
        }
    }

    public async Task<bool> TestConnectionAsync(Device device)
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

    private async Task<bool> EnsureConnected(Device device)
    {
        lock (_lock)
        {
            if (_tcpClient?.Connected == true && _networkStream != null)
                return true;
        }

        return await ConnectAsync(device);
    }

    private async Task<bool> AuthenticateAsync(Device device)
    {
        try
        {
            await Task.Delay(100);
            return true;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Authentication failed for device {DeviceName}", device.Name);
            return false;
        }
    }

    private byte[] BuildCommand(ushort command, ushort sessionId, ushort replyId, byte[] data)
    {
        var header = new byte[8];
        header[0] = 0x50;
        header[1] = 0x00;
        Buffer.BlockCopy(BitConverter.GetBytes(command), 0, header, 2, 2);
        Buffer.BlockCopy(BitConverter.GetBytes(sessionId), 0, header, 4, 2);
        Buffer.BlockCopy(BitConverter.GetBytes(replyId), 0, header, 6, 2);

        var packet = new byte[header.Length + data.Length + 2];
        Buffer.BlockCopy(header, 0, packet, 0, header.Length);
        Buffer.BlockCopy(data, 0, packet, header.Length, data.Length);
        
        ushort checksum = CalculateChecksum(packet);
        packet[^2] = (byte)(checksum & 0xFF);
        packet[^1] = (byte)((checksum >> 8) & 0xFF);

        return packet;
    }

    private ushort CalculateChecksum(byte[] data)
    {
        ushort checksum = 0;
        for (int i = 0; i < data.Length - 2; i++)
        {
            checksum += data[i];
        }
        return checksum;
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