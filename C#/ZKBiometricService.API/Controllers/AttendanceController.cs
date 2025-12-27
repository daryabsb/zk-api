using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using ZKBiometricService.Core.Models;
using ZKBiometricService.Data;

namespace ZKBiometricService.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AttendanceController : ControllerBase
{
    private readonly AppDbContext _context;
    private readonly ILogger<AttendanceController> _logger;

    public AttendanceController(AppDbContext context, ILogger<AttendanceController> logger)
    {
        _context = context;
        _logger = logger;
    }

    [HttpGet]
    public async Task<ActionResult<IEnumerable<AttendanceRecord>>> GetAttendanceRecords(
        [FromQuery] string? employeeId = null,
        [FromQuery] int? deviceId = null,
        [FromQuery] DateTime? startDate = null,
        [FromQuery] DateTime? endDate = null,
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 50)
    {
        var query = _context.AttendanceRecords
            .Include(a => a.Device)
            .Include(a => a.Employee)
            .AsQueryable();

        if (!string.IsNullOrEmpty(employeeId))
        {
            query = query.Where(a => a.EmployeeId == employeeId);
        }

        if (deviceId.HasValue)
        {
            query = query.Where(a => a.DeviceId == deviceId.Value);
        }

        if (startDate.HasValue)
        {
            query = query.Where(a => a.RecordTime >= startDate.Value);
        }

        if (endDate.HasValue)
        {
            query = query.Where(a => a.RecordTime <= endDate.Value);
        }

        var totalCount = await query.CountAsync();
        var records = await query
            .OrderByDescending(a => a.RecordTime)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync();

        return Ok(new
        {
            TotalCount = totalCount,
            Page = page,
            PageSize = pageSize,
            Records = records
        });
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<AttendanceRecord>> GetAttendanceRecord(long id)
    {
        var record = await _context.AttendanceRecords
            .Include(a => a.Device)
            .Include(a => a.Employee)
            .FirstOrDefaultAsync(a => a.Id == id);

        if (record == null)
        {
            return NotFound();
        }

        return Ok(record);
    }

    [HttpPost("report")]
    public async Task<ActionResult> GenerateAttendanceReport(
        [FromQuery] DateTime startDate,
        [FromQuery] DateTime endDate,
        [FromQuery] string? department = null)
    {
        var query = _context.AttendanceRecords
            .Include(a => a.Employee)
            .Where(a => a.RecordTime >= startDate && a.RecordTime <= endDate);

        if (!string.IsNullOrEmpty(department))
        {
            query = query.Where(a => a.Employee.Department == department);
        }

        var records = await query.ToListAsync();
        
        var report = records
            .GroupBy(a => new { a.EmployeeId, a.Employee.Name, a.RecordTime.Date })
            .Select(g => new
            {
                EmployeeId = g.Key.EmployeeId,
                EmployeeName = g.Key.Name,
                Date = g.Key.Date,
                FirstCheckIn = g.Min(r => r.RecordTime),
                LastCheckOut = g.Max(r => r.RecordTime),
                TotalRecords = g.Count()
            })
            .ToList();

        return Ok(report);
    }

    [HttpDelete("{id}")]
    public async Task<IActionResult> DeleteAttendanceRecord(long id)
    {
        var record = await _context.AttendanceRecords.FindAsync(id);
        if (record == null)
        {
            return NotFound();
        }

        _context.AttendanceRecords.Remove(record);
        await _context.SaveChangesAsync();

        return NoContent();
    }
}