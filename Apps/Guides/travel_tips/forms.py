"""
Forms for the travel_tips app.

This module contains all the form classes used for creating and editing
travel tips and related models.
"""

from django import forms
from django.forms import ModelForm, Textarea, TextInput, FileInput, Select, CheckboxInput
from .models import TravelTip, TravelTipComment, TravelTipCategory


class TravelTipForm(forms.ModelForm):
    """
    Form for creating and updating travel tips.
    
    Includes validation and custom widgets for better user experience.
    """
    class Meta:
        model = TravelTip
        fields = [
            'title', 'category', 'content', 'excerpt', 
            'featured_image', 'status', 'is_featured'
        ]
        widgets = {
            'title': TextInput(attrs={
                'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'placeholder': 'Enter a descriptive title for your tip'
            }),
            'content': Textarea(attrs={
                'class': 'form-textarea mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'rows': 10,
                'placeholder': 'Write your travel tip here. Markdown is supported.'
            }),
            'excerpt': Textarea(attrs={
                'class': 'form-textarea mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'rows': 3,
                'placeholder': 'A brief summary of your tip (optional)'
            }),
            'featured_image': FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100',
            }),
            'category': Select(attrs={
                'class': 'form-select mt-1 block w-full rounded-md border-gray-300 shadow-sm',
            }),
            'status': Select(attrs={
                'class': 'form-select mt-1 block w-full rounded-md border-gray-300 shadow-sm',
            }),
            'is_featured': CheckboxInput(attrs={
                'class': 'form-checkbox h-5 w-5 text-indigo-600',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        """Initialize the form with customizations."""
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Only show published categories in the dropdown
        self.fields['category'].queryset = TravelTipCategory.objects.all().order_by('name')
        
        # Only staff can change the featured status
        if not (user and user.is_staff):
            del self.fields['is_featured']
        
        # Only show draft/published status for non-staff
        if not (user and user.is_staff):
            self.fields['status'].choices = [
                choice for choice in self.fields['status'].choices 
                if choice[0] in ['draft', 'published']
            ]


class TravelTipCommentForm(forms.ModelForm):
    """
    Form for adding comments to travel tips.
    
    Simple form with just a content field for user comments.
    """
    class Meta:
        model = TravelTipComment
        fields = ['content']
        widgets = {
            'content': Textarea(attrs={
                'class': 'form-textarea mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'rows': 3,
                'placeholder': 'Share your thoughts, experiences, or ask a question...',
                'required': 'required',
            })
        }
        labels = {
            'content': 'Your Comment'
        }


class TravelTipCategoryForm(forms.ModelForm):
    """
    Form for creating and editing travel tip categories.
    
    Used in the admin interface or for staff to manage categories.
    """
    class Meta:
        model = TravelTipCategory
        fields = ['name', 'description', 'icon']
        widgets = {
            'name': TextInput(attrs={
                'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'placeholder': 'e.g., Packing, Budget Travel, Safety Tips'
            }),
            'description': Textarea(attrs={
                'class': 'form-textarea mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'rows': 3,
                'placeholder': 'A brief description of this category'
            }),
            'icon': TextInput(attrs={
                'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'placeholder': 'e.g., fa-suitcase, fa-money-bill-wave, fa-camera'
            }),
        }
