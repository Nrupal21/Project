"""
Models for the accounts app.

This module contains the CustomUser model that extends the default Django User model
and the UserProfile model with additional fields specific to our travel platform.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.dispatch import receiver
from django.db.models.signals import post_save

# UUID for primary key
import uuid

class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifier
    for authentication instead of usernames.
    
    This manager is designed to work with MongoDB using Djongo.
    It provides methods for creating regular users and superusers with appropriate defaults.
    """
    use_in_migrations = True  # Allows this manager to be used in migrations
    
    def _create_user(self, email, password=None, **extra_fields):
        """
        Create and save a user with the given email and password.
        
        Args:
            email (str): The user's email address (required)
            password (str, optional): The user's password
            **extra_fields: Additional fields to be set on the user model
            
        Returns:
            CustomUser: The created user instance
            
        Raises:
            ValueError: If email is not provided
        """
        # Validate email is provided
        if not email:
            raise ValueError(_('The Email must be set'))
        
        # Normalize email (lowercase domain part)
        email = self.normalize_email(email)
        
        # Set default values if not provided
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', CustomUser.UserRole.USER)
        
        # Create the user instance
        user = self.model(email=email, **extra_fields)
        
        # Set password if provided
        if password:
            user.set_password(password)
            
        # Save the user to database
        user.save(using=self._db)
        return user
    
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular user with the given email and password.
        
        Args:
            email (str): The user's email address
            password (str, optional): The user's password
            **extra_fields: Additional fields to be set on the user model
            
        Returns:
            CustomUser: The created regular user instance
        """
        # Set default permissions for regular users
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        
        # Use the _create_user helper method
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        
        Args:
            email (str): The superuser's email address
            password (str, optional): The superuser's password
            **extra_fields: Additional fields to be set on the user model
            
        Returns:
            CustomUser: The created superuser instance
            
        Raises:
            ValueError: If is_staff or is_superuser is not True
        """
        # Set superuser defaults
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', CustomUser.UserRole.ADMIN)
        
        # Validate superuser flags
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        # Create and return the superuser
        return self._create_user(email, password, **extra_fields)
    
    def get_by_natural_key(self, username):
        """
        Retrieve a user by the case-insensitive email.
        This allows login with mixed-case email addresses.
        
        Args:
            username (str): Email address used for login (username field)
            
        Returns:
            CustomUser: The user matching the email address
        """
        return self.get(email__iexact=username)  # Case-insensitive lookup

class CustomUser(AbstractUser):
    """
    Custom user model that uses email as the unique identifier
    instead of username and includes role-based access control.
    
    This model extends Django's AbstractUser to provide email-based authentication 
    and role-based permissions. It uses UUID as the primary key.
    """
    # Define UserRole choices as a nested class for better organization and accessibility
    class UserRole(models.TextChoices):
        """
        User role choices for role-based access control.
        
        This is defined as a TextChoices class for Django's admin interface
        and form validation, but will be stored as a simple string in the database.
        
        Each role has different permissions and capabilities in the system:
        - ADMIN: Full system access and management rights
        - LOCAL_GUIDE: Can create and manage tours, attractions, etc.
        - HOTEL_OWNER: Can manage accommodations and related services
        - USER: Standard user with basic permissions
        """
        ADMIN = 'admin', _('Administrator')  # Full system access
        LOCAL_GUIDE = 'local_guide', _('Local Guide')  # Tour and destination management
        HOTEL_OWNER = 'hotel_owner', _('Hotel Owner')  # Accommodation management
        USER = 'user', _('Regular User')  # Standard user role
    # Use UUID as primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique identifier for the user")
    
    # User fields
    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(
        _('email address'), 
        unique=True,
        help_text=_('Required. Must be a valid email address.')
    )
    
    # Remove first_name and last_name from AbstractUser as they're not needed
    first_name = None
    last_name = None
    
    # Custom fields
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        default='',
        help_text=_('User\'s phone number')
    )
    
    is_verified = models.BooleanField(
        default=False,
        help_text=_('Whether the user has verified their email address')
    )
    
    role = models.CharField(
        _('role'),
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.USER,
        help_text=_('User role for access control')
    )
    
    # Required fields for Django's authentication
    is_active = models.BooleanField(
        default=True,
        help_text=_('Designates whether this user should be treated as active. Unselect this instead of deleting accounts.')
    )
    
    is_staff = models.BooleanField(
        default=False,
        help_text=_('Designates whether the user can log into this admin site.')
    )
    
    is_superuser = models.BooleanField(
        default=False,
        help_text=_('Designates that this user has all permissions without explicitly assigning them.')
    )
    
    date_joined = models.DateTimeField(
        auto_now_add=True,
        help_text=_('When the user account was created')
    )
    
    last_login = models.DateTimeField(
        null=True, 
        blank=True,
        help_text=_('Last login timestamp')
    )
    
    # Use email as the username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    objects = CustomUserManager()
    
    class Meta:
        """
        Meta class for CustomUser model.
        
        Configures the model's database representation and behavior.
        Defines the table name and indexes for efficient queries.
        """
        # Use 'auth_user' table in PostgreSQL
        db_table = 'auth_user'
        verbose_name = _('user')
        verbose_name_plural = _('users')
        
        # Add indexes for better query performance
        indexes = [
            models.Index(fields=['email'], name='email_idx'),
            models.Index(fields=['username'], name='username_idx'),
            models.Index(fields=['role'], name='role_idx'),
            models.Index(fields=['is_active'], name='is_active_idx'),
        ]
    
    def __str__(self):
        """Return a string representation of the user (email)."""
        return self.email
    
    @property
    def is_admin(self):
        """Check if user has admin role.
        
        Returns:
            bool: True if user has admin role, False otherwise
        """
        return self.role == self.UserRole.ADMIN or self.is_superuser
    
    @property
    def is_local_guide(self):
        """Check if user is a local guide.
        
        Returns:
            bool: True if user is a local guide, False otherwise
        """
        return self.role == self.UserRole.LOCAL_GUIDE
    
    @property
    def is_hotel_owner(self):
        """Check if user is a hotel owner.
        
        Returns:
            bool: True if user is a hotel owner, False otherwise
        """
        return self.role == self.UserRole.HOTEL_OWNER

class UserProfile(models.Model):
    """
    UserProfile model extends the CustomUser model with additional fields.
    
    This model stores additional user information that doesn't belong in the 
    authentication model. It has a one-to-one relationship with CustomUser 
    through the user field.
    """
    # Reference to CustomUser using OneToOneField
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    
    # Profile fields
    date_of_birth = models.DateField(
        null=True, 
        blank=True, 
        help_text="User's date of birth"
    )
    
    # For file storage, using URL to the image
    # In production, consider using a service like AWS S3 or Cloudinary
    profile_picture = models.URLField(
        max_length=500, 
        null=True, 
        blank=True, 
        help_text="URL to user's profile picture"
    )
    
    bio = models.TextField(
        blank=True, 
        help_text="Short bio or description about the user"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True, 
        help_text="When the profile was created"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True, 
        help_text="When the profile was last updated"
    )
    
    class Meta:
        """
        Meta class for UserProfile model.

        Configures the model's database representation and behavior.
        Defines the table name and indexes for efficient queries.
        """
        # Specify the table name in PostgreSQL database
        db_table = 'accounts_userprofile'
        # Human-readable names for Django admin
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')
        # Create index on 'user' field for faster lookups
        indexes = [
            models.Index(fields=['user'], name='user_idx')
        ]

    def __str__(self):
        """
        String representation of the UserProfile model.
        
        Returns:
            str: The username of the associated user followed by 'Profile'
        """
        # Safe access to username in case user reference is invalid
        return f"{self.user.username}'s Profile" if hasattr(self, 'user') and hasattr(self.user, 'username') else "Profile"

    @property
    def full_name(self):
        """
        Returns the full name of the user.
        
        Concatenates first name and last name if they exist, handling cases
        where either might be missing or the user reference is invalid.
        
        Returns:
            str: The user's full name (first name + last name), or empty string if not available
        """
        # Check if user attribute exists and has name attributes
        if hasattr(self, 'user') and hasattr(self.user, 'first_name') and hasattr(self.user, 'last_name'):
            return f"{self.user.first_name} {self.user.last_name}".strip()
        return ""

    def age(self):
        """
        Calculates the user's age based on their date of birth.
        
        Uses the date_of_birth field to calculate current age, accounting for
        whether the birthday has occurred this year or not.
        
        Returns:
            int or None: The user's age in years, or None if date of birth is not set
        """
        from datetime import date
        # Only calculate if date_of_birth is set
        if self.date_of_birth:
            today = date.today()
            # Calculate age considering month and day to handle birthdays correctly
            # Subtracts an extra year if birthday hasn't occurred yet this year
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None

@receiver(post_save, sender=CustomUser)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Signal receiver to create or update the user profile when a CustomUser instance is saved.
    
    Args:
        sender: The model class that sent the signal (CustomUser)
        instance: The actual CustomUser instance being saved
        created (bool): Whether this is a new record being created
        **kwargs: Additional keyword arguments
    """
    # When a new user is created, we need to set up associated records
    if created:
        try:
            # Create a user profile with default values
            UserProfile.objects.get_or_create(
                user=instance,
                defaults={
                    'bio': ''  # Initialize with empty bio
                }
            )
            
            # Create default user preferences with system defaults
            # These settings control user experience across the application
            UserPreferences.objects.get_or_create(
                user=instance,
                defaults={
                    'preferred_currency': 'USD',  # Default to US dollars
                    'language': 'en',  # Default to English
                    'newsletter_subscription': True,  # Opt-in by default
                    'marketing_emails': True  # Opt-in by default
                }
            )
            
            print(f"Created profile and preferences for user: {instance.email}")
            
        except Exception as e:
            # Log any errors that occur during profile/preferences creation
            # This helps with debugging and ensures the error doesn't crash the application
            print(f"Error creating user profile/preferences: {e}")
            import traceback
            traceback.print_exc()
    else:
        # If this is an update to an existing user rather than a new creation
        try:
            # Update the associated profile if the user already exists
            # First check if a user profile exists for this user
            try:
                # Try to retrieve the existing profile by user ID
                profile = UserProfile.objects.get(user=instance)
                # Update any profile fields if needed based on user changes
                # Currently we just save the profile, but custom logic could be added here
                profile.save()
            except UserProfile.DoesNotExist:
                # If no profile exists (unusual but possible due to data migrations or manual DB operations)
                # Create a new profile with default values
                UserProfile.objects.create(
                    user=instance,
                    bio=''
                )
            
            # Next, check if user preferences exist for this user
            try:
                # Try to retrieve existing preferences by user ID
                preferences = UserPreferences.objects.get(user=instance)
                # Update any preferences fields if needed based on user changes
                # Currently we just save the preferences, but custom logic could be added here
                preferences.save()
            except UserPreferences.DoesNotExist:
                # If no preferences exist, create them with default values
                # This ensures every user has preferences even if created through other means
                UserPreferences.objects.create(
                    user=instance,
                    preferred_currency='USD',  # Default to US dollars
                    language='en',  # Default to English
                    newsletter_subscription=True,  # Opt-in by default
                    marketing_emails=True  # Opt-in by default
                )
                
        except Exception as e:
            # Log any errors that occur during profile/preferences updating
            # This prevents the application from crashing if an update fails
            print(f"Error updating user profile/preferences: {e}")
            import traceback
            traceback.print_exc()

class UserPreferences(models.Model):
    """
    Model to store user preferences for the travel platform.
    
    This model stores user-specific preferences like language and notification settings.
    
    Attributes:
        user (OneToOneField): Reference to the CustomUser model
        preferred_currency (CharField): User's preferred currency
        language (CharField): User's preferred language
        newsletter_subscription (BooleanField): Whether the user wants to receive newsletters
        marketing_emails (BooleanField): Whether the user wants to receive marketing emails
        created_at (DateTimeField): When the preferences were created
        updated_at (DateTimeField): When the preferences were last updated
    """
    # Note: We don't define _id field explicitly as Djongo creates it automatically
    # Djongo will use its own auto-generated ObjectId field for the primary key
    
    # Constants for choices
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('JPY', 'Japanese Yen'),
        ('INR', 'Indian Rupee'),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German'),
        ('hi', 'Hindi'),
        ('ja', 'Japanese'),
    ]
    
    # Reference to CustomUser using ObjectId
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        primary_key=True,
        help_text="Reference to the user these preferences belong to"
    )
    
    # Preference fields
    preferred_currency = models.CharField(
        max_length=3, 
        choices=CURRENCY_CHOICES, 
        default='USD',
        help_text="User's preferred currency for displaying prices"
    )
    
    language = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        default='en',
        help_text="User's preferred language for the application"
    )
    
    newsletter_subscription = models.BooleanField(
        default=True,
        help_text="Whether the user wants to receive newsletters"
    )
    
    marketing_emails = models.BooleanField(
        default=True,
        help_text="Whether the user wants to receive marketing emails"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the preferences were created"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When the preferences were last updated"
    )
    
    class Meta:
        """
        Meta class for UserPreferences model.
        
        Configures the model's database representation and behavior in MongoDB.
        Defines the collection name and indexes for efficient queries.
        """
        # Use 'accounts_userpreferences' collection in MongoDB
        db_table = 'accounts_userpreferences'
        verbose_name = _('user preferences')
        verbose_name_plural = _('user preferences')
        
        # Add index on user field for faster lookups
        # Note: We don't use unique=True parameter here as it's not supported
        # by the current Djongo version. Uniqueness is enforced at the MongoDB level.
        indexes = [
            models.Index(fields=['user'], name='prefs_user_idx')
        ]

    def __str__(self):
        """
        String representation of the UserPreferences model.
        
        Returns:
            str: A string indicating the user's preferences
        """
        return f"Preferences for {self.user.email if hasattr(self, 'user') else 'unknown user'}"
