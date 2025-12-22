using Microsoft.EntityFrameworkCore;
using ZKBiometricService.Core.Models;

namespace ZKBiometricService.Data;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options)
    {
    }

    public DbSet<Device> Devices { get; set; }
    public DbSet<Employee> Employees { get; set; }
    public DbSet<AttendanceRecord> AttendanceRecords { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.Entity<Device>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Name).IsRequired().HasMaxLength(100);
            entity.Property(e => e.IpAddress).IsRequired().HasMaxLength(15);
            entity.Property(e => e.SerialNumber).HasMaxLength(50);
            entity.Property(e => e.Model).HasMaxLength(50);
            entity.HasIndex(e => e.IpAddress).IsUnique();
        });

        modelBuilder.Entity<Employee>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.EmployeeId).IsRequired().HasMaxLength(20);
            entity.Property(e => e.Name).IsRequired().HasMaxLength(100);
            entity.Property(e => e.Department).HasMaxLength(50);
            entity.Property(e => e.Position).HasMaxLength(50);
            entity.HasIndex(e => e.EmployeeId).IsUnique();
        });

        modelBuilder.Entity<AttendanceRecord>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.EmployeeId).IsRequired().HasMaxLength(20);
            entity.Property(e => e.RecordTime).IsRequired();
            
            entity.HasIndex(e => new { e.DeviceId, e.RecordTime });
            entity.HasIndex(e => new { e.EmployeeId, e.RecordTime });
            entity.HasIndex(e => e.RecordTime);
            
            entity.HasOne(e => e.Device)
                .WithMany()
                .HasForeignKey(e => e.DeviceId)
                .OnDelete(DeleteBehavior.Restrict);
                
            entity.HasOne(e => e.Employee)
                .WithMany()
                .HasForeignKey(e => e.EmployeeId)
                .HasPrincipalKey(e => e.EmployeeId)
                .OnDelete(DeleteBehavior.Restrict);
        });
    }
}