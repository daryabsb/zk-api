"""
URL configuration for devices app."""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.DeviceAPIView.as_view(), name='device-list'),
    path('test/<int:device_id>/', views.test_device_connection, name='test-device-connection'),
    path('sync/<int:device_id>/', views.sync_device_attendance, name='sync-device-attendance'),
]