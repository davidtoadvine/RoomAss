from django import forms
from .models import Room

class BookingForm(forms.Form):
    room_id = forms.IntegerField(widget=forms.HiddenInput())
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))