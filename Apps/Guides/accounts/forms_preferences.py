"""
Preference Form Module.

This module contains forms related to user preferences and settings for 
the TravelGuide application. It handles travel interests, destination preferences,
budget settings and notification preferences.

The forms in this module include comprehensive validation, field customization,
and appropriate styling to match the TravelGuide's UI standards.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import UserProfile, UserPreference

# Define travel interest choices for multi-select fields
TRAVEL_INTEREST_CHOICES = [
    ('adventure', _('Adventure & Outdoor')),
    ('beach', _('Beach & Relaxation')),
    ('cultural', _('Cultural & Heritage')),
    ('food', _('Food & Culinary')),
    ('urban', _('Urban Exploration')),
    ('nature', _('Nature & Wildlife')),
    ('historical', _('Historical Sites')),
    ('nightlife', _('Nightlife & Entertainment')),
    ('romantic', _('Romantic Getaways')),
    ('family', _('Family-Friendly')),
    ('luxury', _('Luxury Travel')),
    ('budget', _('Budget Travel')),
    ('wellness', _('Wellness & Spa')),
    ('sports', _('Sports & Activities')),
    ('photography', _('Photography Spots')),
]

# Budget preference options
BUDGET_CHOICES = [
    ('economy', _('Economy ($ Budget-friendly)')),
    ('moderate', _('Moderate ($$)')),
    ('premium', _('Premium ($$$)')), 
    ('luxury', _('Luxury ($$$$)')),
]

# Accommodation preference options
ACCOMMODATION_CHOICES = [
    ('hostel', _('Hostels')),
    ('budget_hotel', _('Budget Hotels')),
    ('mid_range', _('Mid-Range Hotels')),
    ('luxury_hotel', _('Luxury Hotels')),
    ('resort', _('Resorts')),
    ('vacation_rental', _('Vacation Rentals')),
    ('boutique', _('Boutique Hotels')),
    ('bnb', _('Bed & Breakfasts')),
    ('camping', _('Camping/Glamping')),
]

class PreferencesForm(forms.ModelForm):
    """
    Form for managing a user's travel preferences.
    
    This form allows users to set and update their travel preferences including
    travel interests, budget preferences, and favorite types of destinations.
    These preferences help personalize recommendations across the platform.
    """
    # Multi-select field for travel interests with custom styling
    travel_interests = forms.MultipleChoiceField(
        choices=TRAVEL_INTEREST_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'grid grid-cols-2 gap-2',
        }),
        required=False,
        help_text=_('Select all travel types that interest you')
    )
    
    # Budget preference selector
    budget_preference = forms.ChoiceField(
        choices=BUDGET_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-radio text-indigo-600',
        }),
        required=False,
        help_text=_('Choose your typical travel budget range')
    )
    
    # Accommodation preferences
    accommodation_preferences = forms.MultipleChoiceField(
        choices=ACCOMMODATION_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'grid grid-cols-2 gap-2',
        }),
        required=False,
        help_text=_('Select your preferred accommodation types')
    )
    
    # Trip duration preferences
    min_trip_days = forms.IntegerField(
        min_value=1,
        max_value=30,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-input block w-full sm:text-sm rounded-md',
            'placeholder': '3'
        }),
        help_text=_('Minimum number of days for your typical trip')
    )
    
    max_trip_days = forms.IntegerField(
        min_value=1,
        max_value=90,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-input block w-full sm:text-sm rounded-md',
            'placeholder': '14'
        }),
        help_text=_('Maximum number of days for your typical trip')
    )
    
    # Preferred continents/regions
    preferred_regions = forms.MultipleChoiceField(
        choices=[
            ('europe', _('Europe')),
            ('north_america', _('North America')),
            ('south_america', _('South America')),
            ('asia', _('Asia')),
            ('africa', _('Africa')),
            ('oceania', _('Oceania')),
            ('antarctica', _('Antarctica')),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'grid grid-cols-2 gap-2',
        }),
        required=False,
        help_text=_('Select regions you are interested in visiting')
    )
    
    # Special requirements or accessibility needs
    special_requirements = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-textarea block w-full sm:text-sm rounded-md',
            'rows': 3,
            'placeholder': _('Any special requirements or accessibility needs...')
        }),
        required=False,
        help_text=_('Let us know if you have any special requirements or accessibility needs')
    )

    class Meta:
        """
        Meta configuration for the PreferencesForm.
        
        Defines the model, fields to include, and additional customization.
        """
        model = UserPreference
        fields = [
            'travel_interests', 
            'budget_preference',
            'accommodation_preferences',
            'min_trip_days',
            'max_trip_days',
            'preferred_regions',
            'special_requirements'
        ]
    
    def clean(self):
        """
        Validate the form data as a whole.
        
        Performs cross-field validation to ensure data consistency.
        For example, ensures min_trip_days is less than max_trip_days.
        
        Returns:
            dict: The cleaned form data
        
        Raises:
            ValidationError: If validation fails
        """
        cleaned_data = super().clean()
        min_days = cleaned_data.get('min_trip_days')
        max_days = cleaned_data.get('max_trip_days')
        
        # Validate trip duration range if both fields are provided
        if min_days and max_days and min_days > max_days:
            raise ValidationError({
                'min_trip_days': _('Minimum trip duration cannot be greater than maximum')
            })
            
        return cleaned_data
    
    def save(self, commit=True):
        """
        Save the form data to the database.
        
        This method overrides the default save to properly handle the
        JSON fields in the UserPreference model.
        
        Args:
            commit (bool): Whether to save the instance to the database
            
        Returns:
            UserPreference: The saved UserPreference instance
        """
        instance = super().save(commit=False)
        
        # Convert form data to appropriate JSON structure
        if self.cleaned_data.get('travel_interests'):
            instance.travel_interests = self.cleaned_data['travel_interests']
            
        # Create preferred destinations dictionary if not already exists
        if not instance.preferred_destinations:
            instance.preferred_destinations = {}
            
        # Add regions to preferred destinations
        if self.cleaned_data.get('preferred_regions'):
            instance.preferred_destinations['regions'] = self.cleaned_data['preferred_regions']
            
        # Add accommodation preferences to preferences
        if self.cleaned_data.get('accommodation_preferences'):
            if not isinstance(instance.preferred_destinations, dict):
                instance.preferred_destinations = {}
            instance.preferred_destinations['accommodations'] = self.cleaned_data['accommodation_preferences']
        
        # Save the trip duration preferences
        if self.cleaned_data.get('min_trip_days') or self.cleaned_data.get('max_trip_days'):
            if not isinstance(instance.preferred_destinations, dict):
                instance.preferred_destinations = {}
                
            instance.preferred_destinations['trip_duration'] = {
                'min': self.cleaned_data.get('min_trip_days'),
                'max': self.cleaned_data.get('max_trip_days')
            }
            
        # Save special requirements
        if self.cleaned_data.get('special_requirements'):
            if not isinstance(instance.preferred_destinations, dict):
                instance.preferred_destinations = {}
                
            instance.preferred_destinations['special_requirements'] = self.cleaned_data['special_requirements']
        
        if commit:
            instance.save()
            
        return instance


class NotificationPreferencesForm(forms.ModelForm):
    """
    Form for managing user notification preferences.
    
    This form allows users to control what types of notifications and
    communications they receive from the TravelGuide platform.
    """
    # Email subscription settings
    newsletter_subscription = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox h-5 w-5 text-indigo-600',
        }),
        help_text=_('Receive our monthly newsletter with travel tips and deals')
    )
    
    email_notifications = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox h-5 w-5 text-indigo-600',
        }),
        help_text=_('Receive email notifications for account activity and bookings')
    )
    
    # Marketing preferences
    marketing_emails = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox h-5 w-5 text-indigo-600',
        }),
        help_text=_('Receive special offers and promotions')
    )
    
    # New destination alerts
    new_destination_alerts = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox h-5 w-5 text-indigo-600',
        }),
        help_text=_('Alerts when new destinations matching your preferences are added')
    )
    
    # Deal alerts
    deal_alerts = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox h-5 w-5 text-indigo-600',
        }),
        help_text=_('Alerts for special deals on your favorite destinations')
    )
    
    # Communication frequency preference
    communication_frequency = forms.ChoiceField(
        choices=[
            ('daily', _('Daily')),
            ('weekly', _('Weekly')),
            ('biweekly', _('Bi-weekly')),
            ('monthly', _('Monthly')),
            ('quarterly', _('Quarterly')),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'form-radio text-indigo-600',
        }),
        required=False,
        help_text=_('Preferred frequency for non-essential communications')
    )

    class Meta:
        """
        Meta configuration for the NotificationPreferencesForm.
        
        Defines the model, fields to include, and additional customization.
        """
        model = UserProfile
        fields = [
            'newsletter_subscription',
            'email_notifications',
        ]
        
    def __init__(self, *args, **kwargs):
        """
        Initialize the NotificationPreferencesForm.
        
        Sets up initial values for custom fields that may not be in the model
        but are stored in other data structures.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        super().__init__(*args, **kwargs)
        
        # Set initial values for fields not directly mapped to model fields
        instance = kwargs.get('instance')
        if instance:
            # If we have a user profile instance, try to get additional settings
            # from related models or JSON fields
            
            # Get user preferences if they exist
            try:
                user_prefs = instance.user.preferences
                if user_prefs and hasattr(user_prefs, 'preferred_destinations'):
                    prefs_dict = user_prefs.preferred_destinations or {}
                    
                    # Extract notification settings from preferences if they exist
                    notification_settings = prefs_dict.get('notification_settings', {})
                    
                    # Set initial values based on stored preferences
                    self.fields['marketing_emails'].initial = notification_settings.get('marketing_emails', False)
                    self.fields['new_destination_alerts'].initial = notification_settings.get('new_destination_alerts', False)
                    self.fields['deal_alerts'].initial = notification_settings.get('deal_alerts', False)
                    self.fields['communication_frequency'].initial = notification_settings.get('communication_frequency', 'monthly')
            except (AttributeError, UserPreference.DoesNotExist):
                # If preferences don't exist, use default values
                pass
    
    def save(self, commit=True):
        """
        Save the notification preferences to the database.
        
        This method saves both direct model fields and custom notification
        preferences that may be stored in JSON fields on related models.
        
        Args:
            commit (bool): Whether to save the instance to the database
            
        Returns:
            UserProfile: The saved UserProfile instance
        """
        # Save fields directly mapped to the UserProfile model
        profile = super().save(commit=False)
        
        # Get or create user preferences to store additional fields
        try:
            preferences, created = UserPreference.objects.get_or_create(user=profile.user)
            
            # Initialize preferred_destinations if needed
            if not preferences.preferred_destinations or not isinstance(preferences.preferred_destinations, dict):
                preferences.preferred_destinations = {}
                
            # Create or update notification_settings
            notification_settings = preferences.preferred_destinations.get('notification_settings', {})
            
            # Update settings with form data
            notification_settings.update({
                'marketing_emails': self.cleaned_data.get('marketing_emails', False),
                'new_destination_alerts': self.cleaned_data.get('new_destination_alerts', False),
                'deal_alerts': self.cleaned_data.get('deal_alerts', False),
                'communication_frequency': self.cleaned_data.get('communication_frequency', 'monthly')
            })
            
            # Save updated settings back to preferences
            preferences.preferred_destinations['notification_settings'] = notification_settings
            
            if commit:
                profile.save()
                preferences.save()
        except Exception as e:
            # Log the error but continue with saving the profile
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error saving notification preferences: {str(e)}")
        
        if commit:
            profile.save()
            
        return profile
