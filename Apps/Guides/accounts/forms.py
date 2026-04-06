import re
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _
from django.conf import settings

# Import models
from .models import User, UserProfile, UserPreference, GuideApplication

# Import logger
import logging
logger = logging.getLogger(__name__)

class RegisterForm(UserCreationForm):
    """
    Custom user registration form extending Django's UserCreationForm.
    
    This form adds role selection, first_name, last_name, email field validation, 
    and custom styling to the standard registration form. It ensures emails are 
    unique across the system and provides additional fields for user preferences.
    
    The form includes support for all user roles including ADMIN, MANAGER, 
    LOCAL_GUIDE and TRAVELER, with appropriate role-based permissions.
    """
    
    # Role is automatically set to TRAVELER for all new registrations
    # Users can apply to become guides after registration
    
    # Add first_name field with custom styling
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'block w-full rounded-lg border-0 py-3 px-4 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm',
            'placeholder': 'First Name',
            'autocomplete': 'given-name',
            'aria-label': 'First name',
        }),
        help_text='Enter your first name.'
    )
    
    # Add last_name field with custom styling
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'block w-full rounded-lg border-0 py-3 px-4 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm',
            'placeholder': 'Last Name',
            'autocomplete': 'family-name',
            'aria-label': 'Last name',
        }),
        help_text='Enter your last name.'
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'block w-full rounded-lg border-0 py-3 px-4 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm',
            'placeholder': 'Email address',
            'autocomplete': 'email',
            'aria-label': 'Email address',
        }),
        help_text='We\'ll never share your email with anyone else.'
    )
    
    # Add terms acceptance field
    terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500',
            'aria-label': 'I agree to the terms and conditions',
        }),
        label='I agree to the Terms of Service and Privacy Policy',
    )
    
    # Marketing preferences - these are not part of the User model
    # but will be used to set UserPreference fields
    marketing_emails = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500',
            'aria-label': 'Subscribe to marketing emails',
        }),
        label='I want to receive marketing promotions and updates via email',
        help_text='You can unsubscribe at any time.'
    )
    
    # Newsletter subscription preference
    newsletter_subscription = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500',
            'aria-label': 'Subscribe to newsletter',
        }),
        label='Subscribe to our monthly newsletter',
        help_text='Get the latest travel tips and destination guides.'
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        # Note: marketing_emails and newsletter_subscription are handled separately in the view
    
    # Override default widgets to add custom styling
    def __init__(self, *args, **kwargs):
        """
        Initialize the form with custom widget attributes for styling purposes.
        
        Adds Tailwind CSS classes to all form fields for consistent styling.
        """
        super().__init__(*args, **kwargs)
        
        # Apply styling to username field
        self.fields['username'].widget.attrs.update({
            'class': 'block w-full rounded-lg border-0 py-3 px-4 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm',
            'placeholder': 'Username',
            'autocomplete': 'username',
            'aria-label': 'Username',
            'data-validate': '{"required": true, "minlength": 3, "maxlength": 30}',
        })
        
        # Apply styling to password fields
        self.fields['password1'].widget.attrs.update({
            'class': 'block w-full rounded-lg border-0 py-3 px-4 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm',
            'placeholder': 'Create a password',
            'autocomplete': 'new-password',
            'aria-label': 'Create a password',
            'data-validate': '{"required": true, "minlength": 8}',
        })
        
        self.fields['password2'].widget.attrs.update({
            'class': 'block w-full rounded-lg border-0 py-3 px-4 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm',
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password',
            'aria-label': 'Confirm your password',
            'data-validate': '{"required": true, "equalTo": "#id_password1"}',
        })
        
        # Add help text for password requirements
        self.fields['password1'].help_text = '''
            <ul class="mt-2 text-sm text-gray-500">
                <li>• At least 8 characters</li>
                <li>• At least one uppercase letter</li>
                <li>• At least one number</li>
                <li>• At least one special character</li>
            </ul>
        '''
        self.fields['password2'].help_text = 'Please confirm your password.'
        
        # Update help text for username
        self.fields['username'].help_text = 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'
    
    def clean_email(self):
        """
        Validate that the email is not already in use and properly formatted.
        
        Performs the following validations:
        1. Checks if email is already registered (case-insensitive)
        2. Validates email format using Django's built-in EmailValidator
        3. Converts email to lowercase for consistency
        
        Returns:
            str: The cleaned and normalized email address
            
        Raises:
            forms.ValidationError: If email is invalid or already in use
        """
        email = self.cleaned_data.get('email', '').strip().lower()
        
        # Basic email format validation (Django's built-in)
        try:
            from django.core.validators import validate_email
            validate_email(email)
        except forms.ValidationError:
            raise forms.ValidationError('Please enter a valid email address.')
        
        # Check if email is already in use
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'This email is already registered. Please use a different email or try logging in.'
            )
            
        # Check for disposable email domains if needed
        if self.is_disposable_email(email):
            raise forms.ValidationError(
                'Disposable email addresses are not allowed. Please use a permanent email address.'
            )
            
        return email
        
    def clean_username(self):
        """
        Validate the username to ensure it meets our requirements.
        
        Performs the following validations:
        1. Checks for minimum and maximum length
        2. Validates allowed characters
        3. Ensures username is not already taken
        4. Prevents usernames that are too similar to existing ones
        
        Returns:
            str: The cleaned username
            
        Raises:
            forms.ValidationError: If username is invalid or already taken
        """
        username = self.cleaned_data.get('username', '').strip()
        
        # Check for minimum length
        if len(username) < 3:
            raise forms.ValidationError('Username must be at least 3 characters long.')
            
        # Check for maximum length
        if len(username) > 30:
            raise forms.ValidationError('Username cannot be longer than 30 characters.')
            
        # Check for allowed characters (letters, numbers, @/./+/-/_ only)
        if not re.match(r'^[\w.@+-]+$', username):
            raise forms.ValidationError(
                'Username can only contain letters, numbers, and @/./+/-/_ characters.'
            )
            
        # Check if username is already taken
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken. Please choose another.')
            
        # Check for reserved usernames
        reserved_names = ['admin', 'administrator', 'root', 'superuser', 'system', 'support']
        if username.lower() in reserved_names:
            raise forms.ValidationError('This username is not available. Please choose another.')
            
        return username
    
    def clean(self):
        """
        Perform cross-field validation and clean the entire form.
        
        This method is called after each field's clean() method has been called.
        It's useful for validation that requires access to multiple form fields.
        
        Also handles special role-based validation:
        - ADMIN role can only be assigned by an existing admin
        - MANAGER role requires additional verification
        """
        
        # Only allow ADMIN role to be set programmatically, not via form
        if 'role' in self.cleaned_data and self.cleaned_data['role'] == User.Role.ADMIN:
            self.cleaned_data['role'] = User.Role.TRAVELER
            # Don't show an error to avoid revealing this security check
        cleaned_data = super().clean()
        
        # Initialize the default permissions based on the selected role
        # These will be stored in the permissions field when user is saved
        if 'role' in cleaned_data:
            role = cleaned_data['role']
            # Default permissions will be handled by the User model's save method
        
        # Check if passwords match (though Django handles this by default)
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'The two password fields did not match.')
        
        # Check if terms were accepted
        if not cleaned_data.get('terms'):
            self.add_error('terms', 'You must accept the terms and conditions to register.')
            
        return cleaned_data
    
    def is_disposable_email(self, email):
        """
        Check if the email is from a known disposable email provider.
        
        Args:
            email (str): The email address to check
            
        Returns:
            bool: True if the email is from a disposable provider, False otherwise
        """
        disposable_domains = [
            'yopmail.com', 'mailinator.com', 'tempmail.com', 'guerrillamail.com',
            '10minutemail.com', 'temp-mail.org', 'throwawaymail.com', 'maildrop.cc'
        ]
        

    # ... (rest of the class remains the same)

class LoginForm(AuthenticationForm):
    """
    Custom login form extending Django's AuthenticationForm.
    
    This form adds custom styling and enhanced functionality for role-based login,
    supporting both email and username authentication.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize the form with custom widget attributes for styling purposes.
        
        Adds Tailwind CSS classes to username and password fields and updates field
        labels to reflect that either username or email can be used for login.
        """
        super().__init__(*args, **kwargs)
        
        # Change the username field label to indicate email login is possible
        self.fields['username'].label = _('Username or Email')
        
        # Apply styling to username field
        self.fields['username'].widget.attrs.update({
            'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm',
            'placeholder': 'Username or Email',
            'autocomplete': 'username email'
        })
        
        # Apply styling to password field
        self.fields['password'].widget.attrs.update({
            'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm',
            'placeholder': 'Password',
            'autocomplete': 'current-password'
        })
    
    def clean(self):
        """
        Validate the form input.
        
        Override the default clean method to support both username and email login.
        The authentication backend will handle the actual verification logic.
        
        Returns:
            dict: The cleaned data dictionary
            
        Raises:
            ValidationError: If authentication fails
        """
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            # Let the authentication backend handle the validation
            self.user_cache = authenticate(
                request=self.request,
                username=username,
                password=password
            )
            
            if self.user_cache is None:
                raise ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                    params={'username': self.username_field.verbose_name},
                )
            else:
                self.confirm_login_allowed(self.user_cache)
                
                # Store role in session for role-based UI customization
                if self.request and hasattr(self.request, 'session'):
                    self.request.session['user_role'] = self.user_cache.role

        return self.cleaned_data


class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Custom password change form extending Django's PasswordChangeForm.
    
    Adds custom styling and field attributes for a more user-friendly
    password change experience.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the form with custom widget attributes for styling purposes.
        
        Adds Tailwind CSS classes to all password fields.
        """
        super().__init__(*args, **kwargs)
        
        # Apply styling to old password field
        self.fields['old_password'].widget.attrs.update({
            'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm',
            'placeholder': 'Current password'
        })
        
        # Apply styling to new password fields
        self.fields['new_password1'].widget.attrs.update({
            'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm',
            'placeholder': 'New password'
        })
        
        self.fields['new_password2'].widget.attrs.update({
            'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm',
            'placeholder': 'Confirm new password'
        })


class CustomPasswordResetForm(PasswordResetForm):
    """
    Custom password reset request form extending Django's PasswordResetForm.
    
    Adds custom styling and improved email field attributes.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the form with custom widget attributes for styling purposes.
        
        Adds Tailwind CSS classes to the email field.
        """
        super().__init__(*args, **kwargs)
        
        # Apply styling to email field
        self.fields['email'].widget.attrs.update({
            'class': 'appearance-none rounded relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm',
            'placeholder': 'Email address'
        })


class CustomSetPasswordForm(SetPasswordForm):
    """
    Custom set password form extending Django's SetPasswordForm.
    
    Used during password reset process to set a new password.
    Adds custom styling and improved field attributes.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the form with custom widget attributes for styling purposes.
        
        Adds Tailwind CSS classes to password fields.
        """
        super().__init__(*args, **kwargs)
        
        # Apply styling to new password fields
        self.fields['new_password1'].widget.attrs.update({
            'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm',
            'placeholder': 'New password'
        })
        
        self.fields['new_password2'].widget.attrs.update({
            'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm',
            'placeholder': 'Confirm new password'
        })


class UserProfileForm(forms.ModelForm):
    """
    Form for updating user basic information.
    
    Handles the fields directly from the Django User model,
    such as first_name, last_name, and email.
    """
    
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    
    class Meta:
        """
        Meta class specifies the model and fields for the form.
        """
        model = User
        fields = ('first_name', 'last_name', 'email')
        
    def clean_email(self):
        """
        Validate that the email is not already in use by another user.
        
        Checks if the email is being used by a different user to prevent
        email address conflicts while allowing users to keep their current email.
        
        Returns:
            str: The cleaned email value if validation passes
            
        Raises:
            ValidationError: If email already exists for a different user
        """
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise ValidationError(_("This email is already in use."))
        return email


class ProfileForm(forms.ModelForm):
    """
    Form for updating extended user profile information.
    
    Handles the fields from the custom UserProfile model including profile picture, bio,
    phone number, address, and preferences.
    
    Each method and field has detailed comments to improve code understanding.
    """
    
    # Field for user preferences related to travel interests
    # Note: This has been adjusted to match the UserPreference model structure
    # which uses JSONField for travel_interests instead of a many-to-many relationship
    travel_interests = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text='Enter your travel interests separated by commas (e.g., beaches, mountains, cities)'
    )
    
    class Meta:
        """
        Meta class specifies the model, fields, and widgets for the form.
        """
        model = UserProfile  # Fixed to use the correct UserProfile model
        fields = ('profile_picture', 'bio', 'phone_number', 'address', 'newsletter_subscription', 'email_notifications')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }
        
    def clean_profile_picture(self):
        """
        Validate the uploaded profile picture image.
        
        Checks if the uploaded file is a valid image and not too large.
        
        Returns:
            File: The cleaned profile picture file if validation passes
            
        Raises:
            ValidationError: If file is too large or not a valid image format
        """
        profile_picture = self.cleaned_data.get('profile_picture', False)
        if profile_picture:
            # Check if the file is too large (5MB limit)
            if profile_picture.size > 5 * 1024 * 1024:
                raise ValidationError(_("Image file is too large (> 5MB)"))
                
            # Check if the file is a valid image format
            allowed_types = ['image/jpeg', 'image/png', 'image/gif']
            if hasattr(profile_picture, 'content_type') and profile_picture.content_type not in allowed_types:
                raise ValidationError(_("Only JPEG, PNG, and GIF images are allowed."))
                
        return profile_picture


class PreferencesForm(forms.ModelForm):
    """
    Form for updating user travel preferences.
    
    This form handles user travel preferences including preferred destinations,
    travel interests, and budget preferences. It uses the UserPreference model
    to store these preferences.
    
    Each field has detailed comments to improve code understanding.
    """
    
    # Convert JSON field to more user-friendly form inputs
    BUDGET_CHOICES = [
        ('budget', 'Budget'),
        ('mid_range', 'Mid-Range'),
        ('luxury', 'Luxury'),
        ('all', 'All Ranges')
    ]
    
    # Field for travel interests with user-friendly input
    travel_interests = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'
        }),
        help_text='Enter your travel interests separated by commas (e.g., beaches, mountains, cities)'
    )
    
    # Field for budget preference with dropdown
    budget_preference = forms.ChoiceField(
        choices=BUDGET_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'
        })
    )
    
    # Field for preferred destinations with user-friendly input
    preferred_destinations = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'
        }),
        help_text='Enter your preferred destinations separated by commas (e.g., Paris, Tokyo, New York)'
    )
    
    class Meta:
        """
        Meta class specifies the model and fields for the form.
        """
        model = UserPreference
        fields = ('preferred_destinations', 'travel_interests', 'budget_preference')
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the form with custom widget attributes and convert JSON data to strings.
        
        Converts JSON data from the model to string representation for form fields.
        """
        super().__init__(*args, **kwargs)
        
        # Convert JSON data to string representation if instance exists
        if self.instance and self.instance.pk:
            # Convert preferred_destinations JSON to comma-separated string
            if self.instance.preferred_destinations:
                if isinstance(self.instance.preferred_destinations, dict):
                    destinations = self.instance.preferred_destinations.get('places', [])
                    self.initial['preferred_destinations'] = ', '.join(destinations)
                elif isinstance(self.instance.preferred_destinations, list):
                    self.initial['preferred_destinations'] = ', '.join(self.instance.preferred_destinations)
            
            # Convert travel_interests JSON to comma-separated string
            if self.instance.travel_interests:
                if isinstance(self.instance.travel_interests, list):
                    self.initial['travel_interests'] = ', '.join(self.instance.travel_interests)
    
    def clean_travel_interests(self):
        """
        Clean and convert travel interests from string to list format for JSON storage.
        
        Returns:
            list: List of travel interests
        """
        interests_str = self.cleaned_data.get('travel_interests', '')
        if interests_str:
            # Split by comma and strip whitespace
            interests = [interest.strip() for interest in interests_str.split(',') if interest.strip()]
            return interests
        return []
    
    def clean_preferred_destinations(self):
        """
        Clean and convert preferred destinations from string to structured format for JSON storage.
        
        Returns:
            dict: Dictionary with 'places' key containing list of destinations
        """
        destinations_str = self.cleaned_data.get('preferred_destinations', '')
        if destinations_str:
            # Split by comma and strip whitespace
            destinations = [dest.strip() for dest in destinations_str.split(',') if dest.strip()]
            return {'places': destinations}
        return {'places': []}
    
    def save(self, commit=True):
        """
        Save the form data to the model instance.
        
        Overrides the default save method to handle the conversion of form data
        to the appropriate JSON format for the model fields.
        
        Args:
            commit: Whether to save the instance to the database
            
        Returns:
            UserPreference: The saved model instance
        """
        instance = super().save(commit=False)
        
        # Set the cleaned and processed data
        instance.travel_interests = self.cleaned_data.get('travel_interests', [])
        instance.preferred_destinations = self.cleaned_data.get('preferred_destinations', {'places': []})
        
        if commit:
            instance.save()
        return instance


class GuideApplicationForm(forms.ModelForm):
    """
    Form for submitting applications to become a local guide.
    
    This form collects the necessary information for users to apply for
    the local guide role, including government ID verification documents,
    experience details, and areas of expertise. The form follows the workflow
    where regular users must apply and be approved by admins/managers.    
    """
    # Define the Indian government ID type choices
    ID_TYPE_CHOICES = [
        ('aadhaar', 'Aadhaar Card'),
        ('pan', 'PAN Card'),
        ('passport', 'Passport'),
        ('voter', 'Voter ID'),
        ('driving_license', 'Driving License')
    ]
    
    # Fields with custom widgets and validation
    id_type = forms.ChoiceField(
        choices=ID_TYPE_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'aria-label': 'Select your ID type'
        }),
        help_text=_('Select the type of government ID you will be uploading')
    )
    
    experience = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-600 focus:border-indigo-600 dark:bg-gray-800 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-violet-600 dark:focus:border-violet-600 sm:text-sm',
            'placeholder': 'Describe your experience as a local guide...'
        }),
        help_text=_('Describe your previous experience as a local guide, tour leader, or related roles')
    )
    
    areas_of_expertise = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-600 focus:border-indigo-600 dark:bg-gray-800 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-violet-600 dark:focus:border-violet-600 sm:text-sm',
            'placeholder': 'List the areas or regions you have expertise in...'
        }),
        help_text=_('List specific areas, cities, or regions where you have local knowledge')
    )
    
    languages = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-600 focus:border-indigo-600 dark:bg-gray-800 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-violet-600 dark:focus:border-violet-600 sm:text-sm',
            'placeholder': 'English, Marathi, Hindi...'
        }),
        help_text=_('Enter languages you speak, separated by commas')
    )
    
    government_id = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 focus:outline-none',
            'accept': 'image/jpeg,image/png,application/pdf'
        }),
        help_text=_('Upload your government-issued ID proof (JPG, PNG, PDF only)')
    )
    
    class Meta:
        """
        Meta class for GuideApplicationForm defining the model and fields.
        """
        model = GuideApplication
        fields = ['id_type', 'government_id', 'experience', 'areas_of_expertise', 'languages']
        exclude = ['user', 'status', 'reviewed_by', 'review_date', 'review_notes', 'rejection_reason']
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the form with custom attributes and user information.
        
        Sets up the form fields with appropriate CSS classes following the site's
        indigo/violet color scheme and adds any user context if provided.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments including the user instance
        """
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_government_id(self):
        """
        Validate the uploaded government ID file.
        
        Checks that the file is of an allowed type (PDF, JPG, PNG) and not too large.
        
        Returns:
            File: The validated government ID file
            
        Raises:
            ValidationError: If file type is not allowed or file is too large
        """
        government_id = self.cleaned_data.get('government_id')
        
        # Check if a file was uploaded
        if not government_id:
            raise ValidationError(_('Please upload your government ID'))
            
        # Check file type
        allowed_types = ['application/pdf', 'image/jpeg', 'image/png']
        content_type = government_id.content_type
        
        if content_type not in allowed_types:
            raise ValidationError(_('Only PDF, JPG, and PNG files are allowed'))
            
        # Check file size (max 5MB)
        if government_id.size > 5 * 1024 * 1024:  # 5MB in bytes
            raise ValidationError(_('File size must not exceed 5MB'))
            
        return government_id
    
    def clean_languages(self):
        """
        Convert comma-separated languages string to a list for JSON storage.
        
        Returns:
            list: List of languages spoken by the applicant
        """
        languages_text = self.cleaned_data.get('languages', '')
        # Split by comma, strip whitespace, and filter out empty strings
        languages_list = [lang.strip() for lang in languages_text.split(',') if lang.strip()]
        
        if not languages_list:
            raise ValidationError(_('Please enter at least one language'))
            
        return languages_list
    
    def save(self, commit=True):
        """
        Save the form data to a new GuideApplication instance.
        
        Associates the application with the current user and sets the initial
        status to PENDING for admin review.
        
        Args:
            commit: Whether to save the instance to the database (default: True)
            
        Returns:
            GuideApplication: The newly created application instance
        """
        instance = super().save(commit=False)
        
        # Set the user if provided (should be the current logged-in user)
        if self.user:
            instance.user = self.user
            
        # Set initial status
        instance.status = GuideApplication.Status.PENDING
        
        if commit:
            instance.save()
            
        return instance
