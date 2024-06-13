from django.shortcuts import render, get_object_or_404
# Create your views here.
from .models import Room, Building,Section, Person
from datetime import timedelta
from django.utils import timezone
import pytz

def building_list(request):
    buildings = Building.objects.all()
    return render(request, 'catalog/building_list.html', {'buildings': buildings})

def building_detail(request, building_id):
    building = get_object_or_404(Building, pk=building_id)
    return render(request, 'catalog/building_detail.html', {'building': building})

def section_detail(request, section_id):
    section = get_object_or_404(Section, pk=section_id)
    return render(request, 'catalog/section_detail.html', {'section': section})

def room_detail(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    return render(request, 'catalog/room_detail.html', {'room': room})

def home(request):
    rooms = Room.objects.all()

    # Get start and end date from the request's query parameters
    start_date_str = request.POST.get('start_date')
    end_date_str = request.POST.get('end_date')

    # Set default dates to today's date and tomorrow's date at the start and end of the day respectively
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)

    default_start_date = today
    default_end_date = tomorrow

    # Convert the start and end date strings to timezone-aware datetime objects
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

            # Ensure the dates are timezone-aware and convert to UTC
            start_date = timezone.make_aware(datetime.combine(start_date, datetime.min.time()), timezone.get_current_timezone())
            end_date = timezone.make_aware(datetime.combine(end_date, datetime.max.time()), timezone.get_current_timezone())
            start_date = start_date.astimezone(pytz.utc)
            end_date = end_date.astimezone(pytz.utc)
        except ValueError:
            # Use default dates if there's an error in parsing
            start_date = timezone.make_aware(datetime.combine(default_start_date, datetime.min.time()), timezone.get_current_timezone())
            end_date = timezone.make_aware(datetime.combine(default_end_date, datetime.max.time()), timezone.get_current_timezone())
            start_date = start_date.astimezone(pytz.utc)
            end_date = end_date.astimezone(pytz.utc)
    else:
        # Use default dates if query parameters are not provided
        start_date = timezone.make_aware(datetime.combine(default_start_date, datetime.min.time()), timezone.get_current_timezone())
        end_date = timezone.make_aware(datetime.combine(default_end_date, datetime.max.time()), timezone.get_current_timezone())
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
    # Create a temporary availability event
    CustomEvent.objects.create(
        title=f"Temporary Availability for Room {room.number}",
        start=start_date,
        end=end_date,
        calendar=room.calendar,
        event_type='availability'
    )


# def available_rooms(request):
#     start_date = datetime.now()
#     end_date = start_date + timedelta(days=7)  # Example: checking availability for the next week
#     available_rooms = [room for room in Room.objects.all() if room.is_available(start_date, end_date)]
#     return render(request, 'catalog/available_rooms.html', {'available_rooms': available_rooms})