from django import forms
from django.core.validators import MinLengthValidator, MaxLengthValidator
import bleach
from .models import Person, CustomEvent, Room, Section
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone
class BookingForm(forms.Form):
    
    GUEST_TYPE_CHOICES = [
        (1, 'Relatively new to Twin Oaks'),
        (2, 'Well known to Twin Oaks'),
        (3, 'Twin Oaks member'),
    ]
    room_id = forms.IntegerField(widget=forms.HiddenInput())
    start_date = forms.DateField(widget=forms.HiddenInput())
    end_date = forms.DateField(widget=forms.HiddenInput())
    guest_name = forms.CharField(max_length=100, validators = [MinLengthValidator(1), MaxLengthValidator(100)])
    host_name = forms.CharField(max_length=100, validators = [MinLengthValidator(1), MaxLengthValidator(100)])
    guest_type = forms.ChoiceField(choices=GUEST_TYPE_CHOICES, required=False)

    def clean_room_id(self):
        room_id = self.cleaned_data.get('room_id')
        if not Room.objects.filter(id=room_id).exists():
            raise forms.ValidationError('Invalid room ID.')
        return room_id

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError('Start date must be before end date.')

        return cleaned_data

    def clean_guest_name(self):
        guest_name = self.cleaned_data['guest_name']
        # Sanitize input using bleach
        guest_name = bleach.clean(guest_name)
        return guest_name

    def clean_host_name(self):
        host_name = self.cleaned_data['host_name']
        # Sanitize input using bleach
        host_name = bleach.clean(host_name)
        return host_name
    
    #  dont think this actually does anything , but it is called in available_rooms view
    def clean_guest_type(self):
        guest_type = self.cleaned_data.get('guest_type')
        if not guest_type:
            raise forms.ValidationError("Guest type is required.")
        return guest_type

  

        return cleaned_data
class DateRangeForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    GUEST_TYPE_CHOICES = [
        (1, 'Relatively new to Twin Oaks'),
        (2, 'Well known to Twin Oaks'),
        (3, 'Twin Oaks member'),
    ]
    guest_type = forms.ChoiceField(choices=GUEST_TYPE_CHOICES, required=True, initial=2)

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            now = datetime.now().date()
            three_months_later = now + timedelta(days=90)

            if start_date < now - timedelta(days=1):
                raise ValidationError("Start date cannot be that far in the past.")
            if start_date > end_date:
                raise ValidationError("Invalid date range.")
            if end_date > three_months_later:
                raise ValidationError("You cannot schedule more than 3 months out.")

        return cleaned_data

class CreateAvailabilityForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    room_id = forms.IntegerField(widget=forms.HiddenInput())

class EditAvailabilityForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    event_id = forms.IntegerField(widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = super().clean()
        event_id = cleaned_data.get('event_id')
        new_start_date = cleaned_data.get('start_date')
        new_end_date = cleaned_data.get('end_date')

        # Fetch the existing event
        event = CustomEvent.objects.get(id=event_id)

        # if new_start_date and new_end_date:
        #     # Ensure the new dates are within the old limits
        #     if new_start_date < event.start.date() or new_end_date > event.end.date():
        #         raise ValidationError("The new dates must be within the original booking dates.")

        return cleaned_data

    def ensure_timezone_aware(date):
        if timezone.is_naive(date):
            return timezone.make_aware(date, timezone.get_current_timezone())
        return date

class DeleteAvailabilityForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    event_id = forms.IntegerField(widget=forms.HiddenInput())
# honestly not sure why this is a model form, guessing it doesn't need to be
class GuestPreferencesForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ['preference']

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