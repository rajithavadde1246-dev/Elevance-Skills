import os

from celery import Celery


# Set Django settings module
os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'ticket_system.settings'
)


# Create Celery application
app = Celery('ticket_system')


# Read Celery configuration from Django settings
app.config_from_object(
    'django.conf:settings',
    namespace='CELERY'
)


# Automatically discover tasks.py
# inside installed Django applications
app.autodiscover_tasks()