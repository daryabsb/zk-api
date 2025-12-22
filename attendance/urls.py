"""
URL configuration for attendance app.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('records/', views.AttendanceAPIView.as_view(), name='attendance-records'),
    path('stats/', views.attendance_stats, name='attendance-stats'),
]