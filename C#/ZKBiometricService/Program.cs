using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using System.Windows.Forms;
using ZKBiometricService.Core.Services;
using ZKBiometricService.Data;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;

namespace ZKBiometricService;

static class Program
{
    private static IHost? _host;
    private static NotifyIcon? _trayIcon;

    [STAThread]
    static void Main()
    {
        ApplicationConfiguration.Initialize();

        _host = CreateHostBuilder().Build();
        
        SetupTrayIcon();
        
        Application.Run();
        
        _trayIcon?.Dispose();
        _host?.Dispose();
    }

    private static IHostBuilder CreateHostBuilder()
    {
        return Host.CreateDefaultBuilder()
            .UseWindowsService()
            .ConfigureServices((context, services) =>
            {
                services.AddDbContext<AppDbContext>(options =>
                    options.UseNpgsql(context.Configuration.GetConnectionString("DefaultConnection")));

                services.AddScoped<IZKDeviceService, ZKDeviceService>();
                
                services.AddHostedService<DeviceSyncService>();
                
                services.AddSingleton<MainForm>();
            })
            .ConfigureLogging(logging =>
            {
                logging.AddConsole();
                logging.AddDebug();
            });
    }

    private static void SetupTrayIcon()
    {
        _trayIcon = new NotifyIcon
        {
            Icon = System.Drawing.SystemIcons.Application,
            Text = "ZK Biometric Service",
            Visible = true
        };

        var contextMenu = new ContextMenuStrip();
        
        var showWindowItem = new ToolStripMenuItem("Show Window");
        showWindowItem.Click += (s, e) => ShowMainWindow();
        contextMenu.Items.Add(showWindowItem);
        
        var syncNowItem = new ToolStripMenuItem("Sync Now");
        syncNowItem.Click += async (s, e) => await SyncAllDevices();
        contextMenu.Items.Add(syncNowItem);
        
        contextMenu.Items.Add(new ToolStripSeparator());
        
        var exitItem = new ToolStripMenuItem("Exit");
        exitItem.Click += (s, e) => Application.Exit();
        contextMenu.Items.Add(exitItem);

        _trayIcon.ContextMenuStrip = contextMenu;
        _trayIcon.DoubleClick += (s, e) => ShowMainWindow();
    }

    private static void ShowMainWindow()
    {
        var mainForm = _host?.Services.GetRequiredService<MainForm>();
        if (mainForm != null && !mainForm.Visible)
        {
            mainForm.Show();
        }
    }

    private static async Task SyncAllDevices()
    {
        using var scope = _host?.Services.CreateScope();
        var deviceService = scope?.ServiceProvider.GetRequiredService<IZKDeviceService>();
        var dbContext = scope?.ServiceProvider.GetRequiredService<AppDbContext>();
        
        if (deviceService != null && dbContext != null)
        {
            var devices = await dbContext.Devices.Where(d => d.IsEnabled).ToListAsync();
            foreach (var device in devices)
            {
                await deviceService.GetAttendanceRecordsAsync(device, DateTime.UtcNow.AddHours(-1), DateTime.UtcNow);
            }
        }
    }
}