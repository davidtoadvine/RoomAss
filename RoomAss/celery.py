from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
from datetime import timedelta

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RoomAss.settings')

app = Celery('RoomAss')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.update(
    broker_url='amqp://guest:guest@localhost//',
    # Define periodic tasks schedule
    beat_schedule={
        'delete-ended-events-every-midnight': {
            'task': 'catalog.tasks.delete_ended_events',  # Your task
            'schedule': crontab(hour=19, minute=53),  # Runs at midnight every day
        },
       
    },

    # Optionally specify max interval for checking tasks
    beat_max_interval=30.0,  # Celery Beat checks for tasks every 30 seconds
)