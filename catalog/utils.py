
from datetime import datetime, time

import pytz

from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect

from catalog.models import CustomEvent, Room, Building


# Merge overlapping availability events on a single calendar
# I guess this could have been part of Calendar model
#  but that model is imported so I didn't want to mess with it
def merge_overlapping_availabilities(calendar):
    
    # get availability events from calendar ordered by start date
    events = CustomEvent.objects.filter(calendar = calendar, event_type='availability').order_by('start')
    merged_events = []
    
    # go through them
    for event in events:
        # add first event to list
        if not merged_events:
            merged_events.append(event)
        # then...
        else:
            # get the last merged event in list
            last_event = merged_events[-1]
            
            # Normalize times of events to 12:00 PM for sake of comparison
            normalized_last_end = normalize_time(last_event.end)
            normalized_current_start = normalize_time(event.start)
            
            # adjust and cull as the merge operation
            if normalized_current_start <= normalized_last_end:
                if event.end > last_event.end:
                    last_event.end = event.end
                last_event.save()
                event.delete()

            else:
                # there's no overlap so don't merge anything
                merged_events.append(event)

    # save your work
    for event in merged_events:
        event.save()

# Set time of day equal for comparing days
def normalize_time(datetime):
  return datetime.replace(hour=12, minute=0, second=0, microsecond=0)


# For navigation back to correct room pages
def event_id_to_redirect_room_id(event_id):
  occ_event = get_object_or_404(CustomEvent, id = event_id)
  
  # ownerless rooms
  room_id = occ_event.calendar.room.id
  # owned rooms
  if occ_event.calendar.room.owner:
    person = occ_event.calendar.room.owner
    # if room owner is a child, redirect to parent's page
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
        #print(f"Converted Naive Date: {aware_date} to Timezone: {timezone.get_current_timezone()}")
    else:
        aware_date = date
        #print(f"Date is already aware: {aware_date}")

    # Convert to specified timezone
    target_timezone = pytz.timezone(tz_name)
    converted_date = aware_date.astimezone(target_timezone)
    #print(f"Converted Date to {tz_name} Timezone: {converted_date}")

    return converted_date


# occupation events will sometimes be disrupted by the alteration of availabiliity events
# this attempts to find another room that is available for the missing chunk of time
# calls create_stopgap_booking if possible, sends emails regardless
def handle_reassign(occ_event, start_date, end_date, owner, room):
                  
    guest_type = occ_event.guest_type
    guest_name = occ_event.guest_name
    host_email = occ_event.creator.email

    original_room = room

    # getting available rooms in order of assumed geographic preference
    original_building = original_room.section.building
    buildings_in_same_area = Building.objects.filter(area=original_building.area).exclude(id=original_building.id)
    buildings_in_other_area = Building.objects.exclude(area = original_building.area)

    # randomly order the rooms in each area
    rooms_in_original_building = Room.objects.filter(section__building = original_building).order_by('?')
    rooms_in_same_area = Room.objects.filter(section__building__in = buildings_in_same_area).order_by('?')
    rooms_outside_original_area = Room.objects.filter(section__building__in = buildings_in_other_area).order_by('?')

    # ooh boy now we've got a list
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
          #print('event not reassigned')
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

# i think this is assessing events on a room's calender in order to create a sensible display
# but it's been while since I've looked at it
def process_occupancy_events(availability_events, occupancy_events):
    
    occupancy_events_processed = []

    for avail_event in availability_events:
            

              edge_date = avail_event.start
              for occ_event in occupancy_events:
                  if occ_event.start >= avail_event.start and occ_event.end <= avail_event.end:

                    if occ_event.start > edge_date and edge_date.date() != occ_event.start.date():
                          occupancy_events_processed.append({
                              'start': edge_date,
                              'end': occ_event.start,
                              'type': 'Vacant'
                          })
                    
                    occupancy_events_processed.append({
                        'event': occ_event,
                        'start': occ_event.start,
                        'end': occ_event.end,
                        'type': 'Booked',
                        'title': occ_event.title,
                        'id':occ_event.id
                        })
                    
                    edge_date = occ_event.end

              if edge_date < avail_event.end and edge_date.date() != avail_event.end.date():
                occupancy_events_processed.append({
                'start': edge_date,
                'end': avail_event.end,
                'type': 'Vacant'
              })
    return occupancy_events_processed