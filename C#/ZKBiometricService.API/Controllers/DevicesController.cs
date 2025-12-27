using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using ZKBiometricService.Core.Models;
using ZKBiometricService.Core.Services;
using ZKBiometricService.Data;

namespace ZKBiometricService.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class DevicesController : ControllerBase
{
    private readonly AppDbContext _context;
    private readonly IZKDeviceService _deviceService;
    private readonly ILogger<DevicesController> _logger;

    public DevicesController(AppDbContext context, IZKDeviceService deviceService, ILogger<DevicesController> logger)
    {
        _context = context;
        _deviceService = deviceService;
        _logger = logger;
    }

    [HttpGet]
    public async Task<ActionResult<IEnumerable<Device>>> GetDevices()
    {
        var devices = await _context.Devices.ToListAsync();
        return Ok(devices);
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<Device>> GetDevice(int id)
    {
        var device = await _context.Devices.FindAsync(id);
        if (device == null)
        {
            return NotFound();
        }
        return Ok(device);
    }

    [HttpPost]
    public async Task<ActionResult<Device>> CreateDevice(Device device)
    {
        if (!ModelState.IsValid)
        {
            return BadRequest(ModelState);
        }

        device.CreatedAt = DateTime.UtcNow;
        _context.Devices.Add(device);
        await _context.SaveChangesAsync();

        return CreatedAtAction(nameof(GetDevice), new { id = device.Id }, device);
    }

    [HttpPut("{id}")]
    public async Task<IActionResult> UpdateDevice(int id, Device device)
    {
        if (id != device.Id)
        {
            return BadRequest();
        }

        _context.Entry(device).State = EntityState.Modified;

        try
        {
            await _context.SaveChangesAsync();
        }
        catch (DbUpdateConcurrencyException)
        {
            if (!DeviceExists(id))
            {
                return NotFound();
            }
            throw;
        }

        return NoContent();
    }

    [HttpDelete("{id}")]
    public async Task<IActionResult> DeleteDevice(int id)
    {
        var device = await _context.Devices.FindAsync(id);
        if (device == null)
        {
            return NotFound();
        }

        _context.Devices.Remove(device);
        await _context.SaveChangesAsync();

        return NoContent();
    }

    [HttpPost("{id}/test-connection")]
    public async Task<ActionResult<bool>> TestConnection(int id)
    {
        var device = await _context.Devices.FindAsync(id);
        if (device == null)
        {
            return NotFound();
        }

        var isConnected = await _deviceService.TestConnectionAsync(device);
        return Ok(isConnected);
    }

    [HttpPost("{id}/sync-attendance")]
    public async Task<ActionResult> SyncAttendance(int id, [FromQuery] DateTime? startTime = null, [FromQuery] DateTime? endTime = null)
    {
        var device = await _context.Devices.FindAsync(id);
        if (device == null)
        {
            return NotFound();
        }

        startTime ??= DateTime.UtcNow.AddDays(-1);
        endTime ??= DateTime.UtcNow;

        try
        {
            var records = await _deviceService.GetAttendanceRecordsAsync(device, startTime.Value, endTime.Value);
            
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
            await _context.SaveChangesAsync();

            return Ok(new { SyncedRecords = records.Count });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to sync attendance for device {DeviceId}", id);
            return StatusCode(500, "Failed to sync attendance records");
        }
    }

    private bool DeviceExists(int id)
    {
        return _context.Devices.Any(e => e.Id == id);
    }
}