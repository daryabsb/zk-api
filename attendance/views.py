"""
Views for attendance management.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from .models import AttendanceRecord, Employee
import json


@method_decorator(csrf_exempt, name='dispatch')
class AttendanceAPIView(View):
    """API endpoint for attendance records."""
    
    def get(self, request):
        """Get attendance records with optional filters."""
        employee_id = request.GET.get('employee_id')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        records = AttendanceRecord.objects.all()
        
        if employee_id:
            records = records.filter(employee__employee_id=employee_id)
        
        if start_date:
            records = records.filter(punch_time__date__gte=start_date)
        
        if end_date:
            records = records.filter(punch_time__date__lte=end_date)
        
        data = [
            {
                'employee_id': record.employee.employee_id,
                'employee_name': f"{record.employee.user.first_name} {record.employee.user.last_name}",
                'punch_time': record.punch_time.isoformat(),
                'device_ip': record.device_ip,
                'status': record.status,
            }
            for record in records[:100]  # Limit to 100 records
        ]
        
        return JsonResponse({'success': True, 'records': data})
    
    def post(self, request):
        """Create attendance records from device sync."""
        try:
            data = json.loads(request.body)
            records = data.get('records', [])
            
            created_count = 0
            for record_data in records:
                try:
                    employee_id = record_data.get('employee_id')
                    punch_time = record_data.get('punch_time')
                    device_ip = record_data.get('device_ip')
                    
                    if not all([employee_id, punch_time, device_ip]):
                        continue
                    
                    employee = Employee.objects.get(employee_id=employee_id)
                    
                    AttendanceRecord.objects.create(
                        employee=employee,
                        punch_time=punch_time,
                        device_ip=device_ip,
                        device_id=record_data.get('device_id', 0),
                        verification_mode=record_data.get('verification_mode', 0),
                        status=record_data.get('status', 0),
                    )
                    created_count += 1
                    
                except Employee.DoesNotExist:
                    continue
                except Exception as e:
                    continue
            
            return JsonResponse({
                'success': True, 
                'message': f'Created {created_count} attendance records'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)


@csrf_exempt
@require_http_methods(["GET"])
def attendance_stats(request):
    """Get attendance statistics."""
    total_records = AttendanceRecord.objects.count()
    total_employees = Employee.objects.filter(is_active=True).count()
    
    return JsonResponse({
        'success': True,
        'stats': {
            'total_records': total_records,
            'total_employees': total_employees,
        }
    })