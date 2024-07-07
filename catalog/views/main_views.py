from catalog.forms import DateRangeForm, UserSelectForm
from catalog.models import CustomEvent, Room, Person

from catalog.utils import date_to_aware_datetime

from datetime import datetime, timedelta
from django.utils import timezone

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib.auth.models import User


def home(request):
    
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
            start_date = None
            end_date = None
            guest_type = None

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
          available_rooms_info.append((room, potential_end_date, room_image_url))

    context = {
        'available_rooms_info': available_rooms_info,
        'start_date': start_date.strftime('%Y-%m-%d') if start_date else today.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d') if end_date else tomorrow.strftime('%Y-%m-%d'),
        'today': today,
        'tomorrow': tomorrow,
        'form': form,
        'guest_type': guest_type
    }
    return render(request, 'catalog/home.html', context)



def all_guests(request):
    occupation_events = CustomEvent.objects.filter(event_type='occupancy')

    processed_events = []
    for event in occupation_events:
        event_info = {
            'guest_name': event.guest_name,
            'creator': event.creator,
            'start': event.start,
            'end': event.end,
            'room_info': None,
        }
        if event.calendar.room.owner:
            event_info['room_info'] = f"{event.calendar.room.owner}'s room, {event.calendar.room.section.building}"
        else:
            event_info['room_info'] = f"Room #{event.calendar.room.number}, {event.calendar.room.section.building}"
        processed_events.append(event_info)

    context = {
        'occupation_events': processed_events,
    }
    return render(request, 'catalog/all_guests.html', context)


@login_required
def my_room(request):
  person = request.user.person
    # Using hasattr
  if hasattr(person, 'room'):
    room = person.room
    calendar = room.calendar

    availability_events = CustomEvent.objects.filter(calendar=calendar, event_type='availability').order_by('start')
    occupancy_events = CustomEvent.objects.filter(calendar = calendar, event_type = 'occupancy').order_by('start')

    # Get events for each child
    children = person.children.all()

    children_events = {}
    for child in children:
        child_calendar = Room.objects.filter(owner=child).first().calendar
        child_availability_events = CustomEvent.objects.filter(calendar=child_calendar, event_type='availability').order_by('start')
        child_occupancy_events = CustomEvent.objects.filter(calendar=child_calendar, event_type='occupancy').order_by('start')
        children_events[child] = {
            'availability': child_availability_events,
            'occupancy': child_occupancy_events
        }

    # Get the current local date and the next day's date
    local_now = timezone.localtime(timezone.now())
    tomorrow = local_now.date() + timedelta(days=1)
    dayafter = tomorrow + timedelta(days=1)

    context = {
        'room': room,
        'availability_events': availability_events,
        'occupancy_events': occupancy_events,
        'children_events': children_events,
        'children': children,
        'start_date': tomorrow.strftime('%Y-%m-%d'),
        'end_date': dayafter.strftime('%Y-%m-%d'),
    }
    return render(request, 'catalog/my_room.html', context)
  else:
      return redirect('no_room')




@login_required
def my_guests(request):
    occupation_events = CustomEvent.objects.filter(event_type='occupancy', creator=request.user)

    processed_events = []

    for event in occupation_events:
        event_info = {
            'id': event.id,
            'guest_name': event.guest_name,
            'creator': event.creator,
            'start': event.start,
            'end': event.end,
            'room_info': None,
            'image_url': event.calendar.room.image.url if event.calendar.room.image else '',  # Store the image URL for each event
        }
        print(event_info)
        if event.calendar.room.owner:
            event_info['room_info'] = f"{event.calendar.room.owner}'s room, {event.calendar.room.section.building}"
        else:
            event_info['room_info'] = f"Room #{event.calendar.room.number}, {event.calendar.room.section.building}"
        processed_events.append(event_info)


    context = {
        'occupation_events': processed_events,
    }
    return render(request, 'catalog/my_guests.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser or u.has_perm('app.view_all_rooms'))
def rooms_master(request, user_id=None):
    form = UserSelectForm()

    # Deal with dropdown selection
    # Determine the selected person
    if request.method == 'POST':
        form = UserSelectForm(request.POST)

        if form.is_valid():
          selected_user = form.cleaned_data['user']
          try:
                selected_person = selected_user.person
            
                return redirect('rooms_master_with_user', user_id=selected_user.id)
          except Person.DoesNotExist:
                # Handle case where user does not have an associated person
                return redirect('no_person')  # or render a template with an error message
          
    # load initial page with noone selected
    # or take the redirect after dropdown selection and pass on context
    else:
        selected_person = None
        if user_id:
            user = get_object_or_404(User, id=user_id)
            selected_person = get_object_or_404(Person, user=user)
        
        context = {
            'form': form,
            'selected_person': selected_person,
            'user_id': user_id,
        }
        
        if selected_person and hasattr(selected_person, 'room'):
            room = selected_person.room
            calendar = room.calendar

            availability_events = CustomEvent.objects.filter(calendar=calendar, event_type='availability').order_by('start') if calendar else None
            occupancy_events = CustomEvent.objects.filter(calendar=calendar, event_type='occupancy').order_by('start') if calendar else None

            children = selected_person.children.all()
            children_events = {}

            for child in children:
                child_room = Room.objects.filter(owner=child).first()
                if child_room and child_room.calendar:
                    child_calendar = child_room.calendar
                    child_availability_events = CustomEvent.objects.filter(calendar=child_calendar, event_type='availability').order_by('start')
                    child_occupancy_events = CustomEvent.objects.filter(calendar=child_calendar, event_type='occupancy').order_by('start')
                    children_events[child] = {
                        'availability': child_availability_events,
                        'occupancy': child_occupancy_events,
                        'room_image_url': child_room.image.url if child_room.image else '',

                        
                    }

            local_now = timezone.localtime(timezone.now())
            tomorrow = local_now.date() + timedelta(days=1)
            dayafter = tomorrow + timedelta(days=1)

            context.update({
                'room': room,
                'room_image_url': room.image.url if room.image else '',
                'availability_events': availability_events,
                'occupancy_events': occupancy_events,
                'children_events': children_events,
                'children': children,
                'start_date': tomorrow.strftime('%Y-%m-%d'),
                'end_date': dayafter.strftime('%Y-%m-%d'),
            })

        return render(request, 'catalog/rooms_master.html', context)
    
    
