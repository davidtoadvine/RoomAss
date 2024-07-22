#
# Views for creating, editing, deleting Occupancy Events (bookings)
#


from datetime import datetime

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect, reverse

from catalog.forms import CreateBookingForm, ExtendBookingForm, ShortenBookingForm
from catalog.models import CustomEvent, Room
from catalog.utils import ensure_timezone_aware, event_id_to_redirect_room_id

from django.http import JsonResponse

@login_required
def create_booking(request):

    if request.method == 'POST':
        
        form = CreateBookingForm(request.POST)

        if form.is_valid():
            room_id = form.cleaned_data['room_id']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            host_name = form.cleaned_data['host_name']
            room = Room.objects.get(id=room_id)
            host_object = request.user
            guest_type = form.cleaned_data['guest_type']
            guest_name = form.cleaned_data['guest_name']

            # Convert dates to datetime objects with specific time (around noon)
            start_date = datetime.combine(start_date, datetime.min.time()).replace(hour=12, minute=1)
            end_date = datetime.combine(end_date, datetime.min.time()).replace(hour=11, minute=59)

            # Ensure dates are timezone-aware
            start_date = ensure_timezone_aware(start_date)
            end_date = ensure_timezone_aware(end_date)

            if room.is_available(start_date, end_date):

                booking_event = CustomEvent(
                    calendar=room.calendar,
                    event_type='occupancy',
                    start=start_date,
                    end=end_date,
                    title= f"Booking: {guest_name} hosted by {host_name}",
                    description = "Meaningful Description",
                    creator = host_object,
                    guest_type = guest_type,
                    guest_name = guest_name
                )
                booking_event.save()
                
                # Store form data in session
                request.session['start_date'] = str(start_date.date())
                request.session['end_date'] = str(end_date.date())
                request.session['guest_type'] = guest_type
            
                return redirect('available_rooms')
            else:
                return render(request, 'catalog/available_rooms.html', {'error': 'Room is not available'})
        else:
            return render(request, 'catalog/available_rooms.html', {'error': 'Form is invalid', 'form_errors': form.errors})
    return redirect('available_rooms')

@login_required
def delete_booking(request, event_id, section_id = None):
    event = get_object_or_404(CustomEvent, id=event_id)

    room_id = event_id_to_redirect_room_id(event_id)
    
    if request.method == 'POST':
        source_page = request.session.get('source_page', 'my_guests')
        event.delete()
        if source_page == 'rooms_master' and section_id:
              return redirect('rooms_master_with_section', section_id = section_id)
        elif source_page == 'rooms_master':
              return redirect('rooms_master_with_room', room_id = room_id)
        
        return redirect('my_guests')
        # Render a confirmation page for GET request, if needed
    return render(request, 'catalog/delete_booking.html', {'event': event})

from django.http import JsonResponse

@login_required
def extend_booking(request, event_id, section_id=None):
    event = get_object_or_404(CustomEvent, id=event_id)
    redirect_room_id = event_id_to_redirect_room_id(event_id)

    if request.method == 'POST':
        source_page = request.session.get('source_page', 'my_guests')
        form = ExtendBookingForm(request.POST, event=event)
        if form.is_valid():
            new_start_date = form.cleaned_data['start_date']
            new_end_date = form.cleaned_data['end_date']

            # Convert dates to datetime objects with specific time (around noon)
            new_start_date = datetime.combine(new_start_date, datetime.min.time()).replace(hour=12, minute=1)
            new_end_date = datetime.combine(new_end_date, datetime.min.time()).replace(hour=11, minute=59)
            new_start_date = ensure_timezone_aware(new_start_date)
            new_end_date = ensure_timezone_aware(new_end_date)

            room = event.calendar.room

            old_start_date = ensure_timezone_aware(event.start)
            old_end_date = ensure_timezone_aware(event.end)

            conflict = False
            # Update the event dates
            if new_start_date < old_start_date and room.is_available(new_start_date, old_start_date):
                event.start = new_start_date
                event.save()
            elif new_start_date != old_start_date:
                conflict = True

            if new_end_date > old_end_date and room.is_available(old_end_date, new_end_date):
                event.end = new_end_date
                event.save()
            elif new_end_date != old_end_date:
                conflict = True

            if conflict:
                return JsonResponse({
                    'status': 'conflict',
                    'start': event.start,
                    'end': event.end,
                    'redirect_room_id': redirect_room_id,
                    'source_page': source_page
                })

            response_data = {
                'status': 'success',
                'redirect_url': None
            }

            if source_page == 'rooms_master' and section_id:
                response_data['redirect_url'] = reverse('rooms_master_with_section', args=[section_id])
            elif source_page == 'rooms_master':
                response_data['redirect_url'] = reverse('rooms_master_with_room', args=[redirect_room_id])
            else:
                response_data['redirect_url'] = reverse('my_guests')

            return JsonResponse(response_data)

        # If form is invalid, return errors as JSON
        return JsonResponse({
            'status': 'error',
            'errors': form.errors,
        })

    if request.user.is_superuser:
        return redirect('rooms_master_with_room', room_id=redirect_room_id)

    return redirect('my_guests')



@login_required
def shorten_booking(request, event_id, section_id = None):
  print('in Shorten Booking')
  event = get_object_or_404(CustomEvent, id=event_id)
  redirect_room_id = event_id_to_redirect_room_id(event_id)

  if request.method == 'POST':
        print("shorten Booking POST")
        source_page = request.session.get('source_page', 'my_guests')
        form = ShortenBookingForm(request.POST, event=event)

        if form.is_valid():
            print('form valid')
            new_start_date = form.cleaned_data['start_date']
            new_end_date = form.cleaned_data['end_date']


            # Convert dates to datetime objects with specific time (around noon)
            new_start_date = datetime.combine(new_start_date, datetime.min.time()).replace(hour=12, minute=1)
            new_end_date = datetime.combine(new_end_date, datetime.min.time()).replace(hour=11, minute=59)
            new_start_date= ensure_timezone_aware(new_start_date)
            new_end_date=ensure_timezone_aware(new_end_date)
          
            # Fetch the existing event
            event.start = new_start_date
            event.end = new_end_date
            event.save()

            response_data = {
                'status': 'success',
                'redirect_url': None
            }

            if source_page == 'rooms_master' and section_id:
                response_data['redirect_url'] = reverse('rooms_master_with_section', args=[section_id])
            elif source_page == 'rooms_master':
                response_data['redirect_url'] = reverse('rooms_master_with_room', args=[redirect_room_id])
            else:
                response_data['redirect_url'] = reverse('my_guests')

            return JsonResponse(response_data)

        # If form is invalid, return errors as JSON
        response_data = {
            'status': 'error',
            'errors': form.errors,
        }
        return JsonResponse(response_data)


        
  if source_page == 'rooms_master' and section_id:
              return redirect('rooms_master_with_section', section_id = section_id)
  elif source_page == 'rooms_master':
              return redirect('rooms_master_with_room', room_id = redirect_room_id)
  return redirect('my_guests')  # Redirect to the appropriate page if form is not valid


def extend_conflict(request):
    return render(request, 'catalog/extend_conflict.html')