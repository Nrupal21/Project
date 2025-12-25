"""
Restaurant app forms.
Contains forms for restaurant staff authentication, marketing campaigns, and table management.
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import MarketingCampaign, RestaurantTable


class RestaurantLoginForm(AuthenticationForm):
    """
    Custom login form for restaurant staff.
    Extends Django's AuthenticationForm with custom styling.
    
    Fields:
        username: Staff username
        password: Staff password
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition duration-200',
            'placeholder': 'Username'
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition duration-200',
            'placeholder': 'Password'
        })
    )


class MarketingCampaignForm(forms.ModelForm):
    """
    Form for creating and editing marketing campaigns.
    
    Allows restaurant owners to create promotional email campaigns
    with customer targeting and scheduling options.
    
    Fields:
        name: Campaign name for internal reference
        subject: Email subject line
        message: Custom email message content
        target_customers: Customer segment to target
        template: Email template to use
        scheduled_at: When to send the campaign
    """
    
    class Meta:
        model = MarketingCampaign
        fields = ['name', 'subject', 'message', 'target_customers', 'template', 'scheduled_at']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition duration-200',
                'placeholder': 'Enter campaign name (e.g., Weekend Special Offer)'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition duration-200',
                'placeholder': 'Enter email subject (e.g., Special 20% Off This Weekend!)'
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition duration-200',
                'rows': 6,
                'placeholder': 'Write your promotional message here...\n\nExample:\n🎉 Special Weekend Offer! 🎉\n\nGet 20% off on all orders this weekend!\nUse code: WEEKEND20\n\nValid from Friday to Sunday only.'
            }),
            'target_customers': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition duration-200'
            }),
            'template': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition duration-200'
            }),
            'scheduled_at': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition duration-200',
                'type': 'datetime-local'
            })
        }
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the form with custom field configurations.
        
        Sets up help text and field labels for better user experience.
        """
        super().__init__(*args, **kwargs)
        
        # Add help text for better guidance
        self.fields['name'].help_text = 'Internal name to identify this campaign'
        self.fields['subject'].help_text = 'Subject line that customers will see in their email'
        self.fields['message'].help_text = 'Main promotional message content (supports emojis and formatting)'
        self.fields['target_customers'].help_text = 'Choose which customer segment to target'
        self.fields['template'].help_text = 'Email template design to use'
        self.fields['scheduled_at'].help_text = 'Schedule to send later (optional). Leave empty to send immediately.'
        
        # Make scheduled_at optional
        self.fields['scheduled_at'].required = False
        
        # Add field labels
        self.fields['name'].label = 'Campaign Name'
        self.fields['subject'].label = 'Email Subject'
        self.fields['message'].label = 'Promotional Message'
        self.fields['target_customers'].label = 'Target Customers'
        self.fields['template'].label = 'Email Template'
        self.fields['scheduled_at'].label = 'Schedule For Later'
        
        # Add placeholder for scheduled_at
        self.fields['scheduled_at'].widget.attrs['placeholder'] = 'Select date and time (optional)'
    
    def clean_scheduled_at(self):
        """
        Validate the scheduled_at field.
        
        Ensures that scheduled time is in the future if provided.
        
        Returns:
            datetime: Validated scheduled datetime
            
        Raises:
            ValidationError: If scheduled time is in the past
        """
        from django.utils import timezone
        from django.core.exceptions import ValidationError
        
        scheduled_at = self.cleaned_data.get('scheduled_at')
        
        if scheduled_at and scheduled_at <= timezone.now():
            raise ValidationError('Scheduled time must be in the future.')
        
        return scheduled_at
    
    def clean_message(self):
        """
        Validate the message field.
        
        Ensures message has minimum content and removes excessive whitespace.
        
        Returns:
            str: Cleaned message content
            
        Raises:
            ValidationError: If message is too short
        """
        message = self.cleaned_data.get('message')
        
        if message and len(message.strip()) < 10:
            raise ValidationError('Message must be at least 10 characters long.')
        
        return message.strip() if message else ''


class RestaurantTableForm(forms.ModelForm):
    """
    Form for creating and editing restaurant tables.
    
    Allows restaurant owners to create and manage tables with QR codes
    for contactless menu ordering.
    
    Fields:
        table_number: Unique table identifier
        capacity: Number of seats at the table
        is_active: Whether the table is currently active
        location_description: Optional location description
    """
    
    class Meta:
        model = RestaurantTable
        fields = ['table_number', 'capacity', 'is_active', 'location_description']
        widgets = {
            'table_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition duration-200',
                'placeholder': 'e.g., T1, A-5, 101'
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition duration-200',
                'min': '1',
                'max': '20',
                'placeholder': '4'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
            }),
            'location_description': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition duration-200',
                'placeholder': 'e.g., Near window, Corner booth, Patio area'
            })
        }
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the form with custom field configurations.
        
        Sets up help text and field labels for better user experience.
        """
        super().__init__(*args, **kwargs)
        
        # Add help text for better guidance
        self.fields['table_number'].help_text = 'Unique identifier for this table (e.g., T1, A-5, 101)'
        self.fields['capacity'].help_text = 'Maximum number of people this table can accommodate'
        self.fields['is_active'].help_text = 'Inactive tables will not be accessible via QR code'
        self.fields['location_description'].help_text = 'Optional: Describe the table location (e.g., "Near window", "Patio area")'
        
        # Make location_description optional
        self.fields['location_description'].required = False
        
        # Add field labels
        self.fields['table_number'].label = 'Table Number'
        self.fields['capacity'].label = 'Seating Capacity'
        self.fields['is_active'].label = 'Active'
        self.fields['location_description'].label = 'Location Description'
    
    def clean_table_number(self):
        """
        Validate the table_number field.
        
        Ensures table number is unique within the restaurant and follows format rules.
        
        Returns:
            str: Cleaned and validated table number
            
        Raises:
            ValidationError: If table number is invalid or duplicate
        """
        from django.core.exceptions import ValidationError
        
        table_number = self.cleaned_data.get('table_number')
        
        if table_number:
            # Strip whitespace and convert to uppercase for consistency
            table_number = table_number.strip().upper()
            
            # Check for invalid characters
            if not table_number.replace('-', '').replace('_', '').isalnum():
                raise ValidationError('Table number can only contain letters, numbers, hyphens, and underscores.')
            
            # Check length
            if len(table_number) > 20:
                raise ValidationError('Table number must be 20 characters or less.')
            
            if len(table_number) < 1:
                raise ValidationError('Table number is required.')
        
        return table_number
    
    def clean_capacity(self):
        """
        Validate the capacity field.
        
        Ensures capacity is within reasonable range.
        
        Returns:
            int: Validated capacity value
            
        Raises:
            ValidationError: If capacity is out of range
        """
        from django.core.exceptions import ValidationError
        
        capacity = self.cleaned_data.get('capacity')
        
        if capacity is not None:
            if capacity < 1:
                raise ValidationError('Capacity must be at least 1.')
            
            if capacity > 20:
                raise ValidationError('Capacity cannot exceed 20 seats.')
        
        return capacity
