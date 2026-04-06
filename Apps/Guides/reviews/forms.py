"""
Forms for the reviews_new application.

This module defines forms for creating, editing, and filtering reviews,
as well as for uploading review images and adding comments.
All forms include comprehensive field validation and styling.
"""

import os
from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from .models import Review, ReviewImage, ReviewComment


class ReviewForm(forms.ModelForm):
    """
    Form for creating and editing reviews.
    
    Includes fields for review title, content, and rating with appropriate
    validation and styling. Uses a star rating widget for the rating field.
    
    Attributes:
        title (CharField): Review title with maximum length validation
        content (TextField): Review content with minimum length validation
        rating (ChoiceField): Star rating with custom widget
    """
    
    class Meta:
        """Meta options for the ReviewForm."""
        model = Review
        fields = ['title', 'content', 'rating']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'placeholder': _('Enter a title for your review'),
            }),
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'placeholder': _('Share your experience...'),
                'rows': 5,
            }),
            'rating': forms.RadioSelect(attrs={
                'class': 'star-rating hidden',
            }),
        }
        error_messages = {
            'title': {
                'required': _('Please provide a title for your review.'),
                'max_length': _('Title is too long. Please keep it under 255 characters.'),
            },
            'content': {
                'required': _('Please share your experience.'),
            },
            'rating': {
                'required': _('Please select a rating.'),
                'invalid_choice': _('Please select a valid rating between 1 and 5.'),
            },
        }
    
    def clean_content(self):
        """
        Validate that review content meets minimum length requirements.
        
        Returns:
            str: Cleaned content value
            
        Raises:
            ValidationError: If content is too short
        """
        content = self.cleaned_data.get('content')
        if content and len(content) < 20:
            raise forms.ValidationError(_('Please provide more details (at least 20 characters).'))
        return content


class ReviewImageForm(forms.ModelForm):
    """
    Form for uploading images for a review.
    
    Handles single or multiple image uploads with optional captions.
    Validates file types, sizes, and enforces upload limits.
    
    Attributes:
        image (ImageField): The image file to upload
        caption (CharField): Optional caption for the image
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the form with custom attributes.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        super().__init__(*args, **kwargs)
        # Set HTML attributes for the file input
        self.fields['image'].widget.attrs.update({
            'class': 'hidden',
            'accept': 'image/*',
            'multiple': True,
            'data-max-size': '5242880'  # 5MB in bytes
        })
    
    class Meta:
        """Meta options for the ReviewImageForm."""
        model = ReviewImage
        fields = ['image', 'caption']
        widgets = {
            'caption': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'placeholder': _('Add a caption (optional)'),
                'maxlength': '255',
            }),
        }
        error_messages = {
            'image': {
                'required': _('Please select an image file.'),
                'invalid_image': _('The selected file is not a valid image.'),
            },
            'caption': {
                'max_length': _('Caption is too long. Maximum 255 characters allowed.'),
            },
        }
        
    def clean_image(self):
        """
        Validate that the uploaded file is an image with acceptable size and type.
        
        Returns:
            ImageField: Cleaned image value
            
        Raises:
            ValidationError: If file is too large, not an image, or has invalid extension
        """
        image = self.cleaned_data.get('image')
        if not image:
            return image
            
        # Check file size (limit to 5MB)
        max_size = 5 * 1024 * 1024  # 5MB in bytes
        if image.size > max_size:
            raise forms.ValidationError(
                _('Image file too large. Please keep it under 5MB.')
            )
        
        # Check file extension
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        ext = os.path.splitext(image.name)[1].lower()
        if ext not in allowed_extensions:
            raise forms.ValidationError(
                _('Unsupported file type. Allowed formats: JPG, JPEG, PNG, GIF, WEBP')
            )
            
        # Additional validation using Pillow if available
        try:
            from PIL import Image
            from io import BytesIO
            
            # Open the image to verify it's a valid image file
            img = Image.open(image)
            
            # Verify image format
            if img.format.lower() not in ['jpeg', 'png', 'gif', 'webp']:
                raise forms.ValidationError(
                    _('Invalid image format. Please upload a valid image file.')
                )
                
            # Reset file pointer after reading
            image.seek(0)
            
        except ImportError:
            # Pillow not available, skip additional validation
            pass
        except Exception as e:
            # Catch any errors during image processing
            raise forms.ValidationError(
                _('Invalid image file. Please upload a valid image.')
            )
                
        return image


# Create a formset for multiple image uploads
ReviewImageFormSet = inlineformset_factory(
    Review,
    ReviewImage,
    form=ReviewImageForm,
    extra=3,
    max_num=5,
    can_delete=True,
)


class ReviewCommentForm(forms.ModelForm):
    """
    Form for adding comments to reviews.
    
    Includes fields for comment content with appropriate validation.
    For staff users, also includes a field to mark as official response.
    
    Attributes:
        content (TextField): Comment text
        is_official_response (BooleanField): Whether this is an official staff response
    """
    
    class Meta:
        """Meta options for the ReviewCommentForm."""
        model = ReviewComment
        fields = ['content', 'is_official_response']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'placeholder': _('Add a comment...'),
                'rows': 3,
            }),
            'is_official_response': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500',
            }),
        }
        
    def __init__(self, *args, **kwargs):
        """
        Initialize the form and customize fields based on user permissions.
        
        Only show the official response checkbox to staff users.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments, may include 'user'
        """
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Only show official response option to staff
        if self.user and not self.user.is_staff:
            self.fields.pop('is_official_response')


class ReviewFilterForm(forms.Form):
    """
    Form for filtering reviews by various criteria.
    
    Allows filtering reviews by rating, date range, and sorting options.
    
    Attributes:
        rating (MultipleChoiceField): Filter by specific ratings
        date_range (ChoiceField): Filter by when reviews were posted
        sort_by (ChoiceField): Sort reviews by different criteria
    """
    
    # Rating filter options
    RATING_FILTER_CHOICES = [
        ('5', _('5 Stars')),
        ('4', _('4 Stars')),
        ('3', _('3 Stars')),
        ('2', _('2 Stars')),
        ('1', _('1 Star')),
    ]
    
    # Date range filter options
    DATE_RANGE_CHOICES = [
        ('', _('All Time')),
        ('week', _('Last Week')),
        ('month', _('Last Month')),
        ('year', _('Last Year')),
    ]
    
    # Sort options
    SORT_CHOICES = [
        ('newest', _('Newest First')),
        ('oldest', _('Oldest First')),
        ('highest', _('Highest Rated')),
        ('lowest', _('Lowest Rated')),
        ('helpful', _('Most Helpful')),
    ]
    
    rating = forms.MultipleChoiceField(
        choices=RATING_FILTER_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500',
        }),
        label=_('Rating')
    )
    
    date_range = forms.ChoiceField(
        choices=DATE_RANGE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500',
        }),
        label=_('Date Range')
    )
    
    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='newest',
        widget=forms.Select(attrs={
            'class': 'block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500',
        }),
        label=_('Sort By')
    )

