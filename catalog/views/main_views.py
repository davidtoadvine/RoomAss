#
# Main Views for visible pages of the application
#

from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from catalog.forms import DateRangeForm, PersonSelectForm, RoomSelectForm, SectionSelectForm
from catalog.models import CustomEvent, Room, Person, Building, Section
from catalog.utils import date_to_aware_datetime, process_occupancy_events

def available_rooms(request):
    
    # get and order rooms for sensible display later
    rooms = Room.objects.select_related('section__building').order_by('section__building__name', 'section__name', 'number')
    
    # handle form submission
    if request.method == 'POST':
        form = DateRangeForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
            guest_type = form.cleaned_data.get('guest_type')
            
        else:
            # If the form is not valid, render the form with error message
            return render(request, 'catalog/available_rooms.html', {'form': form})

    # retrieve prior session values if not a form submisison
    else:
        # Retrieve data from session if available
        start_date = request.session.get('start_date', timezone.localtime(timezone.now()).date())
        end_date = request.session.get('end_date', timezone.localtime(timezone.now()).date() + timedelta(days=1))
        guest_type = int(request.session.get('guest_type', 2))

        form = DateRangeForm(initial={
            'start_date': start_date,
            'end_date': end_date,
            'guest_type': guest_type
        })

    # Get the current local date and the next day's date
    local_now = timezone.localtime(timezone.now())
    today = local_now.date()
    tomorrow = today + timedelta(days=1)
    

    default_start_date = today
    default_end_date = tomorrow

    # Convert the start and end date strings to timezone-aware datetime objects
    if start_date and end_date:
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Convert to aware datetime objects with specific times
        start_date = date_to_aware_datetime(start_date, 23, 59)
        end_date = date_to_aware_datetime(end_date, 11, 59)
    else:
        # Use default dates if not provided
        start_date = date_to_aware_datetime(default_start_date, 23, 59)
        end_date = date_to_aware_datetime(default_end_date, 11, 59)


    available_rooms_info = []
    for room in rooms:
        
        if room.is_available(start_date, end_date) and (not room.owner or int(guest_type) >= int(room.owner.preference)):
          potential_end_date = room.get_last_available_date(start_date)
          if room.image:
            room_image_url = room.image.url
          else:
            room_image_url = "" 
          room_name = str(room)
          available_rooms_info.append((room, potential_end_date, room_image_url, room_name))

    context = {
        'available_rooms_info': available_rooms_info,
        'start_date': start_date.strftime('%Y-%m-%d') if start_date else today.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d') if end_date else tomorrow.strftime('%Y-%m-%d'),
        'today': today,
        'tomorrow': tomorrow,
        'form': form,
        'guest_type': guest_type
    }
    return render(request, 'catalog/available_rooms.html', context)



def all_guests(request):
    occupancy_events = CustomEvent.objects.filter(event_type='occupancy')

    processed_events = []

    for event in occupancy_events:
        room_owner = "Unassigned"

        if event.calendar.room.owner:
            room_owner = event.calendar.room.owner

        event_info = {
            'guest_name': event.guest_name,
            'creator': event.creator,
            'start_date': event.start,
            'end_date': event.end,
            'room_name': str(event.calendar.room),
            'room_id': event.calendar.room.id,
            'room_owner': room_owner
            }
        processed_events.append(event_info)

    context = {
        'occupancy_events': processed_events,
    }
    return render(request, 'catalog/all_guests.html', context)


@login_required
def my_room(request):
  request.session['source_page'] = 'my_room'

  person = request.user.person

  if hasattr(person, 'room'):
    room = person.room
    calendar = room.calendar
    
    # Events for room owner
    events_exist = CustomEvent.objects.filter(calendar=calendar, event_type='availability').exists()
    availability_events = CustomEvent.objects.filter(calendar=calendar, event_type='availability').order_by('start')
    occupancy_events = CustomEvent.objects.filter(calendar = calendar, event_type = 'occupancy').order_by('start')
    # Processing so we can display booked AND vacant timeblocks within an availability
    occupancy_events_processed = process_occupancy_events(availability_events,occupancy_events)

    # Get events for any children
    children = person.children.all()

    children_info = {}
    for child in children:
                  child_room = Room.objects.get(owner=child)
                  if child_room and child_room.calendar:
                      child_calendar = child_room.calendar
                      child_events_exist = CustomEvent.objects.filter(calendar=child_calendar, event_type='availability').exists()
                      child_availability_events = CustomEvent.objects.filter(calendar=child_calendar, event_type='availability').order_by('start')
                      child_occupancy_events = CustomEvent.objects.filter(calendar=child_calendar, event_type='occupancy').order_by('start')
                      # Processing so we can display booked AND vacant timeblocks within an availability
                      child_occupancy_events_processed = process_occupancy_events(child_availability_events,child_occupancy_events)

                      children_info[child] = {
                          'availability_events': child_availability_events,
                          'occupancy_events_and_vacancies': child_occupancy_events_processed,
                          'room_image_url': child_room.image.url if child_room.image else '',
                          'room_name': str(child.room),
                          'events_exist':child_events_exist,
                      }


    # Get the current local date and the next day's date
    local_now = timezone.localtime(timezone.now())
    tomorrow = local_now.date() + timedelta(days=1)
    dayafter = tomorrow + timedelta(days=1)

    context = {
        'room': room,
        'room_id':room.id,
        'availability_events': availability_events,
        'occupancy_events_and_vacancies': occupancy_events_processed,
        'children_info': children_info,
        'children': children,
        'start_date': tomorrow.strftime('%Y-%m-%d'),
        'end_date': dayafter.strftime('%Y-%m-%d'),
        'source_page': 'my_room',
        'room_image_url': room.image.url if room.image else '',
        'room_name': room,
        'events_exist': events_exist,
    }
    return render(request, 'catalog/my_room.html', context)
  
  else:
      return redirect('no_room')




@login_required
def my_guests(request):
    request.session['source_page'] = 'my_guests'
    occupancy_events = CustomEvent.objects.filter(event_type='occupancy', creator=request.user)

    processed_events = []

    for event in occupancy_events:
        room_owner = "Unassigned"
        if event.calendar.room.owner:
            room_owner = event.calendar.room.owner
        event_info = {
            'id': event.id,
            'guest_name': event.guest_name,
            'creator': event.creator,
            'start_date': event.start,
            'end_date': event.end,
            'last_available': event.calendar.room.get_last_available_date(event.end),
            'room_name': str(event.calendar.room),
            'image_url': event.calendar.room.image.url if event.calendar.room.image else '',  # Store the image URL for each event
            'room_owner': room_owner
        }
    
        processed_events.append(event_info)


    context = {
        'occupancy_events': processed_events,
        'source_page': 'my_guests'
    }
    return render(request, 'catalog/my_guests.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser or u.has_perm('app.view_all_rooms'))
def rooms_master(request, room_id=None, section_id=None):
    
    request.session['source_page'] = 'rooms_master'
    roomless_members = Person.objects.filter(room__isnull=True)

    person_form = PersonSelectForm()
    room_form = RoomSelectForm()
    section_form = SectionSelectForm()

    selected_person = None
    selected_room = None

    # Dealing with form submissions on the page
    if request.method == 'POST':

        if 'person_form_submit' in request.POST:
            person_form = PersonSelectForm(request.POST)
            if person_form.is_valid():
                selected_person = person_form.cleaned_data['person']
                
                try:
                    selected_room = selected_person.room
                except Room.DoesNotExist:
                    return redirect('no_room')
                return redirect('rooms_master_with_room', room_id=selected_room.id )
                
          
        elif 'room_form_submit' in request.POST:
            room_form = RoomSelectForm(request.POST)
            if room_form.is_valid():
                selected_room = room_form.cleaned_data['room']
                return redirect('rooms_master_with_room', room_id=selected_room.id)
            
        elif 'section_form_submit' in request.POST:
            section_form = SectionSelectForm(request.POST)
            if section_form.is_valid():
                selected_room = section_form.cleaned_data['section']
                return redirect('rooms_master_with_section', section_id=selected_room.id)
            
        
        else:
            return redirect('rooms_master')



    # Displaying what's called for
    else:  

      room_name = None
      context = {
          'source_page': 'rooms_master',
          'roomless_members':roomless_members
      }

      local_now = timezone.localtime(timezone.now())
      tomorrow = local_now.date() + timedelta(days=1)
      dayafter = tomorrow + timedelta(days=1)
    
    
      context.update( {
            'person_form': person_form,
            'room_form': room_form,
            'section_form':section_form,
            'start_date': tomorrow.strftime('%Y-%m-%d'),
            'end_date': dayafter.strftime('%Y-%m-%d'),
      })

      # if a single room is selected
      if room_id:
        selected_room = get_object_or_404(Room, id=room_id)
        room_name = str(selected_room)
        if selected_room.owner:
              selected_person = selected_room.owner
              room_name = str(selected_room)

        local_now = timezone.localtime(timezone.now())
        tomorrow = local_now.date() + timedelta(days=1)
        dayafter = tomorrow + timedelta(days=1)
    
    
        context.update( {
            'selected_person': selected_person,
            'room': selected_room,
            'room_name': room_name,
            'room_id': room_id,
            
        })
    
        if selected_room:
          calendar = selected_room.calendar

          events_exist = CustomEvent.objects.filter(calendar=calendar, event_type='availability').exists()
          availability_events = CustomEvent.objects.filter(calendar=calendar, event_type='availability').order_by('start') if calendar else None
          occupancy_events = CustomEvent.objects.filter(calendar=calendar, event_type='occupancy').order_by('start') if calendar else None
        
          # Processing so we can display booked AND vacant timeblocks within an availability
          occupancy_events_processed = process_occupancy_events(availability_events,occupancy_events)
  
          context.update({
              'room': selected_room,
              'room_id': selected_room.id,
              'room_image_url': selected_room.image.url if selected_room.image else '',
              'availability_events': availability_events,
              'occupancy_events_and_vacancies': occupancy_events_processed,
              'events_exist': events_exist
                    
          })
  
          if selected_person:
              children = selected_person.children.all()
              children_info = {}
  
              for child in children:
                  child_room = Room.objects.get(owner=child)
                  if child_room and child_room.calendar:
                      child_calendar = child_room.calendar
                      child_availability_events = CustomEvent.objects.filter(calendar=child_calendar, event_type='availability').order_by('start')
                      child_occupancy_events = CustomEvent.objects.filter(calendar=child_calendar, event_type='occupancy').order_by('start')
                      events_exist = CustomEvent.objects.filter(calendar=child_calendar, event_type='availability').exists()
                      child_occupancy_events_processed= process_occupancy_events(child_availability_events, child_occupancy_events)
                      children_info[child] = {
                          'availability_events': child_availability_events,
                          'occupancy_events_and_vacancies': child_occupancy_events_processed,
                          'room_image_url': child_room.image.url if child_room.image else '',
                          'room_name': str(child_room),
                          'events_exist':events_exist
                      }
  
              context.update({
                  'children_info': children_info,
                  'children': children,

              })
      
      # if an entire section is selected
      elif section_id:

        selected_section = get_object_or_404(Section, id=section_id)
        rooms_in_section = Room.objects.filter(section=selected_section)

        section_events = {}
  
        for room in rooms_in_section:
          
            if room and room.calendar:
              
                calendar = room.calendar
                room_title = str(room)
                if room.owner:
                    room_title = str(room.owner) + "'s Room"

                events_exist = CustomEvent.objects.filter(calendar=calendar, event_type='availability').exists()
                availability_events = CustomEvent.objects.filter(calendar=calendar, event_type='availability').order_by('start')
                occupancy_events = CustomEvent.objects.filter(calendar=calendar, event_type='occupancy').order_by('start')
              
                # Processing so we can display booked AND vacant timeblocks within an availability
                occupancy_events_processed = process_occupancy_events(availability_events,occupancy_events)

                section_events[room] = {
                    'availability_events': availability_events,
                    'occupancy_events_and_vacancies': occupancy_events_processed,
                    'room_image_url': room.image.url if room.image else '',
                    'room_name': str(room),
                    'events_exist':events_exist,
                    'room_id':room.id,
                    'owner_id':room.owner.id if room.owner else None,
                    'room_title' : room_title,
                }

        context.update({
            'selected_section': selected_section,
            'section_title': str(selected_section) + " Section",
            'section_id':section_id,
            'rooms_in_section': rooms_in_section,
        })
        context.update({
                  'section_events': section_events,
              })
        # for room, events in section_events.items():
        #     print(f"Room ID: {room.id} - Occupancy Event IDs:")
        #     for event in events['occupancy_events']:
        #         if 'event' in event:
        #             print(event['event'].id)
        # print("Room Master Bottom")
    return render(request, 'catalog/rooms_master.html', context)

# @login_required
# @user_passes_test(lambda u: u.is_superuser or u.has_perm('app.buildings_offline_toggle'))
# def buildings_offline_toggle(request):
#     buildings = Building.objects.all().order_by('name')

#     return render(request, 'catalog/buildings_offline_toggle.html', {'buildings': buildings})


# @require_POST
# def toggle_offline_section(request):
#     section_id = request.POST.get('section_id')
#     section = get_object_or_404(Section, id=section_id)

#     # Toggle the offline status
#     section.is_offline = not section.is_offline
#     section.save()

#     return redirect('buildings_offline_toggle')

