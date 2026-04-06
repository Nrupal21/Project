"""
Forms for the destinations app.

This module contains forms for creating and updating destinations and attractions.
These forms are used in the guide interface to allow local guides to add
and manage travel destinations and attractions.

The module implements the destination approval workflow:
1. Local guides submit new destinations using PendingDestinationForm
2. Submissions are stored in the PendingDestination table
3. Managers/admins review and can approve or reject submissions
4. Approved submissions are transferred to the main Destination table
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from .models import (
    Destination, Attraction, Region, DestinationImage,
    PendingDestination, PendingDestinationImage
)

class DestinationForm(forms.ModelForm):
    """Form for creating and updating destinations by guides."""
    class Meta:
        model = Destination
        fields = [
            'name', 'region', 'short_description', 'description',
            'latitude', 'longitude', 'city', 'country', 'price', 'is_featured'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'short_description': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'region': forms.Select(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_name(self):
        """Ensure the destination name is unique and generate a slug."""
        name = self.cleaned_data.get('name')
        slug = slugify(name)
        
        if Destination.objects.filter(slug=slug).exists():
            if not self.instance or self.instance.slug != slug:
                raise ValidationError('A destination with this name already exists.')
        
        return name


class AttractionForm(forms.ModelForm):
    """Form for creating and updating attractions by guides."""
    class Meta:
        model = Attraction
        fields = [
            'name', 'destination', 'description', 'category',
            'address', 'city', 'country', 'latitude', 'longitude', 'is_featured'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'destination': forms.Select(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_name(self):
        """Ensure the attraction name is unique within the same destination and generate a slug."""
        name = self.cleaned_data.get('name')
        destination = self.cleaned_data.get('destination')
        slug = slugify(name)
        
        queryset = Attraction.objects.filter(slug=slug, destination=destination)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
            
        if queryset.exists():
            raise ValidationError('An attraction with this name already exists in the selected destination.')
        
        return name


class DestinationImageForm(forms.ModelForm):
    """Form for uploading destination images."""
    class Meta:
        model = DestinationImage
        fields = ['image', 'caption', 'is_primary']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'caption': forms.TextInput(attrs={'class': 'form-control'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PendingDestinationForm(forms.ModelForm):
    """
    Form for local guides to submit new destination proposals.
    
    This form creates entries in the PendingDestination table rather than directly
    creating approved destinations. The submissions go through an approval workflow
    where managers or administrators review them before transfer to the main
    Destination table.
    
    Fields:
        name: The name of the destination
        region: The region this destination belongs to
        short_description: Brief tagline/summary of the destination
        description: Full description with details about the destination
        latitude/longitude: Geographic coordinates for mapping
        city/country: Location information
        price: Estimated cost or price range for visiting
    """
    class Meta:
        model = PendingDestination
        fields = [
            'name', 'region', 'short_description', 'description',
            'latitude', 'longitude', 'city', 'country', 'price'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter destination name'
            }),
            'short_description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief tagline (max 255 characters)'
            }),
            'description': forms.Textarea(attrs={
                'rows': 4, 
                'class': 'form-control',
                'placeholder': 'Detailed description of this destination'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City name'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Country name'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Average cost (optional)'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.000001',
                'placeholder': 'Latitude (decimal format)'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.000001',
                'placeholder': 'Longitude (decimal format)'
            }),
            'region': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_name(self):
        """
        Validate the destination name is unique.
        
        This method checks if a destination with the given name already exists in either
        the PendingDestination or Destination tables to prevent duplicates.
        
        Returns:
            str: The validated destination name
            
        Raises:
            ValidationError: If a destination with this name already exists
        """
        name = self.cleaned_data.get('name')
        slug = slugify(name)
        
        # Check if this name exists in pending destinations
        pending_exists = PendingDestination.objects.filter(slug=slug).exists()
        # Check if this name exists in approved destinations
        destination_exists = Destination.objects.filter(slug=slug).exists()
        
        if pending_exists or destination_exists:
            if not self.instance or (self.instance and self.instance.slug != slug):
                raise ValidationError('A destination with this name already exists or is pending approval.')
        
        return name


class PendingDestinationImageForm(forms.ModelForm):
    """
    Form for uploading images to pending destinations.
    
    This form allows local guides to upload images for their pending destination
    submissions. These images will be transferred to the main DestinationImage
    table if the destination is approved.
    
    Fields:
        image: The image file to upload
        caption: Optional descriptive text for the image
        is_primary: Whether this should be the main/featured image
    """
    class Meta:
        model = PendingDestinationImage
        fields = ['image', 'caption', 'is_primary']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'caption': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief description of this image (optional)'
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
