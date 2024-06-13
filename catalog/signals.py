  
from django.db.models.signals import post_save
from django.dispatch import receiver
from schedule.models import Calendar
from .models import Room
from django.utils.text import slugify
import uuid
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Room, Person

@receiver(post_save, sender=Room)
def create_room_calendar(sender, instance, created, **kwargs):
    if created:
        base_slug = slugify(f"room-{instance.number}-calendar")
        unique_slug = base_slug
        num = 1
        while Calendar.objects.filter(slug=unique_slug).exists():
            unique_slug = f"{base_slug}-{num}"
            num += 1


        calendar_name = f"Room {instance.number} Calendar"
        calendar = Calendar.objects.create(name=calendar_name, slug=unique_slug)
        instance.calendar = calendar
        instance.save()
