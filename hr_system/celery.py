"""
Celery configuration for hr_system project.
"""

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_system.settings')

app = Celery('hr_system')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()