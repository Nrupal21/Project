"""
Models for the accounts app.

This module defines all database models related to user accounts,
including user profiles, preferences, roles, and related entities.
"""

import datetime
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.crypto import get_random_string
from django.conf import settings
import uuid

class CustomUserManager(BaseUserManager):
    """Custom user model manager where email is the unique identifier."""
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a user with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    """
    Custom User model with comprehensive role-based authentication.
    
    This model extends Django's AbstractUser to provide role-based access control
    with integrated permissions, allowing for a more flexible and granular
    authorization system all within a single user table.
    """
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Admin')
        MANAGER = 'MANAGER', _('Manager')
        LOCAL_GUIDE = 'LOCAL_GUIDE', _('Local Guide')
        TRAVELER = 'TRAVELER', _('Traveler')
    
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.TRAVELER)
    
    # JSON field to store role-specific permissions
    permissions = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text=_('JSON object containing role-specific permissions')
    )
    
    # Track when roles and permissions are assigned/modified
    role_assigned_at = models.DateTimeField(auto_now_add=True, null=True)
    role_assigned_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_roles'
    )
    
    # Add related_name to avoid reverse accessor clashes
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="custom_user_groups",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="custom_user_permissions",
        related_query_name="user",
    )
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        """
        Override save method to set default permissions based on role if not specified.
        
        This ensures every user has the appropriate permissions for their role,
        even when created without explicit permissions.
        """
        if not self.permissions:
            self.permissions = self.get_default_permissions_for_role()
        super().save(*args, **kwargs)
    
    def get_default_permissions_for_role(self):
        """
        Get default permissions for the user's role.
        
        Returns:
            dict: Dictionary of default permissions for the user's role
        """
        if self.role == self.Role.ADMIN:
            return {
                "destinations": {"create": True, "read": True, "update": True, "delete": True},
                "tours": {"create": True, "read": True, "update": True, "delete": True},
                "users": {"create": True, "read": True, "update": True, "delete": True}
            }
        elif self.role == self.Role.MANAGER:
            return {
                "destinations": {"create": True, "read": True, "update": True, "delete": False},
                "tours": {"create": True, "read": True, "update": True, "delete": False},
                "users": {"create": False, "read": True, "update": False, "delete": False}
            }
        elif self.role == self.Role.LOCAL_GUIDE:
            return {
                "destinations": {"create": False, "read": True, "update": False, "delete": False},
                "tours": {"create": False, "read": True, "update": True, "delete": False},
                "users": {"create": False, "read": False, "update": False, "delete": False}
            }
        else:  # TRAVELER or default
            return {
                "destinations": {"create": False, "read": True, "update": False, "delete": False},
                "tours": {"create": False, "read": True, "update": False, "delete": False},
                "users": {"create": False, "read": False, "update": False, "delete": False}
            }
    
    def has_module_permission(self, module_name):
        """
        Check if the user has any permission for the given module.
        
        Args:
            module_name: Name of the module to check permissions for
            
        Returns:
            bool: True if the user has any permission for the module, False otherwise
        """
        if self.is_superuser:
            return True
        
        return module_name in self.permissions and any(self.permissions[module_name].values())
    
    def has_object_permission(self, module_name, action, obj=None):
        """
        Check if the user has permission to perform the specified action on an object.
        
        Args:
            module_name: Name of the module containing the object
            action: Action to perform (create, read, update, delete)
            obj: The object to check permission for
            
        Returns:
            bool: True if the user has permission, False otherwise
        """
        if self.is_superuser:
            return True
            
        if module_name in self.permissions and action in self.permissions[module_name]:
            return self.permissions[module_name][action]
            
        return False
    
    @property
    def is_admin(self):
        """
        Check if the user has admin role.
        
        Returns:
            bool: True if the user is an admin, False otherwise
        """
        return self.role == self.Role.ADMIN or self.is_superuser
    
    @property
    def is_manager(self):
        """
        Check if the user has manager role.
        
        Returns:
            bool: True if the user is a manager, False otherwise
        """
        return self.role == self.Role.MANAGER or self.is_admin
    
    @property
    def is_local_guide(self):
        """
        Check if the user has local guide role.
        
        Returns:
            bool: True if the user is a local guide or higher role, False otherwise
        """
        return self.role == self.Role.LOCAL_GUIDE or self.is_manager


class UserProfile(models.Model):
    """
    Extends the built-in Django User model with additional fields.
    
    This model stores additional user information that isn't included
    in the default Django User model such as profile picture, bio,
    and contact information.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    
    # Preferences
    newsletter_subscription = models.BooleanField(default=False)
    email_notifications = models.BooleanField(default=True)
    
    # Location info for nearby recommendations
    latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    
    # Profile completion and verification
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        """
        Return a string representation of the user profile.
        
        Returns:
            str: Username of the associated user
        """
        return f"{self.user.username}'s Profile"
    
    @property
    def full_name(self):
        """
        Get the user's full name or username if not available.
        
        Returns:
            str: Full name or username
        """
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}"
        return self.user.username


class VerificationToken(models.Model):
    """
    Model for storing email verification tokens.
    
    This model is used to store tokens for email verification, password reset,
    and other verification purposes. Each token is associated with a user and
    has an expiration time for security.
    
    Attributes:
        TOKEN_TYPES: Choices for different types of verification tokens.
        token: The verification token string.
        user: The user associated with this token.
        token_type: The type of verification this token is used for.
        created_at: When the token was created.
        expires_at: When the token expires.
        is_used: Whether the token has been used.
    """
    
    class TokenType(models.TextChoices):
        """
        Types of verification tokens.
        
        EMAIL_VERIFICATION: For verifying user email addresses
        PASSWORD_RESET: For resetting user passwords
        ACCOUNT_RECOVERY: For recovering locked or disabled accounts
        """
        EMAIL_VERIFICATION = 'email_verification', _('Email Verification')
        PASSWORD_RESET = 'password_reset', _('Password Reset')
        ACCOUNT_RECOVERY = 'account_recovery', _('Account Recovery')
    
    # Token field with a maximum length of 100 characters
    token = models.CharField(max_length=100, unique=True)
    
    # User this token is associated with
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='verification_tokens'
    )
    
    # Type of verification token
    token_type = models.CharField(
        max_length=20,
        choices=TokenType.choices,
        default=TokenType.EMAIL_VERIFICATION
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    # Status
    is_used = models.BooleanField(default=False)
    
    class Meta:
        """
        Metadata options for the VerificationToken model.
        """
        verbose_name = _('Verification Token')
        verbose_name_plural = _('Verification Tokens')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'token_type', 'is_used']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        """
        Return a string representation of the verification token.
        
        Returns:
            str: A formatted string containing the user's email and token type
        """
        return f"{self.user.email} - {self.get_token_type_display()}"
    
    @classmethod
    def generate_token(cls, length=64):
        """
        Generate a secure random token.
        
        Args:
            length: Length of the token to generate (default: 64)
            
        Returns:
            str: A URL-safe random string of the specified length
        """
        return get_random_string(length=length)
    
    @classmethod
    def create_token(cls, user, token_type=TokenType.EMAIL_VERIFICATION, expires_in_hours=24):
        """
        Create a new verification token for a user.
        
        Args:
            user: The user to create the token for
            token_type: Type of token (from TokenType choices)
            expires_in_hours: Number of hours until the token expires
            
        Returns:
            VerificationToken: The newly created token instance
        """
        # Invalidate any existing tokens of the same type for this user
        cls.objects.filter(
            user=user,
            token_type=token_type,
            is_used=False
        ).update(is_used=True)
        
        # Calculate expiration time
        expires_at = timezone.now() + datetime.timedelta(hours=expires_in_hours)
        
        # Create and return the new token
        return cls.objects.create(
            token=cls.generate_token(),
            user=user,
            token_type=token_type,
            expires_at=expires_at
        )
    
    def is_valid(self):
        """
        Check if the token is valid (not used and not expired).
        
        Returns:
            bool: True if the token is valid, False otherwise
        """
        if self.is_used:
            return False
            
        if timezone.now() > self.expires_at:
            return False
            
        return True
    
    def mark_as_used(self):
        """
        Mark the token as used.
        
        Returns:
            bool: True if the token was successfully marked as used,
                  False if it was already used
        """
        if self.is_used:
            return False
            
        self.is_used = True
        self.save(update_fields=['is_used'])
        return True
        """
        Meta options for the UserProfile model.
        
        Defines verbose names.
        """
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'


class UserFavorite(models.Model):
    """
    Stores user favorites for destinations, tours, etc.
    
    This model allows users to save their favorite items for later reference.
    Uses a generic foreign key to allow favoriting different types of objects.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    content_type = models.CharField(max_length=100)  # 'destination', 'tour', etc.
    object_id = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        """
        Return a string representation of the user favorite.
        
        Returns:
            str: Description of the favorite item
        """
        return f"{self.user.username}'s favorite {self.content_type} #{self.object_id}"
    
    class Meta:
        """
        Meta options for the UserFavorite model.
        
        Defines unique constraints to prevent duplicate favorites.
        """
        unique_together = ['user', 'content_type', 'object_id']


class UserPreference(models.Model):
    """
    Stores user preferences for personalized recommendations.
    
    This model tracks user interests and preferences to provide
    better personalized content and recommendations.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    preferred_destinations = models.JSONField(default=dict, blank=True, null=True)
    travel_interests = models.JSONField(default=list, blank=True, null=True)
    budget_preference = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        """
        Return a string representation of the user preference.
        
        Returns:
            str: Username of the associated user
        """
        return f"{self.user.username}'s Preferences"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal handler to create a user profile when a new user is created.
    
    This ensures every user has an associated profile automatically.
    
    Args:
        sender: The model class that sent the signal (User)
        instance: The actual User instance being saved
        created: Boolean indicating if this is a new record
        **kwargs: Additional keyword arguments
    """
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Signal handler to save a user profile when the user is saved.
    
    This keeps the profile in sync with user updates.
    
    Args:
        sender: The model class that sent the signal (User)
        instance: The actual User instance being saved
        **kwargs: Additional keyword arguments
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()


class GuideApplication(models.Model):
    """
    Model for storing and tracking guide applications.
    
    This model manages the entire lifecycle of a user's application to become a local guide.
    It includes fields for application details, verification status, and review information.
    The model provides methods to approve or reject applications, which automatically
    update the user's role and maintain an audit trail of all actions.
    """
    class Status(models.TextChoices):
        """Application status choices."""
        PENDING = 'PENDING', _('Pending Review')
        UNDER_REVIEW = 'UNDER_REVIEW', _('Under Review')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')
    
    # Application Information
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='guide_applications',
        help_text=_('User who submitted the application')
    )
    application_date = models.DateTimeField(
        auto_now_add=True,
        help_text=_('Date and time when the application was submitted')
    )
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.PENDING,
        help_text=_('Current status of the application')
    )
    
    # Identification and Verification
    government_id = models.FileField(
        upload_to='guide_applications/ids/%Y/%m/%d/',
        help_text=_('Scanned copy of government-issued ID proof')
    )
    id_type = models.CharField(
        max_length=100, 
        help_text=_('Type of ID provided (e.g., Aadhaar, PAN, Passport, Driver\'s License)')
    )
    id_verification_status = models.BooleanField(
        default=False, 
        help_text=_('Indicates if the ID has been verified by an admin')
    )
    background_check_status = models.BooleanField(
        default=False, 
        help_text=_('Indicates if background check has been completed')
    )
    
    # Guide Information
    experience = models.TextField(
        help_text=_('Describe your experience as a local guide or in the tourism industry')
    )
    areas_of_expertise = models.TextField(
        help_text=_('List the cities, regions, or types of locations you have expertise in')
    )
    languages = models.JSONField(
        default=list, 
        help_text=_('List of languages you are fluent in (format: [{"language": "English", "proficiency": "Native"}])')
    )
    
    # Review Information
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_applications',
        help_text=_('Admin/Manager who reviewed the application')
    )
    review_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text=_('Date and time when the application was reviewed')
    )
    review_notes = models.TextField(
        null=True, 
        blank=True,
        help_text=_('Internal notes about the application review')
    )
    rejection_reason = models.TextField(
        null=True, 
        blank=True,
        help_text=_('Reason provided if the application was rejected')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Metadata options for the GuideApplication model."""
        verbose_name = _('Guide Application')
        verbose_name_plural = _('Guide Applications')
        ordering = ['-application_date']
        permissions = [
            ('can_review_applications', 'Can review guide applications'),
            ('can_verify_ids', 'Can verify government IDs'),
        ]

    def __str__(self):
        """
        Return a human-readable string representation of the guide application.
        
        Returns:
            str: A string containing the username and application status
        """
        return f"{self.user.get_full_name() or self.user.username} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        """
        Override the save method to add custom validation and processing.
        """
        # Ensure status is updated when verification status changes
        if self.pk and self.id_verification_status and self.background_check_status:
            if self.status == self.Status.PENDING:
                self.status = self.Status.UNDER_REVIEW
        
        # Call the parent class's save method
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        Get the URL for viewing this application.
        
        Returns:
            str: URL for the application detail view
        """
        from django.urls import reverse
        return reverse('accounts:review_guide_application', args=[str(self.id)])

    def approve_application(self, reviewed_by, notes=None):
        """
        Approve the guide application and update the user's role to LOCAL_GUIDE.
        
        This method performs the following actions:
        1. Updates the application status to APPROVED
        2. Records the reviewer and review date
        3. Updates the user's role to LOCAL_GUIDE
        4. Sends a notification to the user
        
        Args:
            reviewed_by (User): The admin/manager user who is approving the application
            notes (str, optional): Additional notes about the approval
            
        Returns:
            bool: True if the operation was successful, False otherwise
            
        Raises:
            ValueError: If the application is not in a valid state for approval
        """
        # Validate application can be approved
        if self.status == self.Status.APPROVED:
            raise ValueError("This application has already been approved.")
            
        if self.status == self.Status.REJECTED:
            raise ValueError("Cannot approve a rejected application.")
        
        try:
            with transaction.atomic():
                # Update application status
                self.status = self.Status.APPROVED
                self.reviewed_by = reviewed_by
                self.review_date = timezone.now()
                self.review_notes = notes
                self.save()
                
                # Update user role and permissions
                self.user.role = User.Role.LOCAL_GUIDE
                self.user.role_assigned_at = timezone.now()
                self.user.role_assigned_by = reviewed_by
                
                # Add user to Local Guides group if it exists
                try:
                    guides_group = Group.objects.get(name='Local Guides')
                    self.user.groups.add(guides_group)
                except Group.DoesNotExist:
                    pass  # Group doesn't exist, continue without it
                    
                self.user.save()
                
                # TODO: Send approval notification to user
                # send_guide_approval_notification(self.user)
                
                return True
                
        except Exception as e:
            # Log the error
            logger.error(f"Error approving guide application {self.id}: {str(e)}")
            return False

    def reject_application(self, reviewed_by, reason, notes=None):
        """
        Reject the guide application and notify the user.
        
        Args:
            reviewed_by (User): The admin/manager user who is rejecting the application
            reason (str): The reason for rejection
            notes (str, optional): Additional notes about the rejection
            
        Returns:
            bool: True if the operation was successful, False otherwise
            
        Raises:
            ValueError: If the application is not in a valid state for rejection
        """
        if not reason:
            raise ValueError("A rejection reason is required.")
            
        if self.status == self.Status.REJECTED:
            raise ValueError("This application has already been rejected.")
            
        if self.status == self.Status.APPROVED:
            raise ValueError("Cannot reject an approved application.")
        
        try:
            with transaction.atomic():
                # Update application status
                self.status = self.Status.REJECTED
                self.reviewed_by = reviewed_by
                self.review_date = timezone.now()
                self.rejection_reason = reason
                self.review_notes = notes
                self.save()
                
                # TODO: Send rejection notification to user
                # send_guide_rejection_notification(self.user, reason)
                
                return True
                
        except Exception as e:
            # Log the error
            logger.error(f"Error rejecting guide application {self.id}: {str(e)}")
            return False
            
    def get_status_badge_class(self):
        """
        Get the appropriate CSS class for displaying the status.
        
        Returns:
            str: Tailwind CSS classes for the status badge
        """
        status_classes = {
            self.Status.PENDING: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
            self.Status.UNDER_REVIEW: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
            self.Status.APPROVED: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
            self.Status.REJECTED: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
        }
        return status_classes.get(self.status, 'bg-gray-100 text-gray-800')

    @property
    def is_pending(self):
        """Check if the application is pending review."""
        return self.status == self.Status.PENDING
        
    @property
    def is_under_review(self):
        """Check if the application is under review."""
        return self.status == self.Status.UNDER_REVIEW
        
    @property
    def is_approved(self):
        """Check if the application has been approved."""
        return self.status == self.Status.APPROVED
        
    @property
    def is_rejected(self):
        """Check if the application has been rejected."""
        return self.status == self.Status.REJECTED

# ... (rest of the code remains the same)
