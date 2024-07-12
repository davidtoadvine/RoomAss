
from datetime import datetime, time

import pytz

from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.utils import timezone

from catalog.models import CustomEvent, Room, Building

def merge_overlapping_events(calendar):
    
    events = CustomEvent.objects.filter(calendar = calendar, event_type='availability').order_by('start')
    merged_events = []
    
    for event in events:
        if not merged_events:
            merged_events.append(event)
        else:
            last_event = merged_events[-1]
            
            # Normalize times to 12:00 PM for comparison
            normalized_last_end = normalize_time(last_event.end)
            normalized_current_start = normalize_time(event.start)
            
            if normalized_current_start <= normalized_last_end:
                # Overlapping or contiguous events
                if event.end > last_event.end:
                    last_event.end = event.end
                last_event.save()
                event.delete()
            else:
                merged_events.append(event)

    for event in merged_events:
        event.save()


def normalize_time(dt):
    return dt.replace(hour=12, minute=0, second=0, microsecond=0)


def event_id_to_redirect_room_id(event_id):
            occ_event = get_object_or_404(CustomEvent, id = event_id)
            
            #for no owner
            room_id = occ_event.calendar.room.id

            #for owned room, check if kid
            if occ_event.calendar.room.owner:
              person = occ_event.calendar.room.owner
              if person.parent:
                person = person.parent
              room_id = person.room.id
            
            return room_id



def date_to_aware_datetime(date, hour, minute ):
    # Convert dates to datetime objects with specific time (around noon)
            if isinstance(date, datetime):
                date = date.replace(hour=hour, minute=minute)
            else:
                date = datetime.combine(date, time(hour, minute))
            return ensure_timezone_aware(date)

def ensure_timezone_aware(date, tz_name='America/New_York'):
    if timezone.is_naive(date):
        aware_date = timezone.make_aware(date, timezone.get_current_timezone())
        print(f"Converted Naive Date: {aware_date} to Timezone: {timezone.get_current_timezone()}")
    else:
        aware_date = date
        print(f"Date is already aware: {aware_date}")

    # Convert to specified timezone
    target_timezone = pytz.timezone(tz_name)
    converted_date = aware_date.astimezone(target_timezone)
    print(f"Converted Date to {tz_name} Timezone: {converted_date}")

    return converted_date


# this if for after editing or deleting availability events
# attempts to find another room that is available for the missing chunk of time
# calls create_stopgap_booking if possible, sends emails regardless
def handle_reassign(occ_event, start_date, end_date, owner, room):
                  
                  guest_type = occ_event.guest_type
                  guest_name = occ_event.guest_name
                  host_email = occ_event.creator.email

                  original_room = room

                  # getting available rooms in order of geographic preference
                  original_building = original_room.section.building
                  buildings_in_same_area = Building.objects.filter(area=original_building.area).exclude(id=original_building.id)
                  buildings_in_other_area = Building.objects.exclude(area = original_building.area)

                  rooms_in_original_building = Room.objects.filter(section__building = original_building).order_by('?')
                  rooms_in_same_area = Room.objects.filter(section__building__in = buildings_in_same_area).order_by('?')
                  rooms_outside_original_area = Room.objects.filter(section__building__in = buildings_in_other_area).order_by('?')

                  rooms = list(rooms_in_original_building) + list(rooms_in_same_area) + list(rooms_outside_original_area)

                  event_assigned = False

                  for room in rooms:
                      email_start_date = start_date.strftime('%Y-%m-%d')
                      email_end_date = end_date.strftime('%Y-%m-%d')

                      if room.is_available(start_date, end_date) and (
                        (room.owner and int(guest_type) >= int(room.owner.preference)) or not room.owner):

                              create_stopgap_booking(room, occ_event, start_date, end_date, occ_event.guest_type, occ_event.guest_name)
                              event_assigned = True

                              send_mail(
                                        "Your room booking has changed",
                                        f"{owner} has had an availability change. Your guest {guest_name} has been reassigned to a different room from {email_start_date} to {email_end_date}. Visit 'My Guests' in the room system to see the details. ",
                                        "autoRoomAss@email.com",
                                        [f"{host_email}"],
                                        fail_silently=False
                                        )

                              return
                          
                              
                  if not event_assigned:
                        print('event not reassigned')
                        send_mail(
                                        "Your room booking has changed",
                                        f"{owner} has had an availability change. Your guest {guest_name} could not be automatically assigned to a different room. Contact the room assigner for help. ",
                                        "autoRoomAss@email.com",
                                        [f"{host_email}"],
                                        fail_silently=False
                                        )
# for automatic reassign
def create_stopgap_booking(room, event, start_date, end_date, guest_type, guest_name):
                              
                            #book it
                              booking_event = CustomEvent(
                              calendar=room.calendar,
                              event_type='occupancy',
                              start=start_date,
                              end=end_date,
                              title= f"Booking: {guest_name} hosted by {str(event.creator)}",
                              description = "Meaningful Description",
                              creator = event.creator,
                              guest_type = guest_type,
                              guest_name = guest_name
                              )
                              booking_event.save()