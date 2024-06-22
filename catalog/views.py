from django.shortcuts import render, get_object_or_404, redirect
# Create your views here.
from .models import Room, Building, Section, Person

from datetime import timedelta, time
from django.utils import timezone
import pytz
from .forms import BookingForm, AvailabilityForm


def building_list(request):
    buildings = Building.objects.all()
    return render(request, 'catalog/building_list.html', {'buildings': buildings})

def building_detail(request, building_id):
    building = get_object_or_404(Building, pk=building_id)
    return render(request, 'catalog/building_detail.html', {'building': building})

def section_detail(request, section_id):
    section = get_object_or_404(Section, pk=section_id)
    return render(request, 'catalog/section_detail.html', {'section': section})

def create_availability(request):
      if request.method == 'POST':
        form = AvailabilityForm(request.POST)
        if form.is_valid():
            # Process the form data
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            room_id = form.cleaned_data['room_id']
            room = get_object_or_404(Room, id=room_id)

            # Convert dates to datetime objects with specific time (noon)
            start_date = datetime.combine(start_date, datetime.min.time()).replace(hour=12, minute=1)
            end_date = datetime.combine(end_date, datetime.min.time()).replace(hour=11, minute=59)

            # Ensure dates are timezone-aware
            if timezone.is_naive(start_date):
                start_date = timezone.make_aware(start_date, timezone.get_current_timezone())
            if timezone.is_naive(end_date):
                end_date = timezone.make_aware(end_date, timezone.get_current_timezone())

            availability_event = CustomEvent(
                    calendar=room.calendar,
                    event_type='availability',
                    start=start_date,
                    end=end_date,
                    title= f"Availability: Meaningful Title from My Room Form",
                    description = "Meaningful Description",
                    creator = room.owner.user
                )
            availability_event.save()
            
            return redirect('my_room')

def my_room(request):
    person = request.user.person
    room = person.room
    calendar = room.calendar

    availability_events = CustomEvent.objects.filter(calendar=calendar, event_type='availability')
    occupancy_events = CustomEvent.objects.filter(calendar = calendar, event_type = 'occupancy')

    # Get events for each child
    children = person.children.all()

    children_events = {}
    for child in children:
        child_calendar = Room.objects.filter(owner=child).first().calendar
        child_availability_events = CustomEvent.objects.filter(calendar=child_calendar, event_type='availability')
        child_occupancy_events = CustomEvent.objects.filter(calendar=child_calendar, event_type='occupancy')
        children_events[child] = {
            'availability': child_availability_events,
            'occupancy': child_occupancy_events
        }

    context = {
        'room': room,
        'availability_events': availability_events,
        'occupancy_events': occupancy_events,
        'children_events': children_events,
        'children': children
    }
    return render(request, 'catalog/my_room.html', context)

def home(request):
    rooms = Room.objects.select_related('section__building').order_by('section__building__name', 'section__name', 'number')
        # Get start and end date from the request
    start_date_str = request.POST.get('start_date')
    end_date_str = request.POST.get('end_date')

    # Specific times of day. Need booking start time to be 'in the future', so placing it at
    # the end of any given day ensures a room won't be prematurely excluded from
    # availability list. 
    start_time = time(23, 59)  # 11:59 PM
    end_time = time(11, 59)   # 11:59 AM

    # Get the current local date and the next day's date
    local_now = timezone.localtime(timezone.now())
    today = local_now.date()
    tomorrow = today + timedelta(days=1)

    default_start_date = today
    default_end_date = tomorrow

    # Convert the start and end date strings to timezone-aware datetime objects
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

            # Ensure the dates are timezone-aware and convert to UTC
            start_date = timezone.make_aware(datetime.combine(start_date, start_time), timezone.get_current_timezone())
            end_date = timezone.make_aware(datetime.combine(end_date, end_time), timezone.get_current_timezone())
            start_date = start_date.astimezone(pytz.utc)
            end_date = end_date.astimezone(pytz.utc)
        except ValueError:
            # Use default dates if there's an error in parsing
            start_date = timezone.make_aware(datetime.combine(default_start_date, start_time), timezone.get_current_timezone())
            end_date = timezone.make_aware(datetime.combine(default_end_date, end_time), timezone.get_current_timezone())
            start_date = start_date.astimezone(pytz.utc)
            end_date = end_date.astimezone(pytz.utc)
    else:
        # Use default dates if query parameters are not provided
        start_date = timezone.make_aware(datetime.combine(default_start_date, start_time), timezone.get_current_timezone())
        end_date = timezone.make_aware(datetime.combine(default_end_date, end_time), timezone.get_current_timezone())
        start_date = start_date.astimezone(pytz.utc)
        end_date = end_date.astimezone(pytz.utc)

    available_rooms_info = []
    for room in rooms:
        if room.is_available(start_date, end_date):
            potential_end_date = room.get_last_available_date(start_date)
            available_rooms_info.append((room, potential_end_date))

    context = {
        'available_rooms_info': available_rooms_info,
        'start_date': start_date_str if start_date_str else today.strftime('%Y-%m-%d'),
        'end_date': end_date_str if end_date_str else tomorrow.strftime('%Y-%m-%d'),
        'today': today,
        'tomorrow': tomorrow,
        'form': BookingForm(),
    }
    return render(request, 'catalog/home.html', context)

def person_detail(request, person_id):
    person = get_object_or_404(Person, pk=person_id)
    room = person.room
    section = room.section if room else None
    building = section.building if section else None
    return render(request, 'catalog/person_detail.html', {
        'person': person,
        'room': room,
        'section': section,
        'building': building
    })

from datetime import datetime, timedelta
from .models import CustomEvent, Room, Person

def assign_owner(room, person):
    room.owner = person
    room.save()


def make_room_temporarily_available(room, start_date, end_date):
    
    #need to make time zone aware!

    # Create a temporary availability event
    CustomEvent.objects.create(
        title=f"Temporary Availability for Room {room.number}",
        start=start_date,
        end=end_date,
        calendar=room.calendar,
        event_type='availability'
    )
def create_booking(request):

    if request.method == 'POST':
        form = BookingForm(request.POST)

        if form.is_valid():
            room_id = form.cleaned_data['room_id']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            guest = form.cleaned_data['guest_name']
            host_name = form.cleaned_data['host_name']
            room = Room.objects.get(id=room_id)
            host_object = request.user

            # Convert dates to datetime objects with specific time (noon)
            start_date = datetime.combine(start_date, datetime.min.time()).replace(hour=12, minute=1)
            end_date = datetime.combine(end_date, datetime.min.time()).replace(hour=11, minute=59)

            # Ensure dates are timezone-aware
            if timezone.is_naive(start_date):
                start_date = timezone.make_aware(start_date, timezone.get_current_timezone())
            if timezone.is_naive(end_date):
                end_date = timezone.make_aware(end_date, timezone.get_current_timezone())

            if room.is_available(start_date, end_date):
                booking_event = CustomEvent(
                    calendar=room.calendar,
                    event_type='occupancy',
                    start=start_date,
                    end=end_date,
                    title= f"Booking: {guest} hosted by {host_name}",
                    description = "Meaningful Description",
                    creator = host_object
                )
                booking_event.save()
                return redirect('home')
            else:
                return render(request, 'catalog/home.html', {'error': 'Room is not available'})
        else:
            print(form.errors)  # Print form errors to the console for debugging
            return render(request, 'catalog/home.html', {'error': 'Form is invalid', 'form_errors': form.errors})
    return redirect('home')
