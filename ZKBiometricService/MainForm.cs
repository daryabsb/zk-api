using System.Windows.Forms;
using ZKBiometricService.Core.Models;
using ZKBiometricService.Core.Services;
using ZKBiometricService.Data;
using Microsoft.EntityFrameworkCore;

namespace ZKBiometricService;

public partial class MainForm : Form
{
    private readonly AppDbContext _context;
    private readonly IZKDeviceService _deviceService;
    private Timer _refreshTimer;

    public MainForm(AppDbContext context, IZKDeviceService deviceService)
    {
        _context = context;
        _deviceService = deviceService;
        InitializeComponent();
        SetupForm();
    }

    private void InitializeComponent()
    {
        this.Text = "ZK Biometric Service";
        this.Size = new System.Drawing.Size(800, 600);
        this.StartPosition = FormStartPosition.CenterScreen;
        
        var devicesGrid = new DataGridView
        {
            Dock = DockStyle.Fill,
            ReadOnly = true,
            AutoGenerateColumns = false
        };
        
        devicesGrid.Columns.Add("Id", "ID");
        devicesGrid.Columns.Add("Name", "Name");
        devicesGrid.Columns.Add("IpAddress", "IP Address");
        devicesGrid.Columns.Add("Status", "Status");
        devicesGrid.Columns.Add("LastSync", "Last Sync");
        
        var syncButton = new Button
        {
            Text = "Sync All Devices",
            Dock = DockStyle.Bottom,
            Height = 40
        };
        syncButton.Click += async (s, e) => await SyncAllDevices();
        
        this.Controls.Add(devicesGrid);
        this.Controls.Add(syncButton);
        
        _refreshTimer = new Timer { Interval = 5000 };
        _refreshTimer.Tick += async (s, e) => await RefreshDevices();
        _refreshTimer.Start();
    }

    private void SetupForm()
    {
        this.FormClosing += (s, e) =>
        {
            e.Cancel = true;
            this.Hide();
        };
        
        Load += async (s, e) => await RefreshDevices();
    }

    private async Task RefreshDevices()
    {
        if (this.InvokeRequired)
        {
            this.Invoke(async () => await RefreshDevices());
            return;
        }

        try
        {
            var devices = await _context.Devices.ToListAsync();
            var grid = (DataGridView)this.Controls[0];
            
            grid.Rows.Clear();
            
            foreach (var device in devices)
            {
                var status = await _deviceService.GetDeviceStatusAsync(device);
                grid.Rows.Add(
                    device.Id,
                    device.Name,
                    device.IpAddress,
                    status.ToString(),
                    device.LastSync?.ToString("yyyy-MM-dd HH:mm:ss") ?? "Never"
                );
            }
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Error refreshing devices: {ex.Message}");
        }
    }

    private async Task SyncAllDevices()
    {
        try
        {
            var devices = await _context.Devices.Where(d => d.IsEnabled).ToListAsync();
            
            foreach (var device in devices)
            {
                var records = await _deviceService.GetAttendanceRecordsAsync(
                    device, DateTime.UtcNow.AddHours(-1), DateTime.UtcNow);
                
                foreach (var record in records)
                {
                    var existing = await _context.AttendanceRecords
                        .FirstOrDefaultAsync(a => a.DeviceId == record.DeviceId && 
                                                  a.EmployeeId == record.EmployeeId && 
                                                  a.RecordTime == record.RecordTime);
                    
                    if (existing == null)
                    {
                        _context.AttendanceRecords.Add(record);
                    }
                }
                
                device.LastSync = DateTime.UtcNow;
            }
            
            await _context.SaveChangesAsync();
            MessageBox.Show($"Synced {devices.Count} devices successfully");
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Error syncing devices: {ex.Message}");
        }
    }
}