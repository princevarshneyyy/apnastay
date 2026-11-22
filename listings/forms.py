from django import forms
from .models import Listing, ListingImage, Amenity


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)] if data else []
        return result


class ListingForm(forms.ModelForm):
    images = MultipleFileField(
        required=False,
        help_text="Select one or more photos of your property (JPG, PNG, WEBP)."
    )
    cleaning_fee = forms.DecimalField(
        required=False,
        initial=0.00,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Cleaning fee (optional)'})
    )
    amenities = forms.ModelMultipleChoiceField(
        queryset=Amenity.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'amenity-checkbox'})
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    is_featured = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Listing
        fields = [
            'title', 'description', 'property_type', 'address', 'city', 'state', 'country',
            'price_per_night', 'cleaning_fee', 'max_guests', 'bedrooms', 'beds', 'bathrooms',
            'amenities', 'is_active', 'is_featured'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Luxury Sea View Villa in Calangute'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe your property, vibe, highlights, neighborhood...'}),
            'property_type': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full street address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City (e.g. North Goa, Manali, Jaipur)'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State (e.g. Goa, Himachal Pradesh, Rajasthan)'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
            'price_per_night': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Price per night in INR'}),
            'cleaning_fee': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Cleaning fee (optional)'}),
            'max_guests': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'bedrooms': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'beds': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'bathrooms': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'amenities': forms.CheckboxSelectMultiple(attrs={'class': 'amenity-checkbox'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ListingImageForm(forms.ModelForm):
    class Meta:
        model = ListingImage
        fields = ['image', 'caption', 'is_cover']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'caption': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Caption (e.g. Living room, Pool)'}),
            'is_cover': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
