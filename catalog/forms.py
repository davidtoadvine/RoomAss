from django import forms
from django.core.validators import MinLengthValidator, MaxLengthValidator
import bleach
from .models import Person, CustomEvent, Room, Section
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect

###Occupancy Forms###

# book a room
class CreateBookingForm(forms.Form):
    GUEST_TYPE_CHOICES = [
        (1, 'Relatively new to Twin Oaks'),
        (2, 'Well known to Twin Oaks'),
        (3, 'Twin Oaks member'),
    ]
    
    room_id = forms.IntegerField(widget=forms.HiddenInput())
    start_date = forms.DateField(widget=forms.HiddenInput(), error_messages={'invalid': 'Enter a valid date.'})
    end_date = forms.DateField(widget=forms.HiddenInput(), error_messages={'invalid': 'Enter a valid date.'})
    guest_name = forms.CharField(
        max_length=100, 
        validators=[MinLengthValidator(1), MaxLengthValidator(100)],
        error_messages={'required': 'Guest name is required.'}
    )
    host_name = forms.CharField(
        max_length=100, 
        validators=[MinLengthValidator(1), MaxLengthValidator(100)],
        error_messages={'required': 'Host name is required.'}
    )
    guest_type = forms.ChoiceField(
        choices=GUEST_TYPE_CHOICES,
        required=False,
        error_messages={'required': 'Guest type is required.'}
    )



    # sanitizing form inputs to prevent HTML or JS injections
    # cleaned_data starts as just validated, not cleaned
    # is_valid() method in views validates the form input types and then calls clean
    # clean calls all the sub cleans first then does its own stuff

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError('Start date must be before end date.')
        return cleaned_data

    def clean_room_id(self):
           room_id = self.cleaned_data.get('room_id')
           if not Room.objects.filter(id=room_id).exists():
               raise forms.ValidationError('Invalid room ID.')
           return room_id

    def clean_guest_name(self):
        guest_name = self.cleaned_data['guest_name']
        guest_name = bleach.clean(guest_name)
        return guest_name

    def clean_host_name(self):
        host_name = self.cleaned_data['host_name']
        host_name = bleach.clean(host_name)
        return host_name

    def clean_guest_type(self):
        guest_type = self.cleaned_data.get('guest_type')
        if not guest_type:
            raise forms.ValidationError("Guest type is required.")
        return guest_type
  
# for front page input when searching for available guest rooms
class DateRangeForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}),required=True)
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}),required = True)

    GUEST_TYPE_CHOICES = [
        (1, 'Relatively new to Twin Oaks'),
        (2, 'Well known to Twin Oaks'),
        (3, 'Twin Oaks member'),
    ]
    guest_type = forms.ChoiceField(choices=GUEST_TYPE_CHOICES, required=True, initial=2)

    def clean(self):
        cleaned_data = super().clean()
        new_start_date = cleaned_data.get('start_date')
        new_end_date = cleaned_data.get('end_date')

        if new_start_date and new_end_date:
            now = datetime.now().date()
            three_months_later = now + timedelta(days=90)

            if new_start_date < now - timedelta(days=1):
                raise ValidationError("Start date cannot be that far in the past.")
            if new_start_date > new_end_date:
                raise ValidationError("Invalid date range.")
            if new_end_date > three_months_later:
                raise ValidationError("You cannot schedule more than 3 months out.")
            if new_start_date > new_end_date:
                raise ValidationError("Start date cannot be after the end date.")

        return cleaned_data



# for shortening a guest's stay
class ShortenBookingForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    event_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        if not self.event:
            raise ValidationError("Event is required for validation.")

        new_start_date = cleaned_data.get('start_date')
        new_end_date = cleaned_data.get('end_date')

        if new_start_date and new_end_date:
            old_start_date = self.event.start.date()
            old_end_date = self.event.end.date()

            if new_start_date < old_start_date:
                raise ValidationError("New start date cannot be before the original start date.")

            if new_end_date > old_end_date:
                raise ValidationError("New end date cannot be after the original end date.")
            if new_start_date > new_end_date:
                raise ValidationError("Start date cannot be after the end date.")

        return cleaned_data


# for extending a guest's stay
class ExtendBookingForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    event_id = forms.IntegerField(widget=forms.HiddenInput())


    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        if not self.event:
            raise ValidationError("Event is required for validation.")

        new_start_date = cleaned_data.get('start_date')
        new_end_date = cleaned_data.get('end_date')

        if new_start_date and new_end_date:
            old_start_date = self.event.start.date()
            old_end_date = self.event.end.date()

            if new_start_date > old_start_date:
                raise ValidationError("New start date cannot be after the original start date.")

            if new_end_date < old_end_date:
                raise ValidationError("New end date cannot be before the original end date.")

        return cleaned_data


    
# for deleting a booking entirely
class DeleteBookingForm(forms.Form):

    event_id = forms.IntegerField(widget=forms.HiddenInput())
    def clean_event_id(self):
        event_id = self.cleaned_data.get('event_id')
        if not CustomEvent.objects.filter(id=event_id).exists():
            raise ValidationError('Invalid event ID.')
        return event_id


### Availability Forms ###

# forms for members managing their own room
class CreateAvailabilityForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    room_id = forms.IntegerField(widget=forms.HiddenInput())

class EditAvailabilityForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    event_id = forms.IntegerField(widget=forms.HiddenInput())

class DeleteAvailabilityForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    event_id = forms.IntegerField(widget=forms.HiddenInput())

class GuestPreferencesForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ['preference']





### Form for Admin Page ###
class CustomEventForm(forms.ModelForm):
    class Meta:
        model = CustomEvent
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        event_type = cleaned_data.get('event_type')
        guest_name = cleaned_data.get('guest_name')

        # Debug statements
        print(f"Cleaning form: event_type={event_type}, guest_name={guest_name}")

        if event_type == 'occupancy' and not guest_name:
            print("Guest name is required for occupancy events.")
            self.add_error('guest_name', 'Guest name is required for occupancy events.')

        return cleaned_data





### Rooms Master Selection Forms####
class PersonSelectForm(forms.Form):
    person = forms.ModelChoiceField(
        queryset=Person.objects.filter(room__is_offline=False),
        label="Select Room by Owner"
    )
class RoomSelectForm(forms.Form):
    room = forms.ModelChoiceField(
        queryset=Room.objects.filter(owner__isnull=True, is_offline=False),
          label="Select Room without Owner")

class SectionSelectForm(forms.Form):
    section = forms.ModelChoiceField(queryset=Section.objects.all(), label = "Select Rooms by Section")