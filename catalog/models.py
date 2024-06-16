from django.db import models
from schedule.models import Calendar, Event
from django.utils import timezone
import pytz
from datetime import datetime
from datetime import timedelta

# Create your models here.
class Building(models.Model):
  name = models.CharField(max_length = 255)
  
  def __str__(self):
    return self.name
  
class Section(models.Model):
  building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='floors')
  name = models.CharField(max_length=255)
  #imagefield needed

  def __str__(self):
    return f"{self.building.name} / {self.name} Section"

class Room(models.Model):
  section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='rooms')
  number = models.IntegerField()
  #available = models.BooleanField()
  calendar = models.OneToOneField(Calendar, on_delete=models.CASCADE, null=True, blank=True, related_name='room_calendar')
  owner = models.OneToOneField('Person', on_delete=models.SET_NULL, null=True, blank=True, related_name='room_owner')
  
  @staticmethod
  def create_room_calendar(room):
        calendar_name = f"Room {room.number} Calendar"
        calendar_slug = f"room-{room.number}"
        calendar, created = Calendar.objects.get_or_create(name=calendar_name, slug=calendar_slug)
        if created:
            calendar.save()
        room.calendar = calendar
        room.save()
        

  def __str__(self):
    return f"{self.section.building.name} Section {self.section.name} Room {self.number}"

  def is_available(self, start_date, end_date):
        if not self.calendar:
            return True
        
        # Hacky feeling fix for requesting dates where occupancy event begins / ends.
        # Otherwise an occupancy ending on at 11:59am would make room unavailable for new afternoon occupancy.
        # Likewise occupancy beginning on an afternoon would make whole day unavailable.
        # Unsure why comparisons would not work as intended.
        #start_date = start_date + timedelta(days=1)
        #end_date = end_date - timedelta(days=1)

        # Convert dates to UTC for accurate comparisons
        if timezone.is_naive(start_date):
            start_date = timezone.make_aware(start_date, timezone.get_current_timezone())
        if timezone.is_naive(end_date):
            end_date = timezone.make_aware(end_date, timezone.get_current_timezone())

        # start_date_utc = start_date.astimezone(pytz.utc)
        # end_date_utc = end_date.astimezone(pytz.utc)
      
        print(self.__str__)
        occupancy_events = CustomEvent.objects.filter(
            calendar=self.calendar,
            event_type='occupancy',
            start__lt=end_date,
            end__gt=start_date
        )
        print(occupancy_events.exists())

        availability_events = CustomEvent.objects.filter(
    calendar=self.calendar,
    event_type='availability',
    start__lte=end_date,
    end__gte=end_date  # Ensure availability end is after or equal to booking end date
)
        print(availability_events.exists())

        # Detailed debugging output
        # print(f"Start Date UTC: {start_date_utc}, End Date UTC: {end_date_utc}")
        # print(f"Occupancy Events: {occupancy_events}")
        # print(f"Availability Events: {availability_events}")

        # Print details of fetched events for debugging
        # for event in occupancy_events:
        #     print(f"Occupancy Event - Start: {event.start}, End: {event.end}")
        # for event in availability_events:
        #     print(f"Availability Event - Start: {event.start}, End: {event.end}")

    
        # Check for available and not occupied
        return availability_events.exists() and not occupancy_events.exists()
  
  def get_last_available_date(self, start_date):
        if not self.calendar:
            print('no calendar')
            return None

        # Ensure start_date is timezone-aware and convert to UTC for consistent comparison
        start_date = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        if timezone.is_naive(start_date):
            start_date = timezone.make_aware(start_date, timezone.get_current_timezone())
        start_date_utc = start_date.astimezone(pytz.utc)

        # print(f"start_date_utc: {start_date_utc}")

        # Fetch and print all availability events for debugging
        # all_availabilities = CustomEvent.objects.filter(
        #     calendar=self.calendar,
        #     event_type='availability'
        # )
        # for availability in all_availabilities:
        #     availability_start_utc = availability.start.astimezone(pytz.utc)
        #     availability_end_utc = availability.end.astimezone(pytz.utc)
            # print(f"availability: start={availability_start_utc}, end={availability_end_utc}")

        # Fetch current availability event
        current_availability = CustomEvent.objects.filter(
            calendar=self.calendar,
            event_type='availability',
            start__lte=start_date_utc,
            end__gte=start_date_utc
        ).first()

        if not current_availability:
            print("No Current Availability")
            return None

        # Fetch next occupancy event within the availability window
        next_occupancy = CustomEvent.objects.filter(
            calendar=self.calendar,
            event_type='occupancy',
            start__gte=start_date_utc,
            start__lt=current_availability.end
        ).order_by('start').first()

        if next_occupancy:
            return min(current_availability.end, next_occupancy.start)
        else:
            print("returning current availability.end")
            return current_availability.end

  def save(self, *args, **kwargs):
        
        # Ensure the room has a calendar
        if not self.calendar:
            self.calendar = Calendar.objects.create()

        # Update the calendar name
        if (self.owner):
          self.calendar.name = f"{self.owner.name}'s Calendar"  # You can customize this as needed
        else:
          self.calendar.name = f"{self.__str__()}'s Calendar"
        self.calendar.save()

        super().save(*args, **kwargs)
        # Create a specific datetime object far in the future
        never_date = datetime(2999, 4, 20, 12, 0, 0)  # April 20, 2999 at noon

        # Make it timezone-aware
        never_date = timezone.make_aware(never_date, timezone.get_current_timezone())
        if not self.owner:
            # Create or update a permanent availability event
            CustomEvent.objects.update_or_create(
                calendar=self.calendar,
                event_type='availability',
                defaults={
                    'start': timezone.now(),
                    'end':   never_date
                }
            )
        else:
            # Ensure no availability event exists for this room if it has an owner
            CustomEvent.objects.filter(
                calendar=self.calendar,
                event_type='availability'
            ).delete()
        
      
  
  

class Person(models.Model):
  name = models.CharField(max_length=255)
  contact_email = models.EmailField(null=True, blank=True)
  def __str__(self):
    return self.name

class CustomEvent(Event):
    EVENT_TYPES = (
        ('occupancy', 'Occupancy'),
        ('availability', 'Availability'),
    )
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    def save(self, *args, **kwargs):
        # Ensure start and end are timezone-aware
        if timezone.is_naive(self.start):
            self.start = timezone.make_aware(self.start, timezone.get_current_timezone())
        if timezone.is_naive(self.end):
            self.end = timezone.make_aware(self.end, timezone.get_current_timezone())
        super(CustomEvent, self).save(*args, **kwargs)

#def create_booking(start_date,end_date):
    