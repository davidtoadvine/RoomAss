from django import forms
from django.core.validators import MinLengthValidator, MaxLengthValidator
import bleach

class BookingForm(forms.Form):
    room_id = forms.IntegerField(widget=forms.HiddenInput())
    start_date = forms.DateField(widget=forms.HiddenInput())
    end_date = forms.DateField(widget=forms.HiddenInput())
    guest_name = forms.CharField(max_length=100, validators = [MinLengthValidator(1), MaxLengthValidator(100)])
    host_name = forms.CharField(max_length=100, validators = [MinLengthValidator(1), MaxLengthValidator(100)])

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