from catalog.models import Room, CustomEvent, Person
from catalog.forms import  CreateAvailabilityForm, EditAvailabilityForm, DeleteAvailabilityForm, GuestPreferencesForm
from catalog.utils import date_to_aware_datetime, merge_overlapping_events, handle_reassign


from django.shortcuts import  get_object_or_404, redirect, render
from django.http import HttpResponse, HttpResponseForbidden

from django.contrib.auth.decorators import login_required




@login_required
def create_availability(request, room_id):
      if request.method == 'POST':
        form = CreateAvailabilityForm(request.POST)

        redirect_room_id = room_id

        if form.is_valid():
            # Process the form data
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            room_id = form.cleaned_data['room_id']
            room = get_object_or_404(Room, id=room_id)

            if room.is_offline:
              return HttpResponseForbidden("You cannot create availability for an offline room.")

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
                    creator = request.user
                )
            availability_event.save()
            merge_overlapping_events(room.calendar)  # Call the function to handle overlaps

            if request.user.is_superuser:
              return redirect('rooms_master_with_room', room_id = redirect_room_id)
            return redirect('my_room')
        
        # Handle form invalid case
        if request.user.is_superuser:
            return redirect('rooms_master_with_room', room_id=redirect_room_id)
        return redirect('my_room')
        
@login_required
def edit_availability(request, room_id):
    
    if request.method == 'POST':
        form = EditAvailabilityForm(request.POST)
        
        if form.is_valid():
            # Process the form data
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            event_id = form.cleaned_data['event_id']

          # Convert dates to datetime objects with specific time (around noon)
            new_avail_start_date = date_to_aware_datetime(start_date,12,1)
            new_avail_end_date = date_to_aware_datetime(end_date,11,59)

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

          
            ####### Now we deal with any dispruptions to occupation events

            # Filter occupancy events that are within the original availability event's dates
            occupancy_events = CustomEvent.objects.filter(
                calendar=calendar,
                event_type='occupancy',
                start__gte=orig_avail_start_date,
                end__lte=orig_avail_end_date
            ).order_by('start')

            for occ_event in occupancy_events:
              start_date= occ_event.start
              end_date = occ_event.end
              owner = request.user
              full_reassign = False

              #Deal with new end date, new start date, completely delete original occupancy if needed
              if occ_event.end > new_avail_end_date:
                  occ_event.end = new_avail_end_date
                  occ_event.save()
              
                  if new_avail_end_date > occ_event.start:
                    handle_reassign(occ_event, new_avail_end_date, end_date,owner )
                  else:
                    handle_reassign(occ_event, start_date,end_date,owner)
                    full_reassign = True

              if not full_reassign and occ_event.start < new_avail_start_date: 
                  occ_event.start = new_avail_start_date
                  occ_event.save()                

                  if new_avail_start_date < occ_event.end:
                      handle_reassign(occ_event, start_date, new_avail_start_date, owner)
                  else:
                      handle_reassign(occ_event, start_date, end_date,owner)

              if occ_event.start >= occ_event.end:
                  occ_event.delete()

            if request.user.is_superuser:
              return redirect('rooms_master_with_room', room_id = room_id)
            
            return redirect('my_room')  # Redirect to a relevant page after saving
        # Handle form invalid case
        if request.user.is_superuser:
            return redirect('rooms_master_with_room', room_id=room_id)
        return redirect('my_room')
    
    return HttpResponse("Invalid request method", status=405)

@login_required
def delete_availability(request, room_id):
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

            for event in occupancy_events:
                start_date = event.start
                end_date = event.end
                room = event.calendar.room

                owner = 'Twin Oaks'
                if room.owner:
                  owner = room.owner

                handle_reassign(event, start_date, end_date, owner)
                event.delete()

            avail_event.delete()

            if request.user.is_superuser:
                return redirect('rooms_master_with_room', room_id=room_id)
                
            return redirect('my_room')
        
        # Handle form invalid case
        if request.user.is_superuser:
            return redirect('rooms_master_with_room', room_id=room_id)
        return redirect('my_room') 

    return redirect('my_room')


@login_required
def edit_guest_preferences(request, person_id):

    person = get_object_or_404(Person, id=person_id)  # Adjust the model accordingly
    redirect_person = person
    if redirect_person.parent:
      redirect_person = redirect_person.parent
    room_id = redirect_person.room.id

    if request.method == 'POST':
      
        form = GuestPreferencesForm(request.POST, instance=person)
        if form.is_valid():
            form.save()

            if request.user.is_superuser:
              return redirect('rooms_master_with_room', room_id=room_id)
            return redirect('my_room') 
        
    # FIXME unsure if what is below here ever happens
    else:
        form = GuestPreferencesForm(instance=person)
    
    return render(request, 'edit_guest_preferences.html', {'form': form, 'person': person})