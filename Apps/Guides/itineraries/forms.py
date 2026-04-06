"""
Forms for the itineraries app.

This module contains form classes for creating and editing itineraries,
itinerary days, and activities. It handles validation, widget customization,
and form behavior for the itineraries management system.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Itinerary, ItineraryDay, Activity
from destinations.models import Destination
from tours.models import Tour

User = get_user_model()


class DateInput(forms.DateInput):
    """
    Custom DateInput widget that uses HTML5 date input type.
    
    This provides a better user experience with a date picker in supported browsers.
    """
    input_type = 'date'


class TimeInput(forms.TimeInput):
    """
    Custom TimeInput widget that uses HTML5 time input type.
    
    This provides a better user experience with a time picker in supported browsers.
    """
    input_type = 'time'


class ItineraryForm(forms.ModelForm):
    """
    Form for creating and editing Itinerary objects.
    
    Provides custom validation and widget customization for a better user experience,
    including date picker widgets and dynamic tour filtering.
    """
    
    class Meta:
        model = Itinerary
        fields = ['title', 'description', 'tour', 'start_date', 'end_date', 'is_public']
        widgets = {
            'start_date': DateInput(),
            'end_date': DateInput(),
            'description': forms.Textarea(attrs={'rows': 4}),
            'tour': forms.Select(attrs={'class': 'select2'}),
        }
        
    def __init__(self, *args, **kwargs):
        """
        Initialize the form with custom attributes.
        
        Sets the current user to associate with the itinerary and configures
        field attributes for better UI/UX.
        """
        self.user = kwargs.pop('user', None)
        super(ItineraryForm, self).__init__(*args, **kwargs)
        
        # Add helpful text to form fields
        self.fields['title'].help_text = _("Give your itinerary a descriptive name")
        self.fields['description'].help_text = _("Brief overview of your travel plan")
        self.fields['tour'].help_text = _("Optional: Link to a specific tour package")
        self.fields['start_date'].help_text = _("When does your trip begin?")
        self.fields['end_date'].help_text = _("When does your trip end?")
        self.fields['is_public'].help_text = _("Allow others to view this itinerary?")
        
        # If we have a tour field, we can filter by available tours
        if 'tour' in self.fields:
            self.fields['tour'].required = False
            self.fields['tour'].empty_label = _("-- No specific tour --")
            
            # If we're editing an existing itinerary, don't filter tours
            if not self.instance.pk:
                # For new itineraries, we could filter tours to only future ones
                today = timezone.now().date()
                self.fields['tour'].queryset = Tour.objects.filter(
                    start_date__gte=today
                ).order_by('start_date')
            
    def clean(self):
        """
        Custom validation for the form.
        
        Validates that end_date is after start_date and ensures other
        business rules are enforced.
        """
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # Check that end date is after start date
        if start_date and end_date and end_date < start_date:
            self.add_error(
                'end_date', 
                _("End date cannot be before start date.")
            )
            
        # Check if dates match tour dates if a tour is selected
        tour = cleaned_data.get('tour')
        if tour and start_date and end_date:
            if start_date < tour.start_date:
                self.add_error(
                    'start_date',
                    _("Start date cannot be before tour start date ({}).").format(
                        tour.start_date.strftime('%Y-%m-%d')
                    )
                )
            if end_date > tour.end_date:
                self.add_error(
                    'end_date',
                    _("End date cannot be after tour end date ({}).").format(
                        tour.end_date.strftime('%Y-%m-%d')
                    )
                )
                
        return cleaned_data
        
    def save(self, commit=True):
        """
        Save the form instance.
        
        Associates the itinerary with the current user if this is a new itinerary.
        """
        itinerary = super().save(commit=False)
        
        # Set the user if this is a new itinerary
        if not itinerary.pk and self.user:
            itinerary.user = self.user
            
        if commit:
            itinerary.save()
            
        return itinerary


class ItineraryDayForm(forms.ModelForm):
    """
    Form for editing individual days in an itinerary.
    
    Allows users to update day-specific details like accommodation,
    notes, and main destination.
    """
    
    class Meta:
        model = ItineraryDay
        fields = ['destination', 'accommodation_details', 'notes']
        widgets = {
            'accommodation_details': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 4}),
            'destination': forms.Select(attrs={'class': 'select2'})
        }
        
    def __init__(self, *args, **kwargs):
        """
        Initialize the form with custom attributes.
        
        Configures destination field to use a searchable dropdown and adds
        help text to fields.
        """
        super(ItineraryDayForm, self).__init__(*args, **kwargs)
        
        # Add helpful text
        self.fields['destination'].help_text = _("Main location for this day")
        self.fields['destination'].required = False
        self.fields['destination'].empty_label = _("-- Select a destination --")
        self.fields['accommodation_details'].help_text = _(
            "Hotel name, address, booking reference, etc."
        )
        self.fields['notes'].help_text = _(
            "Any special considerations for this day"
        )
        
        # Sort destinations alphabetically for easier selection
        self.fields['destination'].queryset = Destination.objects.all().order_by('name')


class ActivityForm(forms.ModelForm):
    """
    Form for creating and editing activities within an itinerary day.
    
    Handles time formatting, validation, and provides a user-friendly interface
    for managing activities.
    """
    
    class Meta:
        model = Activity
        fields = ['title', 'start_time', 'end_time', 'location', 
                 'description', 'cost', 'booking_reference']
        widgets = {
            'start_time': TimeInput(),
            'end_time': TimeInput(),
            'description': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
        
    def __init__(self, *args, **kwargs):
        """
        Initialize the form with custom attributes.
        
        Makes certain fields optional and adds help text to guide users.
        """
        super(ActivityForm, self).__init__(*args, **kwargs)
        
        # Make certain fields optional
        self.fields['start_time'].required = False
        self.fields['end_time'].required = False
        self.fields['location'].required = False
        self.fields['cost'].required = False
        self.fields['booking_reference'].required = False
        self.fields['notes'].required = False
        
        # Add helpful text
        self.fields['title'].help_text = _("Name of the activity")
        self.fields['start_time'].help_text = _("When does this activity begin?")
        self.fields['end_time'].help_text = _("When does this activity end?")
        self.fields['location'].help_text = _("Where will this activity take place?")
        self.fields['description'].help_text = _("Details about the activity")
        self.fields['cost'].help_text = _("Estimated or actual cost (optional)")
        self.fields['booking_reference'].help_text = _(
            "Booking confirmation number or reference (optional)"
        )
        self.fields['notes'].help_text = _("Any additional information (optional)")
        
    def clean(self):
        """
        Custom validation for activity times.
        
        Ensures that if both start and end times are provided, end time is after start time.
        """
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        # Check that end time is after start time if both are provided
        if start_time and end_time and end_time <= start_time:
            self.add_error(
                'end_time',
                _("End time must be after start time.")
            )
            
        return cleaned_data
