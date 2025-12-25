"""
Customer app models.
Contains user profile and customer-related models for the food ordering system.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.urls import reverse
from orders.models import Order
from menu.models import MenuItem
from restaurant.models import Restaurant
from core.encryption import EncryptionManager
import uuid


class UserProfile(models.Model):
    """
    Extended user profile model linked to Django's User model.
    
    Stores additional customer information essential for food ordering:
    - Contact information for delivery notifications
    - Personal details for better user experience
    - Address information for food delivery
    
    This model extends the User model without modifying Django's built-in User,
    making it migration-safe and following Django best practices.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='profile',
        help_text='Link to the Django User account'
    )
    
    # User Role Field
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('restaurant_owner', 'Restaurant Owner'),
        ('manager', 'Manager'),
        ('admin', 'Administrator'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='customer',
        help_text='Primary role of the user in the system'
    )
    
    # Personal Information - Encrypted Fields
    # Full name stored encrypted for privacy protection
    _full_name_encrypted = models.TextField(
        blank=True,
        null=True,
        help_text='Encrypted full name for delivery and personalization'
    )
    
    # Phone number stored encrypted for security
    _phone_number_encrypted = models.TextField(
        blank=True,
        null=True,
        help_text='Encrypted phone number for order notifications and delivery contact'
    )
    
    # Address Information - Encrypted Fields
    # Physical address stored encrypted for privacy
    _address_encrypted = models.TextField(
        blank=True,
        null=True,
        help_text='Encrypted delivery address for food orders'
    )
    
    city = models.CharField(
        max_length=100,
        blank=True,
        help_text='City for delivery'
    )
    
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        help_text='Postal/ZIP code for delivery'
    )
    
    # Preferences
    dietary_preferences = models.CharField(
        max_length=200,
        blank=True,
        help_text='Dietary preferences (e.g., vegetarian, vegan, allergies)'
    )
    
    # Profile Settings
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True,
        help_text='Profile picture for personalization'
    )
    
    # Loyalty Points System
    points_balance = models.PositiveIntegerField(
        default=0,
        help_text='Current loyalty points balance for the user'
    )
    
    # Property methods for transparent encryption/decryption
    @property
    def full_name(self):
        """
        Get decrypted full name.
        
        Transparently decrypts the full name when accessed.
        
        Returns:
            str: Decrypted full name or empty string
        """
        return EncryptionManager.decrypt(self._full_name_encrypted) or ''
    
    @full_name.setter
    def full_name(self, value):
        """
        Set and encrypt full name.
        
        Transparently encrypts the full name when set.
        
        Args:
            value (str): Plaintext full name to encrypt
        """
        self._full_name_encrypted = EncryptionManager.encrypt(value)
    
    @property
    def phone_number(self):
        """
        Get decrypted phone number.
        
        Transparently decrypts the phone number when accessed.
        
        Returns:
            str: Decrypted phone number or empty string
        """
        return EncryptionManager.decrypt(self._phone_number_encrypted) or ''
    
    @phone_number.setter
    def phone_number(self, value):
        """
        Set and encrypt phone number.
        
        Transparently encrypts the phone number when set.
        
        Args:
            value (str): Plaintext phone number to encrypt
        """
        self._phone_number_encrypted = EncryptionManager.encrypt(value)
    
    @property
    def address(self):
        """
        Get decrypted address.
        
        Transparently decrypts the address when accessed.
        
        Returns:
            str: Decrypted address or empty string
        """
        return EncryptionManager.decrypt(self._address_encrypted) or ''
    
    @address.setter
    def address(self, value):
        """
        Set and encrypt address.
        
        Transparently encrypts the address when set.
        
        Args:
            value (str): Plaintext address to encrypt
        """
        self._address_encrypted = EncryptionManager.encrypt(value)
    
    def get_image_url(self):
        """
        Get user profile picture URL with intelligent fallback system.
        
        Returns database image if available, otherwise falls back to
        default avatar images based on user type and preferences.
        Includes multiple layers of error handling for robustness.
        
        Returns:
            str: Complete image URL for display in templates
        """
        try:
            # First try to get the uploaded image from database
            if self.profile_picture and hasattr(self.profile_picture, 'url'):
                return self.profile_picture.url
        except (ValueError, AttributeError, OSError):
            # Handle cases where image file is missing, corrupted, or inaccessible
            pass
        
        try:
            # Fallback to default avatar images
            # Use user's first letter of name or default avatar
            first_letter = self.full_name[0].upper() if self.full_name else self.user.username[0].upper()
            
            # Generate avatar URL based on user preferences
            avatar_url = f'https://ui-avatars.com/api/?name={first_letter}&background=random&color=fff'
            return avatar_url
        except (AttributeError, IndexError):
            # Handle cases where user data is missing or corrupted
            pass
        
        # Ultimate fallback - hardcoded reliable avatar
        return 'https://ui-avatars.com/api/?name=User&background=6366f1&color=fff'
    
    def get_thumbnail_url(self):
        """
        Get thumbnail version of user profile picture.
        
        Returns:
            str: Thumbnail image URL or fallback
        """
        # For now, return same as get_image_url()
        # TODO: Implement actual thumbnail generation
        return self.get_image_url()
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the profile was created'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='When the profile was last updated'
    )
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        ordering = ['-created_at']
    
    def __str__(self):
        """
        String representation of the user profile.
        
        Returns:
            str: Full name or username if full name not available
        """
        return self.full_name or self.user.username
    
    def get_full_address(self):
        """
        Get formatted full address.
        
        Returns:
            str: Complete address formatted for display
        """
        address_parts = []
        if self.address:
            address_parts.append(self.address)
        if self.city:
            address_parts.append(self.city)
        if self.postal_code:
            address_parts.append(self.postal_code)
        return ', '.join(address_parts) if address_parts else 'No address provided'
    
    def has_delivery_address(self):
        """
        Check if user has a complete delivery address.
        
        Returns:
            bool: True if address is complete enough for delivery
        """
        return bool(self.address and self.city)


# Signal to automatically create UserProfile when User is created
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create a UserProfile when a new User is created.
    
    This signal ensures that every user gets a profile automatically
    without requiring manual profile creation.
    
    Args:
        sender: The model class (User)
        instance: The actual instance being saved
        created: Boolean indicating if this is a new creation
    """
    if created:
        UserProfile.objects.create(user=instance, full_name=instance.username)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Automatically save the UserProfile when the User is saved.
    
    This ensures the profile stays synchronized with the user.
    
    Args:
        sender: The model class (User)
        instance: The actual instance being saved
    """
    # Only save profile if it exists to avoid authentication interference
    if hasattr(instance, 'profile'):
        instance.profile.save()

@receiver(post_save, sender=UserProfile)
def sync_user_role_with_groups(sender, instance, created, **kwargs):
    """
    Synchronize the user role field with Django group membership.
    
    This signal ensures that the role field stays consistent with group membership,
    maintaining backward compatibility with the existing group-based system.
    
    Args:
        sender: The model class (UserProfile)
        instance: The UserProfile instance being saved
        created: Boolean indicating if this is a new creation
    """
    from django.contrib.auth.models import Group
    
    # Prevent infinite recursion by checking if we're already syncing
    if hasattr(instance, '_syncing_groups'):
        return
    
    # Mark that we're syncing to prevent recursion
    instance._syncing_groups = True
    
    try:
        # Ensure the role field is set
        if not instance.role:
            instance.role = 'customer'
            instance.save(update_fields=['role'])
        
        # Sync role with groups
        if instance.role == 'restaurant_owner':
            group, _ = Group.objects.get_or_create(name='Restaurant Owner')
            instance.user.groups.add(group)
        elif instance.role == 'manager':
            # Add to both Restaurant Owner and Manager groups for managers
            restaurant_group, _ = Group.objects.get_or_create(name='Restaurant Owner')
            manager_group, _ = Group.objects.get_or_create(name='Manager')
            instance.user.groups.add(restaurant_group, manager_group)
        elif instance.role == 'admin':
            instance.user.is_staff = True
            instance.user.is_superuser = True
            instance.user.save(update_fields=['is_staff', 'is_superuser'])
    finally:
        # Clean up the flag
        if hasattr(instance, '_syncing_groups'):
            delattr(instance, '_syncing_groups')


class RestaurantReview(models.Model):
    """
    Customer reviews and ratings for restaurants.
    
    Allows customers to rate and review restaurants they've ordered from,
    helping other customers make informed decisions and providing
    valuable feedback to restaurant owners.
    """
    # Relationships
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='restaurant_reviews',
        help_text='Customer who wrote the review'
    )
    
    restaurant = models.ForeignKey(
        'restaurant.Restaurant',
        on_delete=models.CASCADE,
        related_name='reviews',
        help_text='Restaurant being reviewed'
    )
    
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviews',
        help_text='Order associated with this review'
    )
    
    # Review Content
    rating = models.PositiveSmallIntegerField(
        choices=[(i, f'{i} Stars') for i in range(1, 6)],
        help_text='Rating from 1 to 5 stars'
    )
    
    title = models.CharField(
        max_length=200,
        help_text='Review title or summary'
    )
    
    comment = models.TextField(
        help_text='Detailed review comment'
    )
    
    # Additional Ratings
    food_quality = models.PositiveSmallIntegerField(
        choices=[(i, f'{i} Stars') for i in range(1, 6)],
        default=5,
        help_text='Food quality rating'
    )
    
    service_quality = models.PositiveSmallIntegerField(
        choices=[(i, f'{i} Stars') for i in range(1, 6)],
        default=5,
        help_text='Service quality rating'
    )
    
    delivery_speed = models.PositiveSmallIntegerField(
        choices=[(i, f'{i} Stars') for i in range(1, 6)],
        default=5,
        help_text='Delivery speed rating'
    )
    
    value_for_money = models.PositiveSmallIntegerField(
        choices=[(i, f'{i} Stars') for i in range(1, 6)],
        default=5,
        help_text='Value for money rating'
    )
    
    # Moderation
    is_approved = models.BooleanField(
        default=True,
        help_text='Whether review is approved for public display'
    )
    
    is_verified_purchase = models.BooleanField(
        default=False,
        help_text='Whether this review is from a verified order'
    )
    
    is_flagged = models.BooleanField(
        default=False,
        help_text='Whether this review has been flagged for moderation'
    )
    
    is_hidden = models.BooleanField(
        default=False,
        help_text='Whether this review is hidden from public view'
    )
    
    flag_reason = models.TextField(
        blank=True,
        null=True,
        help_text='Reason why this review was flagged'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the review was created'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='When the review was last updated'
    )
    
    class Meta:
        verbose_name = 'Restaurant Review'
        verbose_name_plural = 'Restaurant Reviews'
        ordering = ['-created_at']
        unique_together = ['user', 'restaurant', 'order']
        indexes = [
            models.Index(fields=['restaurant', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_approved']),
        ]
    
    def __str__(self):
        """
        String representation of the review.
        
        Returns:
            str: Review summary with user and restaurant
        """
        return f'{self.user.username} - {self.restaurant.name} ({self.rating} stars)'
    
    def get_average_rating(self):
        """
        Calculate average of all rating categories.
        
        Returns:
            float: Average rating across all categories
        """
        return (self.rating + self.food_quality + self.delivery_speed + self.value_for_money) / 4
    
    @property
    def is_editable(self):
        """
        Check if the review can still be edited.
        
        Returns:
            bool: True if review was created within last 7 days
        """
        from django.utils import timezone
        return (timezone.now() - self.created_at).days <= 7
    
    def save(self, *args, **kwargs):
        """
        Override save to check if review is from verified purchase.
        """
        if self.order and self.order.user == self.user:
            self.is_verified_purchase = True
        super().save(*args, **kwargs)


class Wishlist(models.Model):
    """
    Customer wishlist for favorite restaurants.
    
    Allows customers to save their favorite restaurants for quick access
    and future orders, improving user engagement and retention.
    """
    # Relationships
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='wishlist_items',
        help_text='Customer who owns this wishlist item'
    )
    
    restaurant = models.ForeignKey(
        'restaurant.Restaurant',
        on_delete=models.CASCADE,
        related_name='wishlisted_by',
        help_text='Restaurant added to wishlist'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the restaurant was added to wishlist'
    )
    
    class Meta:
        verbose_name = 'Wishlist Item'
        verbose_name_plural = 'Wishlist Items'
        ordering = ['-created_at']
        unique_together = ['user', 'restaurant']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        """
        String representation of the wishlist item.
        
        Returns:
            str: User and restaurant name
        """
        return f'{self.user.username} - {self.restaurant.name}'


class MenuItemReview(models.Model):
    """
    Review model for specific menu items.
    
    Allows customers to review individual dishes from their orders.
    """
    
    # Core Relationships
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='menu_item_reviews',
        help_text='Customer who wrote the review'
    )
    
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name='reviews',
        help_text='Menu item being reviewed'
    )
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='menu_item_reviews',
        null=True,
        blank=True,
        help_text='Order that contained this menu item (verified purchase)'
    )
    
    # Review Content
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Menu item rating from 1 to 5 stars'
    )
    
    comment = models.TextField(
        blank=True,
        help_text='Detailed review text for the menu item'
    )
    
    # Specific Aspects
    taste = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
        help_text='Taste rating (1-5)'
    )
    
    presentation = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
        help_text='Presentation rating (1-5)'
    )
    
    portion_size = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
        help_text='Portion size rating (1-5)'
    )
    
    # Moderation
    is_flagged = models.BooleanField(
        default=False,
        help_text='Review has been flagged for moderation'
    )
    
    is_hidden = models.BooleanField(
        default=False,
        help_text='Review is hidden from public view'
    )
    
    flag_reason = models.TextField(
        blank=True,
        help_text='Reason why this review was flagged'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the review was created'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='When the review was last updated'
    )
    
    class Meta:
        verbose_name = 'Menu Item Review'
        verbose_name_plural = 'Menu Item Reviews'
        ordering = ['-created_at']
        unique_together = ['user', 'order', 'menu_item']  # Prevent duplicate reviews
        indexes = [
            models.Index(fields=['menu_item', 'created_at']),
            models.Index(fields=['rating']),
            models.Index(fields=['is_flagged']),
        ]
    
    def __str__(self):
        """
        String representation of the menu item review.
        
        Returns:
            str: Review summary with user, menu item, and rating
        """
        return f"{self.user.username} - {self.menu_item.name} ({self.rating}/5)"
    
    @property
    def is_editable(self):
        """
        Check if the review can still be edited.
        
        Returns:
            bool: True if review was created within last 7 days
        """
        from django.utils import timezone
        return (timezone.now() - self.created_at).days <= 7


class ReviewResponse(models.Model):
    """
    Restaurant owner responses to customer reviews.
    
    Allows restaurant owners to publicly respond to feedback.
    """
    
    # Relationships
    restaurant_review = models.ForeignKey(
        RestaurantReview,
        on_delete=models.CASCADE,
        related_name='responses',
        null=True,
        blank=True,
        help_text='Restaurant review being responded to'
    )
    
    menu_item_review = models.ForeignKey(
        MenuItemReview,
        on_delete=models.CASCADE,
        related_name='responses',
        null=True,
        blank=True,
        help_text='Menu item review being responded to'
    )
    
    responder = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='review_responses',
        help_text='Restaurant owner/manager who wrote the response'
    )
    
    # Response Content
    response = models.TextField(
        help_text='Response text from restaurant owner'
    )
    
    is_public = models.BooleanField(
        default=True,
        help_text='Whether this response is visible to customers'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the response was created'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='When the response was last updated'
    )
    
    class Meta:
        verbose_name = 'Review Response'
        verbose_name_plural = 'Review Responses'
        ordering = ['-created_at']
    
    def __str__(self):
        """
        String representation of the review response.
        
        Returns:
            str: Response summary with responder and review type
        """
        if self.restaurant_review:
            return f"Response to {self.restaurant_review}"
        elif self.menu_item_review:
            return f"Response to {self.menu_item_review}"
        return f"Response by {self.responder.username}"
    
    def get_review(self):
        """
        Get the associated review (restaurant or menu item).
        
        Returns:
            Review: The review being responded to
        """
        return self.restaurant_review or self.menu_item_review


class EmailPreference(models.Model):
    """
    User email preferences and consent management.
    
    Tracks user consent for different types of email communications
    to ensure compliance with email regulations and user preferences.
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='email_preferences',
        help_text='User who owns these email preferences'
    )
    
    # Email Consent Types
    transactional_emails = models.BooleanField(
        default=True,
        help_text='Order confirmations, status updates, password resets'
    )
    
    promotional_emails = models.BooleanField(
        default=False,
        help_text='Marketing emails, special offers, new restaurant announcements'
    )
    
    newsletter_emails = models.BooleanField(
        default=False,
        help_text='Weekly newsletter with food trends and featured restaurants'
    )
    
    review_emails = models.BooleanField(
        default=True,
        help_text='Emails asking for reviews after orders'
    )
    
    restaurant_updates = models.BooleanField(
        default=True,
        help_text='Updates from restaurants where user has ordered'
    )
    
    # Consent Tracking
    consent_date = models.DateTimeField(
        auto_now_add=True,
        help_text='When user first set their email preferences'
    )
    
    last_updated = models.DateTimeField(
        auto_now=True,
        help_text='When email preferences were last updated'
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address when preferences were last updated'
    )
    
    class Meta:
        verbose_name = 'Email Preference'
        verbose_name_plural = 'Email Preferences'
    
    def __str__(self):
        """
        String representation of email preferences.
        
        Returns:
            str: Username and email preference summary
        """
        return f"{self.user.username} - Email Preferences"
    
    def get_active_preferences(self):
        """
        Get list of active email preferences.
        
        Returns:
            list: List of enabled email types
        """
        active = []
        if self.transactional_emails:
            active.append('Transactional')
        if self.promotional_emails:
            active.append('Promotional')
        if self.newsletter_emails:
            active.append('Newsletter')
        if self.review_emails:
            active.append('Reviews')
        if self.restaurant_updates:
            active.append('Restaurant Updates')
        
        return active
    
    def can_receive_marketing_emails(self):
        """
        Check if user can receive marketing emails.
        
        Returns:
            bool: True if user has opted in to any marketing emails
        """
        return self.promotional_emails or self.newsletter_emails


# Signal to automatically create EmailPreference when User is created
@receiver(post_save, sender=User)
def create_email_preferences(sender, instance, created, **kwargs):
    """
    Automatically create EmailPreference when a new User is created.
    
    This signal ensures that every user gets email preferences automatically
    with default values that prioritize transactional emails.
    
    Args:
        sender: The model class (User)
        instance: The actual instance being saved
        created: Boolean indicating if this is a new creation
    """
    if created:
        EmailPreference.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_email_preferences(sender, instance, **kwargs):
    """
    Automatically save the EmailPreference when the User is saved.
    
    This ensures the preferences stay synchronized with the user.
    
    Args:
        sender: The model class (User)
        instance: The actual instance being saved
    """
    if hasattr(instance, 'email_preferences'):
        instance.email_preferences.save()


class ReviewFlag(models.Model):
    """
    Model for tracking review flags and moderation actions.
    
    Allows users and admins to flag inappropriate reviews.
    """
    
    FLAG_REASONS = [
        ('spam', 'Spam or fake content'),
        ('offensive', 'Offensive language'),
        ('inappropriate', 'Inappropriate content'),
        ('off_topic', 'Off-topic review'),
        ('duplicate', 'Duplicate review'),
        ('other', 'Other reason'),
    ]
    
    # Relationships
    restaurant_review = models.ForeignKey(
        RestaurantReview,
        on_delete=models.CASCADE,
        related_name='flags',
        null=True,
        blank=True,
        help_text='Restaurant review being flagged'
    )
    
    menu_item_review = models.ForeignKey(
        MenuItemReview,
        on_delete=models.CASCADE,
        related_name='flags',
        null=True,
        blank=True,
        help_text='Menu item review being flagged'
    )
    
    flagged_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='review_flags',
        help_text='User who flagged the review'
    )
    
    # Flag Details
    reason = models.CharField(
        max_length=20,
        choices=FLAG_REASONS,
        help_text='Reason for flagging the review'
    )
    
    description = models.TextField(
        blank=True,
        help_text='Additional details about the flag'
    )
    
    # Moderation Status
    is_resolved = models.BooleanField(
        default=False,
        help_text='Whether this flag has been resolved by admin'
    )
    
    admin_notes = models.TextField(
        blank=True,
        help_text='Admin notes about the resolution'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the review was flagged'
    )
    
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the flag was resolved'
    )
    
    class Meta:
        verbose_name = 'Review Flag'
        verbose_name_plural = 'Review Flags'
        ordering = ['-created_at']
        unique_together = [
            ['flagged_by', 'restaurant_review'], 
            ['flagged_by', 'menu_item_review']
        ]
    
    def __str__(self):
        """
        String representation of the review flag.
        
        Returns:
            str: Flag summary with user and reason
        """
        return f"{self.flagged_by.username} flagged for {self.get_reason_display()}"
    
    def get_review(self):
        """
        Get the associated review (restaurant or menu item).
        
        Returns:
            Review: The review being flagged
        """
        return self.restaurant_review or self.menu_item_review


class LoyaltyTransaction(models.Model):
    """
    Tracks all loyalty point movements for comprehensive point management.
    
    This model maintains a complete audit trail of all point transactions:
    - Points earned from orders
    - Points redeemed for discounts
    - Points expired due to time limits
    - Points awarded manually by admin
    - Points deducted for refunds
    
    Each transaction is linked to a user and optionally to an order for traceability.
    """
    
    # Transaction Types
    TRANSACTION_TYPES = [
        ('earned', 'Points Earned'),
        ('redeemed', 'Points Redeemed'),
        ('expired', 'Points Expired'),
        ('manual', 'Manual Adjustment'),
        ('refunded', 'Points Refunded'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='loyalty_transactions',
        help_text='User who owns this transaction'
    )
    
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES,
        help_text='Type of point transaction'
    )
    
    points = models.IntegerField(
        help_text='Points amount (positive for earned, negative for redeemed/expired)'
    )
    
    balance_after = models.IntegerField(
        help_text='User\'s points balance after this transaction'
    )
    
    # Optional Order Reference
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='loyalty_transactions',
        help_text='Order that triggered this transaction (if applicable)'
    )
    
    # Transaction Details
    description = models.TextField(
        blank=True,
        help_text='Description of why points were awarded or deducted'
    )
    
    # Expiration Tracking
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When these points will expire (for earned points)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the transaction occurred'
    )
    
    class Meta:
        verbose_name = 'Loyalty Transaction'
        verbose_name_plural = 'Loyalty Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['balance_after']),  # Index for faster points queries
        ]
    
    def __str__(self):
        """
        String representation of the loyalty transaction.
        
        Returns:
            str: Transaction summary with user and points
        """
        action = 'earned' if self.points > 0 else 'redeemed'
        return f"{self.user.username} {action} {abs(self.points)} points"
    
    def is_expired(self):
        """
        Check if this transaction's points have expired.
        
        Returns:
            bool: True if points are expired, False otherwise
        """
        from django.utils import timezone
        if self.expires_at and self.transaction_type == 'earned':
            return timezone.now() > self.expires_at
        return False
    
    def get_status_display(self):
        """
        Get human-readable status including expiration info.
        
        Returns:
            str: Status with expiration information
        """
        if self.is_expired():
            return "Expired"
        elif self.expires_at and self.transaction_type == 'earned':
            from django.utils import timezone
            days_until_expiry = (self.expires_at - timezone.now()).days
            if days_until_expiry <= 30:
                return f"Expires in {days_until_expiry} days"
            return "Active"
        return self.get_transaction_type_display()
