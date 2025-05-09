from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    # Deactivate expired jobs every hour
    'deactivate-expired-jobs': {
        'task': 'jobs.tasks.deactivate_expired_jobs',
        'schedule': crontab(minute=0),  # Run every hour
    },
    
    # Send deadline reminders every day at 9 AM
    'send-deadline-reminders': {
        'task': 'jobs.tasks.send_deadline_reminders',
        'schedule': crontab(hour=9, minute=0),  # Run at 9 AM daily
    },
    
    # Update job metrics every 6 hours
    'update-job-metrics': {
        'task': 'jobs.tasks.update_job_metrics',
        'schedule': crontab(minute=0, hour='*/6'),  # Run every 6 hours
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 