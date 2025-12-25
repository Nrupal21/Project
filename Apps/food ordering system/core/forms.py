"""
Core forms for the food ordering system.
Contains unified login and registration forms for role-based authentication.
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User, Group
from django.core.validators import RegexValidator
from restaurant.models import Restaurant
from customer.models import UserProfile


class UnifiedLoginForm(AuthenticationForm):
    """
    Enhanced unified login form for both customers and restaurant owners.
    Extends Django's AuthenticationForm with custom styling, role detection, and security features.
    
    Features:
    - Remember me functionality for extended sessions
    - Enhanced error messages with specific feedback
    - Account status validation (active/inactive)
    - CSRF protection and rate limiting integration
    - Mobile-responsive design with Tailwind CSS
    - Login with either username OR email address
    
    Fields:
        username: User username OR email address (for both customers and restaurant owners)
        password: User password
        remember_me: Optional checkbox for extended session
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': 'Enter your username or email',
            'autofocus': True,
            'autocomplete': 'username'
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password'
        })
    )
    
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-gray-900 border-gray-300 rounded focus:ring-gray-900 focus:ring-2',
            'id': 'remember_me'
        })
    )
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the enhanced unified login form.
        
        Sets up custom error messages, form styling, and validation rules.
        """
        super().__init__(*args, **kwargs)
        
        # Enhanced error messages for better user experience
        self.error_messages.update({
            'invalid_login': 'Invalid username or password. Please check your credentials and try again.',
            'inactive': 'Your account has been deactivated. Please contact support for assistance.',
            'locked_out': 'Too many failed login attempts. Please try again later.',
        })
        
        # Apply consistent styling to all form fields
        for field_name, field in self.fields.items():
            if field_name != 'remember_me':
                field.widget.attrs.update({
                    'class': field.widget.attrs.get('class', '') + ' focus:outline-none focus:ring-2',
                })
    
    def confirm_login_allowed(self, user):
        """
        Enhanced login validation with detailed error messages.
        
        Args:
            user: User object to validate
            
        Raises:
            ValidationError: If user account is not allowed to login
        """
        super().confirm_login_allowed(user)
        
        # Additional validation for business logic
        if not user.is_active:
            raise forms.ValidationError(
                self.error_messages['inactive'],
                code='inactive'
            )
        
        # Check if user has required profile information (non-blocking)
        try:
            from customer.models import UserProfile
            profile = UserProfile.objects.get(user=user)
            if not profile.phone_number:
                # Warning but allow login - they'll be prompted to complete profile
                pass
        except UserProfile.DoesNotExist:
            # Create missing profile automatically (non-blocking)
            try:
                UserProfile.objects.create(user=user, full_name=user.username)
            except Exception:
                # If profile creation fails, still allow login
                pass
    
    def get_redirect_url(self, user):
        """
        Determine the redirect URL based on user's role with enhanced logic.
        
        Args:
            user: Authenticated User object
            
        Returns:
            str: URL to redirect user based on their role and status
        """
        # Debug logging
        print(f"DEBUG get_redirect_url: User={user.username}")
        print(f"DEBUG get_redirect_url: Has restaurants={user.restaurants.exists()}")
        if user.restaurants.exists():
            print(f"DEBUG get_redirect_url: Restaurant count={user.restaurants.count()}")
        
        # Check if user is a restaurant owner (matching dropdown logic)
        if user.restaurants.exists():
            print(f"DEBUG get_redirect_url: Returning restaurant:dashboard")
            return 'restaurant:dashboard'
        
        # Check if user is staff/admin
        if user.is_staff or user.is_superuser:
            print(f"DEBUG get_redirect_url: Returning admin:index")
            return 'admin:index'
        
        # Default to customer home
        print(f"DEBUG get_redirect_url: Returning customer:home")
        return 'customer:home'


class UnifiedRegistrationForm(forms.ModelForm):
    """
    Enhanced unified registration form for food ordering system.
    
    Includes essential customer information for delivery and contact:
    - User account details (username, email, password)
    - Personal information (full name, phone number)
    - Optional address for delivery
    
    Fields:
        username: Unique username for the user
        email: User email address
        full_name: Full name for delivery and personalization
        phone_number: Phone number for order notifications
        password: User password
        password_confirm: Password confirmation field
        address: Optional delivery address
        city: Optional delivery city
        postal_code: Optional postal code
    """
    # User Account Fields
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': 'Create a strong password'
        }),
        validators=[
            RegexValidator(
                regex=r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$',
                message='Password must be at least 8 characters long and contain both letters and numbers.'
            )
        ]
    )
    
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': 'Confirm your password'
        })
    )
    
    # Profile Information Fields
    full_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': 'Enter your full name'
        }),
        help_text='This will be used for delivery and order personalization'
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
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': '+1234567890'
        }),
        help_text='Required for order notifications and delivery contact'
    )
    
    # Optional Address Fields
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': 'Street address (optional - can be added during checkout)',
            'rows': 2
        })
    )
    
    city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': 'City (optional)'
        })
    )
    
    postal_code = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': 'Postal/ZIP code (optional)'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
                'placeholder': 'Choose a unique username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
                'placeholder': 'Enter your email address'
            })
        }
    
    def clean_username(self):
        """
        Validate username uniqueness and format.
        
        Returns:
            str: Validated username
            
        Raises:
            forms.ValidationError: If username is taken or invalid
        """
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken. Please choose another.')
        return username
    
    def clean_email(self):
        """
        Validate email uniqueness.
        
        Returns:
            str: Validated email
            
        Raises:
            forms.ValidationError: If email is already registered
        """
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('This email is already registered. Please use another email.')
        return email
    
    def clean(self):
        """
        Validate form-wide dependencies.
        
        Returns:
            dict: Cleaned form data
            
        Raises:
            forms.ValidationError: If passwords don't match
        """
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Passwords do not match.')
        
        return cleaned_data
    
    def save(self, commit=True):
        """
        Save the user and create/update their profile.
        
        Creates both the User account and UserProfile with the provided
        information. Assigns the user to the Customer group.
        
        Args:
            commit (bool): Whether to save to database immediately
            
        Returns:
            User: The created user instance
        """
        # Create the User account
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        
        if commit:
            user.save()
            
            # Create or update UserProfile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.full_name = self.cleaned_data['full_name']
            profile.phone_number = self.cleaned_data['phone_number']
            profile.address = self.cleaned_data.get('address', '')
            profile.city = self.cleaned_data.get('city', '')
            profile.postal_code = self.cleaned_data.get('postal_code', '')
            profile.save()
            
            # Assign to Customer group
            customer_group, _ = Group.objects.get_or_create(name='Customer')
            user.groups.add(customer_group)
        
        return user


class RestaurantRegistrationForm(forms.ModelForm):
    """
    Restaurant registration form for creating restaurant owner accounts and restaurant profiles.
    
    This form creates both a User account and Restaurant profile in a single submission.
    It handles all restaurant-specific information and automatically assigns the user
    to the Restaurant Owner group.
    
    Fields:
        User Account: username, email, password, password_confirm
        Restaurant Info: name, description, address, phone, email, cuisine_type, 
                        opening_time, closing_time, minimum_order, delivery_fee, image
    """
    # User Account Fields
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': 'Choose a username for your account'
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': 'Enter your email address'
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': 'Create a strong password'
        }),
        validators=[
            RegexValidator(
                regex=r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$',
                message='Password must be at least 8 characters long and contain both letters and numbers.'
            )
        ]
    )
    
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': 'Confirm your password'
        })
    )
    
    # Restaurant Information Fields
    restaurant_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': 'Enter your restaurant name'
        })
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': 'Describe your restaurant, specialties, and what makes you unique...',
            'rows': 4
        })
    )
    
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': 'Enter your restaurant address',
            'rows': 3
        })
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
                message='Please enter a valid phone number.'
            )
        ]
    )
    
    restaurant_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': 'Restaurant contact email (optional)'
        })
    )
    
    cuisine_type = forms.ChoiceField(
        choices=Restaurant.CUISINE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200'
        }),
        initial='other'
    )
    
    opening_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'type': 'time'
        }),
        initial='09:00'
    )
    
    closing_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'type': 'time'
        }),
        initial='22:00'
    )
    
    minimum_order = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        initial=0.00,
        help_text='Minimum order amount in rupees'
    )
    
    delivery_fee = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        initial=0.00,
        help_text='Delivery charge in rupees'
    )
    
    image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-200 transition duration-200'
        }),
        help_text='Upload your restaurant logo or cover photo'
    )
    
    class Meta:
        model = Restaurant
        fields = []  # All fields are defined above for custom naming and validation
    
    def clean_username(self):
        """
        Validate username uniqueness.
        
        Returns:
            str: Validated username
            
        Raises:
            forms.ValidationError: If username is taken
        """
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken. Please choose another.')
        return username
    
    def clean_email(self):
        """
        Validate email uniqueness.
        
        Returns:
            str: Validated email
            
        Raises:
            forms.ValidationError: If email is already registered
        """
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('This email is already registered. Please use another email.')
        return email
    
    def clean_password_confirm(self):
        """
        Validate that password and password confirmation match.
        
        Returns:
            str: Confirmed password
            
        Raises:
            forms.ValidationError: If passwords don't match
        """
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Passwords do not match.')
        
        return password_confirm
    
    def clean(self):
        """
        Perform comprehensive form-wide validation.
        
        Validates:
        - Business hours (closing time after opening time)
        - Duplicate restaurant names
        - Phone number format
        - Minimum order and delivery fee values
        - Image file size and format
        
        Returns:
            dict: Cleaned data
            
        Raises:
            forms.ValidationError: If validation fails
        """
        cleaned_data = super().clean()
        
        # Validate business hours
        opening_time = cleaned_data.get('opening_time')
        closing_time = cleaned_data.get('closing_time')
        
        if opening_time and closing_time:
            if opening_time >= closing_time:
                raise forms.ValidationError(
                    'Closing time must be after opening time. '
                    'If your restaurant is open past midnight, please contact support.'
                )
            
            # Check if business hours are reasonable (at least 1 hour)
            from datetime import datetime, timedelta
            opening_dt = datetime.combine(datetime.today(), opening_time)
            closing_dt = datetime.combine(datetime.today(), closing_time)
            hours_diff = (closing_dt - opening_dt).seconds / 3600
            
            if hours_diff < 1:
                raise forms.ValidationError(
                    'Restaurant must be open for at least 1 hour per day.'
                )
        
        # Check for duplicate restaurant names (case-insensitive)
        restaurant_name = cleaned_data.get('restaurant_name')
        if restaurant_name:
            from restaurant.models import Restaurant
            existing_restaurant = Restaurant.objects.filter(
                name__iexact=restaurant_name.strip()
            ).first()
            
            if existing_restaurant:
                raise forms.ValidationError(
                    f'A restaurant with the name "{restaurant_name}" already exists. '
                    'Please choose a unique name for your restaurant.'
                )
        
        # Validate phone number format (basic validation)
        phone = cleaned_data.get('phone')
        if phone:
            # Remove common separators
            phone_digits = ''.join(filter(str.isdigit, phone))
            
            if len(phone_digits) < 10:
                raise forms.ValidationError(
                    'Phone number must contain at least 10 digits.'
                )
            
            if len(phone_digits) > 15:
                raise forms.ValidationError(
                    'Phone number is too long. Please enter a valid phone number.'
                )
        
        # Validate minimum order and delivery fee
        minimum_order = cleaned_data.get('minimum_order')
        delivery_fee = cleaned_data.get('delivery_fee')
        
        if minimum_order is not None and minimum_order < 0:
            raise forms.ValidationError('Minimum order amount cannot be negative.')
        
        if delivery_fee is not None and delivery_fee < 0:
            raise forms.ValidationError('Delivery fee cannot be negative.')
        
        if minimum_order and delivery_fee:
            if delivery_fee > minimum_order:
                raise forms.ValidationError(
                    'Delivery fee should not exceed the minimum order amount.'
                )
        
        # Validate image file if provided
        image = cleaned_data.get('image')
        if image:
            # Check file size (max 5MB)
            if image.size > 5 * 1024 * 1024:  # 5MB in bytes
                raise forms.ValidationError(
                    'Image file size must not exceed 5MB. Please upload a smaller image.'
                )
            
            # Check file format
            allowed_formats = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp']
            if hasattr(image, 'content_type') and image.content_type not in allowed_formats:
                raise forms.ValidationError(
                    'Invalid image format. Please upload a JPEG, PNG, or WebP image.'
                )
        
        return cleaned_data
    
    def clean_restaurant_name(self):
        """
        Validate and clean restaurant name.
        
        Returns:
            str: Cleaned restaurant name
            
        Raises:
            forms.ValidationError: If name is invalid
        """
        name = self.cleaned_data.get('restaurant_name', '').strip()
        
        if not name:
            raise forms.ValidationError('Restaurant name is required.')
        
        if len(name) < 3:
            raise forms.ValidationError(
                'Restaurant name must be at least 3 characters long.'
            )
        
        if len(name) > 100:
            raise forms.ValidationError(
                'Restaurant name must not exceed 100 characters.'
            )
        
        # Check for inappropriate characters
        import re
        if not re.match(r'^[a-zA-Z0-9\s\-\'&.]+$', name):
            raise forms.ValidationError(
                'Restaurant name can only contain letters, numbers, spaces, hyphens, '
                'apostrophes, ampersands, and periods.'
            )
        
        return name
    
    def clean_description(self):
        """
        Validate and clean restaurant description.
        
        Returns:
            str: Cleaned description
            
        Raises:
            forms.ValidationError: If description is invalid
        """
        description = self.cleaned_data.get('description', '').strip()
        
        if not description:
            raise forms.ValidationError('Restaurant description is required.')
        
        if len(description) < 20:
            raise forms.ValidationError(
                'Please provide a more detailed description (at least 20 characters).'
            )
        
        if len(description) > 1000:
            raise forms.ValidationError(
                'Description is too long. Please keep it under 1000 characters.'
            )
        
        return description
    
    def clean_address(self):
        """
        Validate and clean restaurant address.
        
        Returns:
            str: Cleaned address
            
        Raises:
            forms.ValidationError: If address is invalid
        """
        address = self.cleaned_data.get('address', '').strip()
        
        if not address:
            raise forms.ValidationError('Restaurant address is required.')
        
        if len(address) < 10:
            raise forms.ValidationError(
                'Please provide a complete address (at least 10 characters).'
            )
        
        if len(address) > 500:
            raise forms.ValidationError(
                'Address is too long. Please keep it under 500 characters.'
            )
        
        return address
    
    def save(self, commit=True):
        """
        Save both the user account and restaurant profile.
        
        Creates a User account, assigns them to the Restaurant Owner group,
        and creates a Restaurant profile linked to the user.
        
        Args:
            commit: Whether to save to database
            
        Returns:
            tuple: (User object, Restaurant object)
        """
        # Create user account
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password']
        )
        
        # Assign user to Restaurant Owner group
        restaurant_group = Group.objects.filter(name='Restaurant Owner').first()
        if restaurant_group:
            user.groups.add(restaurant_group)
        
        # Create restaurant profile
        restaurant = Restaurant.objects.create(
            owner=user,
            name=self.cleaned_data['restaurant_name'],
            description=self.cleaned_data['description'],
            address=self.cleaned_data['address'],
            phone=self.cleaned_data['phone'],
            email=self.cleaned_data.get('restaurant_email'),
            cuisine_type=self.cleaned_data['cuisine_type'],
            opening_time=self.cleaned_data['opening_time'],
            closing_time=self.cleaned_data['closing_time'],
            minimum_order=self.cleaned_data['minimum_order'],
            delivery_fee=self.cleaned_data['delivery_fee'],
            image=self.cleaned_data.get('image'),
            is_active=False,  # Set to False until manager approval
            is_approved=False  # Set to False for pending approval
        )
        
        return user, restaurant
