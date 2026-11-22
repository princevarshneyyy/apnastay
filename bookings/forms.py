from django import forms
from django.utils import timezone
from .models import Booking
import datetime


class BookingForm(forms.ModelForm):
    check_in = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'min': timezone.now().date().isoformat(),
            'id': 'booking_check_in'
        })
    )
    check_out = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'min': (timezone.now().date() + datetime.timedelta(days=1)).isoformat(),
            'id': 'booking_check_out'
        })
    )
    guests_count = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'id': 'booking_guests_count'
        })
    )
    special_requests = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any special requirements or arrival timing? (Optional)'
        })
    )

    class Meta:
        model = Booking
        fields = ['check_in', 'check_out', 'guests_count', 'special_requests']

    def __init__(self, *args, listing=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.listing = listing
        if listing:
            self.fields['guests_count'].widget.attrs['max'] = str(listing.max_guests)
            self.fields['guests_count'].initial = 1

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')
        guests_count = cleaned_data.get('guests_count')
        today = timezone.now().date()

        if check_in and check_out:
            if check_out <= check_in:
                self.add_error('check_out', "Check-out date must be after the check-in date.")

            if check_in < today:
                self.add_error('check_in', "Check-in date cannot be in the past.")

        if self.listing and guests_count:
            if guests_count > self.listing.max_guests:
                self.add_error('guests_count', f"This property accommodates up to {self.listing.max_guests} guests.")

        return cleaned_data
