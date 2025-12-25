"""
Customer app forms.
Contains forms for customer information during checkout, restaurant upgrade applications, 
review functionality, and user profile management.
"""
import re
from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from restaurant.models import PendingRestaurant
from .models import RestaurantReview, MenuItemReview, ReviewResponse, ReviewFlag, UserProfile


class CheckoutForm(forms.Form):
    """
    Form for collecting customer information during checkout.
    
    Fields:
        delivery_method: Choice between delivery and takeaway
        delivery_time: Preferred delivery time slot
        customer_name: Customer's full name
        customer_phone: Customer's phone number
        customer_address: Delivery address (required for delivery)
        notes: Optional order notes or instructions
    """
    DELIVERY_CHOICES = [
        ('delivery', '🏠 Delivery'),
        ('takeaway', '🥡 Takeaway'),
    ]
    
    DELIVERY_TIME_CHOICES = [
        ('asap', 'ASAP (25-35 min)'),
        ('30min', '30 minutes'),
        ('1hr', '1 hour'),
        ('2hr', '2 hours'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cod', '💵 Cash on Delivery'),
    ]
    
    delivery_method = forms.ChoiceField(
        choices=DELIVERY_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'space-y-3',
            'onchange': 'toggleAddressField()'
        }),
        initial='delivery',
        label='Delivery Method'
    )
    
    delivery_time = forms.ChoiceField(
        choices=DELIVERY_TIME_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'delivery-time-radio',
        }),
        initial='asap',
        label='Delivery Time'
    )
    
    customer_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': 'Enter your full name'
        }),
        label='Full Name'
    )
    
    customer_phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': 'Enter your phone number'
        }),
        label='Phone Number'
    )
    
    customer_address = forms.CharField(
        required=False,  # Made optional, will be validated in clean() method
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'rows': 4,
            'placeholder': 'Enter your delivery address'
        }),
        label='Delivery Address'
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'rows': 3,
            'placeholder': 'Any special instructions? (Optional)'
        }),
        label='Order Notes'
    )
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'payment-method-radio',
        }),
        initial='cod',
        label='Payment Method'
    )
    
    def clean(self):
        """
        Custom validation to ensure address is required for delivery orders.
        Sanitizes all text inputs to prevent XSS attacks and enforces length limits.
        """
        cleaned_data = super().clean()
        delivery_method = cleaned_data.get('delivery_method')
        customer_address = cleaned_data.get('customer_address')
        customer_name = cleaned_data.get('customer_name')
        notes = cleaned_data.get('notes')
        
        # Validate address requirement for delivery orders
        if delivery_method == 'delivery' and not customer_address:
            self.add_error('customer_address', 'Address is required for delivery orders')
        
        # Server-side sanitization and validation for security
        # This mirrors client-side validation but provides authoritative protection
        if customer_name:
            # Remove HTML tags and scripts, enforce length limits
            sanitized_name = self.sanitize_text_input(customer_name, max_length=200)
            if len(sanitized_name) < 2:
                self.add_error('customer_name', 'Name must be at least 2 characters long')
            elif not re.match(r'^[a-zA-Z\s]+$', sanitized_name):
                self.add_error('customer_name', 'Name can only contain letters and spaces')
            else:
                cleaned_data['customer_name'] = sanitized_name
        
        if customer_address:
            # Sanitize address input
            sanitized_address = self.sanitize_text_input(customer_address, max_length=200)
            if len(sanitized_address) < 10:
                self.add_error('customer_address', 'Address must be at least 10 characters long')
            else:
                cleaned_data['customer_address'] = sanitized_address
        
        if notes:
            # Sanitize notes input
            sanitized_notes = self.sanitize_text_input(notes, max_length=300)
            cleaned_data['notes'] = sanitized_notes
        
        return cleaned_data
    
    def sanitize_text_input(self, text, max_length=200):
        """
        Sanitize text input to prevent XSS attacks and enforce length limits.
        
        This server-side sanitization provides the authoritative security layer,
        complementing client-side validation in JavaScript.
        
        Args:
            text (str): Raw text input to sanitize
            max_length (int): Maximum allowed length for the field
            
        Returns:
            str: Sanitized text safe for database storage
        """
        if not text:
            return ''
        
        # Remove HTML tags and potential scripts
        sanitized = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', text, flags=re.IGNORECASE)
        sanitized = re.sub(r'<[^>]*>', '', sanitized)
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'on\w+\s*=', '', sanitized, flags=re.IGNORECASE)
        
        # Remove extra whitespace and limit length
        sanitized = ' '.join(sanitized.split())
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length].strip()
        
        return sanitized


class RestaurantUpgradeForm(forms.ModelForm):
    """
    Restaurant upgrade form for customers applying to become restaurant owners.
    
    This form allows customers to submit restaurant applications that go through
    a manager approval process. It collects all restaurant information needed
    for the application and creates a PendingRestaurant record.
    
    Fields:
        restaurant_name: Proposed restaurant name
        description: Restaurant description and specialties
        address: Physical restaurant address
        phone: Contact phone number
        restaurant_email: Restaurant contact email (optional)
        cuisine_type: Type of cuisine
        image: Restaurant logo or cover photo (optional)
        opening_time: Business opening time
        closing_time: Business closing time
        minimum_order: Minimum order amount
        delivery_fee: Delivery charge
    """
    
    restaurant_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': 'Enter your restaurant name'
        }),
        help_text='The official name of your restaurant'
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': 'Describe your restaurant, specialties, and what makes you unique...',
            'rows': 4
        }),
        help_text='Tell customers about your restaurant, cuisine specialties, and unique features'
    )
    
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': 'Enter your restaurant address',
            'rows': 3
        }),
        help_text='Complete physical address for delivery and customer navigation'
    )
    
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': 'Enter your contact phone number'
        }),
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Please enter a valid phone number (10-15 digits, optional country code).'
            )
        ],
        help_text='Customer service phone number'
    )
    
    restaurant_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': 'Restaurant contact email (optional)'
        }),
        help_text='Optional business email for customer inquiries'
    )
    
    cuisine_type = forms.ChoiceField(
        choices=PendingRestaurant._meta.get_field('cuisine_type').choices,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200'
        }),
        help_text='Select your primary cuisine type'
    )
    
    image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200'
        }),
        help_text='Upload your restaurant logo or cover photo (optional)'
    )
    
    opening_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'type': 'time'
        }),
        help_text='When your restaurant opens for business'
    )
    
    closing_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'type': 'time'
        }),
        help_text='When your restaurant closes for business'
    )
    
    minimum_order = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        help_text='Minimum order amount in rupees for delivery'
    )
    
    delivery_fee = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        help_text='Delivery charge in rupees (enter 0 for free delivery)'
    )
    
    class Meta:
        model = PendingRestaurant
        fields = []  # All fields are defined above for custom validation and help text
    
    def clean_restaurant_name(self):
        """
        Validate restaurant name uniqueness.
        
        Checks if a restaurant with the same name already exists
        in either approved restaurants or pending applications.
        
        Returns:
            str: Validated restaurant name
            
        Raises:
            forms.ValidationError: If restaurant name is already taken
        """
        restaurant_name = self.cleaned_data.get('restaurant_name')
        from restaurant.models import Restaurant
        
        # Check existing restaurants
        if Restaurant.objects.filter(name__iexact=restaurant_name).exists():
            raise forms.ValidationError(
                'A restaurant with this name already exists. Please choose a different name.'
            )
        
        # Check pending applications
        if PendingRestaurant.objects.filter(
            restaurant_name__iexact=restaurant_name,
            status='pending'
        ).exists():
            raise forms.ValidationError(
                'There is already a pending application for a restaurant with this name.'
            )
        
        return restaurant_name
    
    def clean_phone(self):
        """
        Validate phone number format and uniqueness.
        
        Returns:
            str: Validated phone number
            
        Raises:
            forms.ValidationError: If phone number is invalid or already in use
        """
        phone = self.cleaned_data.get('phone')
        
        # Check if phone is already used by an approved restaurant
        from restaurant.models import Restaurant
        if Restaurant.objects.filter(phone=phone).exists():
            raise forms.ValidationError(
                'This phone number is already registered with another restaurant.'
            )
        
        # Check if phone is already used in a pending application
        if PendingRestaurant.objects.filter(
            phone=phone,
            status='pending'
        ).exists():
            raise forms.ValidationError(
                'There is already a pending application using this phone number.'
            )
        
        return phone
    
    def clean(self):
        """
        Perform form-wide validation.
        
        Validates that closing time is after opening time and that
        the user doesn't already have a pending application.
        """
        cleaned_data = super().clean()
        opening_time = cleaned_data.get('opening_time')
        closing_time = cleaned_data.get('closing_time')
        
        # Validate business hours
        if opening_time and closing_time and opening_time >= closing_time:
            raise forms.ValidationError(
                'Closing time must be after opening time. Please check your business hours.'
            )
        
        return cleaned_data


class RestaurantReviewForm(forms.ModelForm):
    """
    Form for creating and editing restaurant reviews.
    
    Includes comprehensive rating fields for different aspects of the dining experience.
    """
    
    class Meta:
        model = RestaurantReview
        fields = [
            'rating', 'title', 'comment', 'food_quality', 
            'service_quality', 'delivery_speed', 'value_for_money'
        ]
        widgets = {
            'rating': forms.RadioSelect(
                choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'star-rating'}
            ),
            'title': forms.TextInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500',
                    'placeholder': 'Summarize your experience in a few words'
                }
            ),
            'comment': forms.Textarea(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500',
                    'rows': 4,
                    'placeholder': 'Share details about your experience with this restaurant...'
                }
            ),
            'food_quality': forms.RadioSelect(
                choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'star-rating'}
            ),
            'service_quality': forms.RadioSelect(
                choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'star-rating'}
            ),
            'delivery_speed': forms.RadioSelect(
                choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'star-rating'}
            ),
            'value_for_money': forms.RadioSelect(
                choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'star-rating'}
            ),
        }
    
    def __init__(self, *args, **kwargs):
        """
        Initialize form with custom field labels and help text.
        """
        super().__init__(*args, **kwargs)
        
        self.fields['rating'].label = 'Overall Rating'
        self.fields['rating'].required = True
        
        self.fields['title'].label = 'Review Title'
        self.fields['title'].required = False
        
        self.fields['comment'].label = 'Your Review'
        self.fields['comment'].required = True
        
        self.fields['food_quality'].label = 'Food Quality'
        self.fields['food_quality'].required = False
        
        self.fields['service_quality'].label = 'Service Quality'
        self.fields['service_quality'].required = False
        
        self.fields['delivery_speed'].label = 'Delivery Speed'
        self.fields['delivery_speed'].required = False
        
        self.fields['value_for_money'].label = 'Value for Money'
        self.fields['value_for_money'].required = False
    
    def clean_rating(self):
        """
        Validate that rating is between 1 and 5.
        
        Returns:
            int: Validated rating value
        """
        rating = self.cleaned_data.get('rating')
        if rating and (rating < 1 or rating > 5):
            raise ValidationError('Rating must be between 1 and 5 stars.')
        return rating
    
    def clean_comment(self):
        """
        Validate comment length and content.
        
        Returns:
            str: Validated comment
        """
        comment = self.cleaned_data.get('comment')
        if comment and len(comment.strip()) < 10:
            raise ValidationError('Please provide at least 10 characters for your review.')
        return comment


class MenuItemReviewForm(forms.ModelForm):
    """
    Form for creating and editing menu item reviews.
    
    Focuses on specific aspects of individual dishes.
    """
    
    class Meta:
        model = MenuItemReview
        fields = ['rating', 'comment', 'taste', 'presentation', 'portion_size']
        widgets = {
            'rating': forms.RadioSelect(
                choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'star-rating'}
            ),
            'comment': forms.Textarea(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500',
                    'rows': 3,
                    'placeholder': 'Share your thoughts on this menu item...'
                }
            ),
            'taste': forms.RadioSelect(
                choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'star-rating'}
            ),
            'presentation': forms.RadioSelect(
                choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'star-rating'}
            ),
            'portion_size': forms.RadioSelect(
                choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'star-rating'}
            ),
        }
    
    def __init__(self, *args, **kwargs):
        """
        Initialize form with custom field labels.
        """
        super().__init__(*args, **kwargs)
        
        self.fields['rating'].label = 'Overall Rating'
        self.fields['rating'].required = True
        
        self.fields['comment'].label = 'Your Review'
        self.fields['comment'].required = False
        
        self.fields['taste'].label = 'Taste'
        self.fields['taste'].required = False
        
        self.fields['presentation'].label = 'Presentation'
        self.fields['presentation'].required = False
        
        self.fields['portion_size'].label = 'Portion Size'
        self.fields['portion_size'].required = False


class ReviewResponseForm(forms.ModelForm):
    """
    Form for restaurant owners to respond to customer reviews.
    """
    
    class Meta:
        model = ReviewResponse
        fields = ['response', 'is_public']
        widgets = {
            'response': forms.Textarea(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500',
                    'rows': 4,
                    'placeholder': 'Write your response to the customer review...'
                }
            ),
            'is_public': forms.CheckboxInput(
                attrs={'class': 'form-checkbox h-4 w-4 text-orange-600'}
            ),
        }
    
    def __init__(self, *args, **kwargs):
        """
        Initialize form with custom field labels.
        """
        super().__init__(*args, **kwargs)
        
        self.fields['response'].label = 'Your Response'
        self.fields['response'].required = True
        
        self.fields['is_public'].label = 'Make this response public'
        self.fields['is_public'].initial = True
    
    def clean_response(self):
        """
        Validate response length and content.
        
        Returns:
            str: Validated response
        """
        response = self.cleaned_data.get('response')
        if response and len(response.strip()) < 10:
            raise ValidationError('Please provide at least 10 characters for your response.')
        return response


class ReviewFlagForm(forms.ModelForm):
    """
    Form for users to flag inappropriate reviews.
    """
    
    class Meta:
        model = ReviewFlag
        fields = ['reason', 'description']
        widgets = {
            'reason': forms.Select(
                attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500'}
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500',
                    'rows': 3,
                    'placeholder': 'Please provide additional details about why you are flagging this review...'
                }
            ),
        }
    
    def __init__(self, *args, **kwargs):
        """
        Initialize form with custom field labels.
        """
        super().__init__(*args, **kwargs)
        
        self.fields['reason'].label = 'Reason for Flagging'
        self.fields['reason'].required = True
        
        self.fields['description'].label = 'Additional Details'
        self.fields['description'].required = False
    
    def clean_description(self):
        """
        Validate description length if provided.
        
        Returns:
            str: Validated description
        """
        description = self.cleaned_data.get('description')
        if description and len(description.strip()) < 10:
            raise ValidationError('If providing details, please write at least 10 characters.')
        return description


class UserProfileEditForm(forms.ModelForm):
    """
    Form for editing user profile information.
    
    Allows users to update their personal information, contact details,
    address, and preferences directly from their profile page.
    
    Fields:
        full_name: User's full name for delivery and personalization
        phone_number: Contact phone number for order notifications
        address: Delivery address
        city: City for delivery
        postal_code: Postal/ZIP code for delivery
        dietary_preferences: Dietary restrictions and preferences
        profile_picture: Profile picture upload
    """
    
    full_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-rose-500 focus:ring-2 focus:ring-rose-200 transition duration-200',
            'placeholder': 'Enter your full name'
        }),
        help_text='Full name for delivery and personalization'
    )
    
    phone_number = forms.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Phone number must be entered in the format: +999999999. Up to 15 digits allowed.'
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-rose-500 focus:ring-2 focus:ring-rose-200 transition duration-200',
            'placeholder': 'Enter your phone number'
        }),
        help_text='Phone number for order notifications and delivery contact'
    )
    
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-rose-500 focus:ring-2 focus:ring-rose-200 transition duration-200',
            'rows': 3,
            'placeholder': 'Enter your delivery address'
        }),
        help_text='Delivery address for food orders'
    )
    
    city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-rose-500 focus:ring-2 focus:ring-rose-200 transition duration-200',
            'placeholder': 'Enter your city'
        }),
        help_text='City for delivery'
    )
    
    postal_code = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-rose-500 focus:ring-2 focus:ring-rose-200 transition duration-200',
            'placeholder': 'Enter your postal code'
        }),
        help_text='Postal/ZIP code for delivery'
    )
    
    dietary_preferences = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-rose-500 focus:ring-2 focus:ring-rose-200 transition duration-200',
            'placeholder': 'e.g., vegetarian, vegan, gluten-free, allergies'
        }),
        help_text='Dietary preferences for better restaurant recommendations'
    )
    
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-rose-500 focus:ring-2 focus:ring-rose-200 transition duration-200',
            'accept': 'image/*'
        }),
        help_text='Upload a new profile picture (optional)'
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'full_name', 'phone_number', 'address', 'city', 
            'postal_code', 'dietary_preferences', 'profile_picture'
        ]
    
    def __init__(self, *args, **kwargs):
        """
        Initialize form with custom field labels and styling.
        """
        super().__init__(*args, **kwargs)
        
        # Set custom labels
        self.fields['full_name'].label = 'Full Name'
        self.fields['phone_number'].label = 'Phone Number'
        self.fields['address'].label = 'Delivery Address'
        self.fields['city'].label = 'City'
        self.fields['postal_code'].label = 'Postal Code'
        self.fields['dietary_preferences'].label = 'Dietary Preferences'
        self.fields['profile_picture'].label = 'Profile Picture'
    
    def clean_phone_number(self):
        """
        Validate phone number format.
        
        Returns:
            str: Validated phone number
            
        Raises:
            forms.ValidationError: If phone number format is invalid
        """
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number and len(phone_number.strip()) < 10:
            raise ValidationError('Please enter a valid phone number with at least 10 digits.')
        return phone_number
    
    def clean_profile_picture(self):
        """
        Validate profile picture size and format.
        
        Returns:
            ImageField: Validated profile picture
            
        Raises:
            forms.ValidationError: If image is too large or invalid format
        """
        profile_picture = self.cleaned_data.get('profile_picture')
        if profile_picture:
            # Check file size (limit to 5MB)
            if profile_picture.size > 5 * 1024 * 1024:
                raise ValidationError('Profile picture must be smaller than 5MB.')
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if profile_picture.content_type not in allowed_types:
                raise ValidationError('Please upload a valid image file (JPEG, PNG, GIF, or WebP).')
        
        return profile_picture


class GuestCheckoutForm(forms.Form):
    """
    Guest checkout form for collecting contact information for bill delivery.
    
    This form is used when customers scan QR codes at restaurant tables
    and want to receive their bill via email or SMS without creating an account.
    """
    
    DELIVERY_CHOICES = [
        ('email', 'Send Bill via Email'),
        ('sms', 'Send Bill via SMS'),
        ('both', 'Send via Email & SMS'),
    ]
    
    customer_name = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
            'placeholder': 'Your Name',
            'autocomplete': 'name'
        }),
        help_text='Your name for the order'
    )
    
    delivery_method = forms.ChoiceField(
        choices=DELIVERY_CHOICES,
        required=True,
        initial='email',
        widget=forms.RadioSelect(attrs={
            'class': 'space-y-2'
        }),
        help_text='How would you like to receive your bill?'
    )
    
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
            'placeholder': 'your.email@example.com',
            'autocomplete': 'email'
        }),
        help_text='Email address to receive the bill PDF'
    )
    
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
            'placeholder': '+91 98765 43210',
            'autocomplete': 'tel',
            'pattern': '[+]?[0-9]{10,15}'
        }),
        help_text='Mobile number to receive bill via SMS'
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
            'placeholder': 'Any special requests or notes...',
            'rows': 3
        }),
        help_text='Special instructions for your order (optional)'
    )
    
    def clean(self):
        """
        Custom validation to ensure at least email or phone is provided
        based on the delivery method selected.
        """
        cleaned_data = super().clean()
        delivery_method = cleaned_data.get('delivery_method')
        email = cleaned_data.get('email')
        phone = cleaned_data.get('phone')
        
        if delivery_method in ['email', 'both'] and not email:
            raise forms.ValidationError(
                'Email address is required for email delivery.'
            )
        
        if delivery_method in ['sms', 'both'] and not phone:
            raise forms.ValidationError(
                'Phone number is required for SMS delivery.'
            )
        
        # Validate phone number format
        if phone:
            # Remove spaces, dashes, and parentheses for validation
            phone_clean = ''.join(c for c in phone if c.isdigit() or c == '+')
            if len(phone_clean) < 10 or len(phone_clean) > 15:
                raise forms.ValidationError(
                    'Please enter a valid phone number (10-15 digits).'
                )
            cleaned_data['phone'] = phone_clean
        
        return cleaned_data
    
    def clean_phone(self):
        """
        Validate phone number format.
        """
        phone = self.cleaned_data.get('phone')
        if phone:
            # Basic phone validation - can be enhanced
            if not any(c.isdigit() for c in phone):
                raise forms.ValidationError(
                    'Phone number must contain at least one digit.'
                )
        return phone
    
    def get_delivery_info(self):
        """
        Returns formatted delivery information based on the form data.
        
        Returns:
            dict: Delivery information with formatted contact details
        """
        delivery_method = self.cleaned_data.get('delivery_method')
        email = self.cleaned_data.get('email')
        phone = self.cleaned_data.get('phone')
        customer_name = self.cleaned_data.get('customer_name')
        
        delivery_info = {
            'method': delivery_method,
            'name': customer_name,
            'email': email if delivery_method in ['email', 'both'] else None,
            'phone': phone if delivery_method in ['sms', 'both'] else None,
            'display_text': []
        }
        
        if delivery_method in ['email', 'both']:
            delivery_info['display_text'].append(f'Email: {email}')
        
        if delivery_method in ['sms', 'both']:
            delivery_info['display_text'].append(f'SMS: {phone}')
        
        return delivery_info
