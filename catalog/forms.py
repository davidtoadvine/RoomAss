from django import forms
from django.core.validators import MinLengthValidator, MaxLengthValidator
import bleach
from .models import Person, CustomEvent
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
    guest_name = forms.CharField(max_length=20)

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
    
    #  dont think this actually does anything , but it is called in home view
    def clean_guest_type(self):
        guest_type = self.cleaned_data.get('guest_type')
        if not guest_type:
            raise forms.ValidationError("Guest type is required.")
        return guest_type

    def clean(self):
        cleaned_data = super().clean()
        event_type = cleaned_data.get('event_type')  # Assuming you have event_type in form
        guest_type = cleaned_data.get('guest_type')

        if event_type == 'occupancy' and not guest_type:
            self.add_error('guest_type', 'Guest type is required for occupancy events.')

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


class AvailabilityForm(forms.Form):
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