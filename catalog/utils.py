from catalog.models import Room, Building, Section, Person, CustomEvent

from datetime import timedelta, time
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse

from django.core.mail import send_mail
import pytz
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib.auth.models import User

from django.shortcuts import render, get_object_or_404, redirect
from catalog.models import CustomEvent
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from datetime import datetime, timedelta
from catalog.models import CustomEvent, Room, Person

######### Non View Helper Functions############
############################################################################################################

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

def handle_reassign(occ_event, start_date, end_date, owner):
                
                  rooms = Room.objects.select_related('section__building').order_by('section__building__name', 'section__name', 'number')
                  
                  guest_type = occ_event.guest_type
                  guest_name = occ_event.guest_name
                  host_email = occ_event.creator.email

                  for room in rooms:
                    
                    email_start_date = (start_date.__str__())[:-15]
                    email_end_date = (end_date.__str__())[:-15]
                    event_assigned = False

                    if (    (room.is_available(start_date, end_date))
                            and
                            ((room.owner and int(guest_type) >= int(room.owner.preference))
                            or
                            (not room.owner))):
                        

                            #occ_event.end = start_date
                            #occ_event.save()
                            create_stopgap_booking(room, occ_event, start_date, end_date, occ_event.guest_type, occ_event.guest_name)
                            event_assigned = True

                            send_mail(
                                      "Your room booking has changed",
                                      f"{owner} has had an availability change. Your guest {guest_name} has been reassigned to a different room from {email_start_date} to {email_end_date}. Visit 'My Guests' in the room system to see the details. ",
                                      "autoRoomAss@email.com",
                                      [f"{host_email}"],
                                      fail_silently=False
                                      )

                            break
                        
                            
                  if not event_assigned:
                      send_mail(
                                      "Your room booking has changed",
                                      f"{owner} has had an availability change. Your guest {guest_name} could not be automatically assigned to a different room. Contact the room assigner for help. ",
                                      "autoRoomAss@email.com",
                                      [f"{host_email}"],
                                      fail_silently=False
                                      )
                      


def create_stopgap_booking(room, event, start_date, end_date, guest_type, guest_name):
                              
                            #book it
                              booking_event = CustomEvent(
                              calendar=room.calendar,
                              event_type='occupancy',
                              start=start_date,
                              end=end_date,
                              title= f"Auto Booking: {guest_name} hosted by {str(event.creator)}",
                              description = "Meaningful Description",
                              creator = event.creator,
                              guest_type = guest_type,
                              guest_name = guest_name
                              )
                              booking_event.save()