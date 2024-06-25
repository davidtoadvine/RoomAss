from celery import shared_task
from django.utils import timezone
from .models import Event  # Replace with your actual model

@shared_task
def delete_ended_events():
    now = timezone.now()
    ended_events = Event.objects.filter(end_time__lt=now)
    count = ended_events.count()
    ended_events.delete()
    return f'Successfully deleted {count} events that have ended.'