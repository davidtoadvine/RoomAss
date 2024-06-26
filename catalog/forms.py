from django import forms
from django.core.validators import MinLengthValidator, MaxLengthValidator
import bleach
from .models import Person

class BookingForm(forms.Form):
    
    GUEST_TYPE_CHOICES = [
        ('stranger', 'Relatively new / unknown'),
        ('known', 'Well known to Twin Oaks'),
        ('member', 'Twin Oaks member'),
    ]

    room_id = forms.IntegerField(widget=forms.HiddenInput())
    start_date = forms.DateField(widget=forms.HiddenInput())
    end_date = forms.DateField(widget=forms.HiddenInput())
    guest_name = forms.CharField(max_length=100, validators = [MinLengthValidator(1), MaxLengthValidator(100)])
    host_name = forms.CharField(max_length=100, validators = [MinLengthValidator(1), MaxLengthValidator(100)])
    guest_type = forms.ChoiceField(choices=GUEST_TYPE_CHOICES, required=False)

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

class AvailabilityForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    room_id = forms.IntegerField(widget=forms.HiddenInput())

class EditAvailabilityForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    event_id = forms.IntegerField(widget=forms.HiddenInput())


# honestly not sure why this is a model form, guessing it doesn't need to be
class GuestPreferencesForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ['preference']