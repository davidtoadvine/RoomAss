# your_project/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RoomAss.settings')

app = Celery('RoomAss')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Optional configuration, see the application user guide.
app.conf.update(
    broker_url='redis://localhost:6379/0',
)

app.conf.beat_schedule = {
    'delete-ended-events-every-midnight': {
        'task': 'your_app.tasks.delete_ended_events',
        'schedule': crontab(hour=0, minute=0),
    },
}
