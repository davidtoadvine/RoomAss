from .models import Room, Building, Section, Person, CustomEvent
from .forms import BookingForm, AvailabilityForm, EditAvailabilityForm, GuestPreferencesForm, DateRangeForm, DeleteAvailabilityForm

from datetime import timedelta, time
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse


def create_availability(request):
      if request.method == 'POST':
        form = AvailabilityForm(request.POST)

        if form.is_valid():
            # Process the form data
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            room_id = form.cleaned_data['room_id']
            room = get_object_or_404(Room, id=room_id)

            # Make timezone aware datetime object with time of day
            start_date = date_to_aware_datetime(start_date, 11,59)
            end_date = date_to_aware_datetime(end_date, 12,1)

            availability_event = CustomEvent(
                    calendar=room.calendar,
                    event_type='availability',
                    start=start_date,
                    end=end_date,
                    title= f"Availability, {request.user}",
                    description = "Meaningful Description",
                    creator = room.owner.user
                )
            availability_event.save()
            merge_overlapping_events(room.calendar)  # Call the function to handle overlaps

            return redirect('my_room')
        
        else:
            return redirect('my_room')

def edit_availability(request):
    if request.method == 'POST':
        form = EditAvailabilityForm(request.POST)
        
        if form.is_valid():
            # Process the form data
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            event_id = form.cleaned_data['event_id']

          # Convert dates to datetime objects with specific time (around noon)
          
            new_avail_start_date = date_to_aware_datetime(start_date,11,59)
       

            
            new_avail_end_date = date_to_aware_datetime(end_date,12,1)
     


            # Fetch the existing event
            avail_event = get_object_or_404(CustomEvent, id=event_id)
            calendar = avail_event.calendar

            # Original availability event's start and end dates
            orig_avail_start_date = avail_event.start
            orig_avail_end_date = avail_event.end

            # Update the availability event with new dates
            avail_event.start = new_avail_start_date
            avail_event.end = new_avail_end_date
            avail_event.title = f"Availability, {request.user}"
            avail_event.description = "CHANGED"
            avail_event.creator = request.user  # Update creator if needed

            avail_event.save()
            merge_overlapping_events(avail_event.calendar)  # Call the function to handle overlaps
   
            #######
            ####### Now we deal with any dispruptions occupation events
            #######

            # Filter occupancy events that are within the original availability event's dates
            occupancy_events = CustomEvent.objects.filter(
                calendar=calendar,
                event_type='occupancy',
                start__gte=orig_avail_start_date,
                end__lte=orig_avail_end_date
            ).order_by('start')


            rooms = Room.objects.select_related('section__building').order_by('section__building__name', 'section__name', 'number')

            for occ_event in occupancy_events:
            
              guest_type = occ_event.guest_type
              start_date= occ_event.start
              end_date = occ_event.end
              ############
              # if there has been an infringement
              ##############
              # deal with end overlap
              if occ_event.end > new_avail_end_date:
                  print("end date conflict seen")
                  occ_event.end = new_avail_end_date

                  for room in rooms:
                    
                    if (    (room.is_available(new_avail_end_date, end_date))
                            and
                            ((room.owner and int(guest_type) >= int(room.owner.preference))
                            or
                            (not room.owner))):
                        

                            occ_event.end = new_avail_end_date
                            occ_event.save()
                            create_stopgap_booking(room, occ_event, new_avail_end_date, end_date, occ_event.guest_type, occ_event.guest_name)
                            event_assigned = True
                            break
                        
                            
                  if not event_assigned:
                    print(f"Event {occ_event.id} (front portion) could not be assigned to any room.")
              ################          
              # deal with start overlap
              if occ_event.start < new_avail_start_date:
                  occ_event.start = new_avail_start_date

                  for room in rooms:
                    if (  (room.is_available(start_date, new_avail_start_date))
                            and
                            ((room.owner and int(guest_type) >= int(room.owner.preference))
                            or
                            (not room.owner))):
                              
                              occ_event.start = new_avail_start_date
                              occ_event.save()
                              create_stopgap_booking(room, occ_event, start_date, new_avail_start_date, occ_event.guest_type, occ_event.guest_name)
                              event_assigned = True

                              break
                    
                  if not event_assigned:
                    print(f"Event {occ_event.id} could not be assigned to any room.")

            return redirect('my_room')  # Redirect to a relevant page after saving
        else:
            # Log form errors for debugging
            print(form.errors)
            return redirect('my_room')  # Redirect to a relevant page after saving
    
    return HttpResponse("Invalid request method", status=405)




def delete_availability(request):
    if request.method == 'POST':
        form = DeleteAvailabilityForm(request.POST)
        
        if form.is_valid():
            event_id = form.cleaned_data['event_id']
            avail_event = get_object_or_404(CustomEvent, id=event_id)
            calendar = avail_event.calendar
  
          # Original availability event's start and end dates
            avail_start_date = avail_event.start
            avail_end_date = avail_event.end

            # Filter occupancy events that are within the original availability event's dates
            occupancy_events = CustomEvent.objects.filter(
                calendar=calendar,
                event_type='occupancy',
                start__gte=avail_start_date,
                end__lte=avail_end_date
            ).order_by('start')


            rooms = Room.objects.select_related('section__building').order_by('section__building__name', 'section__name', 'number')

            for event in occupancy_events:
          
              guest_type = event.guest_type
              start_date= event.start
              end_date = event.end

              for room in rooms:
                if room.owner:
                    if int(guest_type) >= int(room.owner.preference):
                        if room.is_available(start_date, end_date):
                            event.calendar = room.calendar
                            event.save()
                            event_assigned = True
                            break
                else:
                    if room.is_available(start_date, end_date):
                        event.calendar = room.calendar
                        event.save()
                        event_assigned = True
                        break

              if not event_assigned:
                print(f"Event {event.id} could not be assigned to any room.")


        avail_event.delete()
            # Redirect to a success page or the same page
        return redirect('my_room')  # R

    return redirect('my_room') 

        






def my_room(request):
    person = request.user.person
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
          
          if room.owner:
            if int(guest_type) >= int(room.owner.preference):
              if room.is_available(start_date, end_date) :
                potential_end_date = room.get_last_available_date(start_date)
                available_rooms_info.append((room, potential_end_date))
          else:      
              if room.is_available(start_date, end_date) :
                potential_end_date = room.get_last_available_date(start_date)
                available_rooms_info.append((room, potential_end_date))

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


def create_booking(request):

    if request.method == 'POST':
        form = BookingForm(request.POST)

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
            
                return redirect('home')
            else:
                return render(request, 'catalog/home.html', {'error': 'Room is not available'})
        else:
            return render(request, 'catalog/home.html', {'error': 'Form is invalid', 'form_errors': form.errors})
    return redirect('home')






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






def edit_guest_preferences(request, person_id):

    person = get_object_or_404(Person, id=person_id)  # Adjust the model accordingly

    if request.method == 'POST':
      
        form = GuestPreferencesForm(request.POST, instance=person)
        if form.is_valid():
            form.save()
            return redirect('my_room')  # Adjust to your actual redirect view
    else:
        form = GuestPreferencesForm(instance=person)
    
    return render(request, 'edit_guest_preferences.html', {'form': form, 'person': person})





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








def date_to_aware_datetime(date, hour, minute ):
    # Convert dates to datetime objects with specific time (around noon)
            if isinstance(date, datetime):
                date = date.replace(hour=hour, minute=minute)
            else:
                date = datetime.combine(date, time(hour, minute))
            return ensure_timezone_aware(date)

def ensure_timezone_aware(date):
  if timezone.is_naive(date):
                return timezone.make_aware(date, timezone.get_current_timezone())
  return date