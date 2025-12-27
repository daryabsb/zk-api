using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using ZKBiometricService.Core.Models;
using ZKBiometricService.Data;
using Microsoft.EntityFrameworkCore;

namespace ZKBiometricService.Core.Services;

public class DeviceSyncService : BackgroundService
{
    private readonly ILogger<DeviceSyncService> _logger;
    private readonly IServiceProvider _serviceProvider;
    private Timer? _syncTimer;

    public DeviceSyncService(ILogger<DeviceSyncService> logger, IServiceProvider serviceProvider)
    {
        _logger = logger;
        _serviceProvider = serviceProvider;
    }

    protected override Task ExecuteAsync(CancellationToken stoppingToken)
    {
        _logger.LogInformation("Device Sync Service is starting.");
        
        _syncTimer = new Timer(async _ => await SyncDevicesAsync(), null, 
            TimeSpan.Zero, TimeSpan.FromMinutes(5));
        
        return Task.CompletedTask;
    }

    private async Task SyncDevicesAsync()
    {
        try
        {
            using var scope = _serviceProvider.CreateScope();
            var dbContext = scope.ServiceProvider.GetRequiredService<AppDbContext>();
            var deviceService = scope.ServiceProvider.GetRequiredService<IZKDeviceService>();

            var devices = await dbContext.Devices
                .Where(d => d.IsEnabled)
                .ToListAsync();

            _logger.LogInformation("Starting sync for {DeviceCount} devices", devices.Count);

            foreach (var device in devices)
            {
                try
                {
                    var lastSync = device.LastSync ?? DateTime.UtcNow.AddHours(-1);
                    var records = await deviceService.GetAttendanceRecordsAsync(
                        device, lastSync, DateTime.UtcNow);

                    _logger.LogInformation("Found {RecordCount} records from device {DeviceName}", 
                        records.Count, device.Name);

                    foreach (var record in records)
                    {
                        var existing = await dbContext.AttendanceRecords
                            .FirstOrDefaultAsync(a => a.DeviceId == record.DeviceId && 
                                                      a.EmployeeId == record.EmployeeId && 
                                                      a.RecordTime == record.RecordTime);

                        if (existing == null)
                        {
                            dbContext.AttendanceRecords.Add(record);
                        }
                    }

                    device.LastSync = DateTime.UtcNow;
                    await dbContext.SaveChangesAsync();

                    _logger.LogInformation("Successfully synced device {DeviceName}", device.Name);
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error syncing device {DeviceName}", device.Name);
                }
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error in device sync process");
        }
    }

    public override async Task StopAsync(CancellationToken cancellationToken)
    {
        _logger.LogInformation("Device Sync Service is stopping.");
        
        _syncTimer?.Change(Timeout.Infinite, 0);
        await base.StopAsync(cancellationToken);
    }

    public override void Dispose()
    {
        _syncTimer?.Dispose();
        base.Dispose();
    }
}