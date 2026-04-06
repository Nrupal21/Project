"""
Reward Points System Models.

This module defines all database models related to the reward points system,
including point transactions, redemptions, and reward tiers. It enables users
to earn points for various activities and redeem them for coupons or cash.
"""

import uuid
import datetime
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.crypto import get_random_string
from django.conf import settings

# Import get_user_model to avoid circular imports
from django.contrib.auth import get_user_model


class RewardActivity(models.TextChoices):
    """Defines different types of activities that earn reward points.
    
    This enumeration lists all activities that can earn users reward points,
    making it easy to add new point-earning actions in the future.
    """
    REGISTRATION = 'REGISTRATION', _('Account Registration')
    PROFILE_COMPLETION = 'PROFILE_COMPLETION', _('Complete Profile')
    BOOKING = 'BOOKING', _('Tour Booking')
    REVIEW = 'REVIEW', _('Write a Review')
    REFERRAL = 'REFERRAL', _('Refer a Friend')
    DAILY_LOGIN = 'DAILY_LOGIN', _('Daily Login')
    ATTRACTION_VISIT = 'ATTRACTION_VISIT', _('Visit Attraction')
    GUIDE_INTERACTION = 'GUIDE_INTERACTION', _('Interact with Guide')
    SOCIAL_SHARE = 'SOCIAL_SHARE', _('Social Media Share')
    SPECIAL_EVENT = 'SPECIAL_EVENT', _('Participate in Special Event')
    DESTINATION_APPROVAL = 'DESTINATION_APPROVAL', _('Destination Approval')


class RewardRedemptionType(models.TextChoices):
    """Defines different ways users can redeem their reward points.
    
    This enumeration lists all redemption options available to users,
    allowing for easy extension of redemption methods.
    """
    COUPON = 'COUPON', _('Discount Coupon')
    CASH_TRANSFER = 'CASH_TRANSFER', _('Bank Transfer')
    GIFT_CARD = 'GIFT_CARD', _('Gift Card')
    TRAVEL_CREDIT = 'TRAVEL_CREDIT', _('Travel Credit')
    CHARITY_DONATION = 'CHARITY_DONATION', _('Charity Donation')


class RewardTier(models.Model):
    """Define membership tiers with associated benefits and requirements.
    
    This model represents the different reward tiers available to users,
    such as Bronze, Silver, Gold, etc. Each tier has a minimum point threshold
    and associated benefits that are unlocked when a user reaches that tier.
    
    The tier system provides a gamification element to encourage user engagement
    and loyalty by offering increasing benefits as users accumulate more points.
    """
    TIER_CHOICES = [
        ('BRONZE', _('Bronze')),
        ('SILVER', _('Silver')),
        ('GOLD', _('Gold')),
        ('PLATINUM', _('Platinum')),
    ]
    
    name = models.CharField(max_length=20, choices=TIER_CHOICES, unique=True, 
                          help_text=_('Name of the tier (e.g., BRONZE, SILVER, GOLD)'))
    min_points = models.PositiveIntegerField(
        help_text=_('Minimum points required to reach this tier'))
    point_multiplier = models.FloatField(
        default=1.0, 
        help_text=_('Multiplier applied to point earnings for users in this tier. '
                   'For example, a value of 1.5 means users earn 50% more points for activities.'))
    benefits = models.JSONField(
        default=dict, 
        help_text=_('JSON object containing tier benefits such as discounts, '
                   'free upgrades, priority service, etc.'))
    icon = models.CharField(
        max_length=50, 
        blank=True, 
        help_text=_('Icon identifier for the tier, used in the UI to visually represent the tier'))
    color = models.CharField(
        max_length=20, 
        blank=True, 
        help_text=_('Color code for the tier, used for consistent visual styling across the UI'))
    is_active = models.BooleanField(
        default=True,
        help_text=_('Whether this tier is currently active in the rewards system'))
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('When this tier was created'))
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_('When this tier was last updated'))
    
    def __str__(self):
        """
        Return a string representation of the reward tier.
        
        This method uses Django's get_name_display() to convert the internal
        tier code (e.g., 'BRONZE') to its human-readable form (e.g., 'Bronze').
        This is used throughout the admin interface and in string representations
        of the tier in templates and logs.
        
        The display names are defined in the TIER_CHOICES list and are
        internationalized using Django's translation system for multi-language support.
        
        Returns:
            str: The human-readable display name of the tier (e.g., 'Bronze', 'Silver')
        """
        return self.get_name_display()
    
    class Meta:
        """
        Metadata for the RewardTier model.
        
        This inner class defines various model-level options for the RewardTier model:
        - app_label: Explicitly sets which Django app this model belongs to
        - verbose_name: Human-readable singular name for the model in admin interface
        - verbose_name_plural: Human-readable plural name for the model in admin interface
        - ordering: Default ordering of records when querying this model
        
        The ordering by 'min_points' ensures tiers are naturally sorted from lowest to highest,
        which is important for tier progression display in the UI and for determining a user's
        current tier based on their point balance.
        """
        app_label = 'rewards'
        verbose_name = _('Reward Tier')
        verbose_name_plural = _('Reward Tiers')
        ordering = ['min_points']


class RewardPoints(models.Model):
    """Track reward points earned by users for various activities.
    
    This model records each instance of points being earned or deducted,
    maintaining a detailed history of all point transactions with timestamps
    and descriptions for transparency and auditability.
    """
    # Note: Using default Django id field (SERIAL PRIMARY KEY) to match database schema
    # Reference the custom User model from accounts app
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='reward_points', 
                           db_column='user_id', help_text=_('User who earned or spent these points'))
    activity = models.CharField(max_length=50, choices=RewardActivity.choices, 
                             help_text=_('Type of activity that generated the points'))
    points = models.IntegerField(help_text=_('Points earned (positive) or deducted (negative)'))
    description = models.CharField(max_length=255, help_text=_('Human-readable description of the transaction'))
    reference_id = models.UUIDField(null=True, blank=True,
                                 help_text=_('UUID reference to related entity (booking, review, etc.)'))
    reference_type = models.CharField(max_length=50, null=True, blank=True,
                                   help_text=_('Type of entity referenced by reference_id'))
    expiration_date = models.DateTimeField(null=True, blank=True, 
                                         help_text=_('Date when these points expire, if applicable'))
    is_expired = models.BooleanField(default=False, help_text=_('Whether these points have expired'))
    created_at = models.DateTimeField(auto_now_add=True, help_text=_('When this points transaction was recorded'))
    
    def __str__(self):
        """
        Return a string representation of the reward points entry.
        
        Returns:
            str: User, points amount, and activity description
        """
        return f"{self.user.username}: {self.points} points for {self.get_activity_display()}"
    
    class Meta:
        """Metadata for the RewardPoints model."""
        app_label = 'rewards'
        verbose_name = _('Reward Points Entry')
        verbose_name_plural = _('Reward Points Entries')
        ordering = ['-created_at']
    
    @classmethod
    def get_user_point_balance(cls, user):
        """
        Calculate the current point balance for a user.
        
        This method sums all non-expired points for a user to determine
        their current reward point balance.
        
        Args:
            user: The user whose point balance to calculate
            
        Returns:
            int: Current point balance for the user
        """
        valid_points = cls.objects.filter(user=user, is_expired=False)
        total = valid_points.aggregate(models.Sum('points'))['points__sum'] or 0
        return total
    
    @classmethod
    def add_points(cls, user, activity, points, description=None, reference_type=None, 
                  reference_id=None, expiry_days=None):
        """
        Add points to a user's reward account.
        
        This method creates a new positive points entry for a user
        and applies any tier multipliers if applicable.
        
        Args:
            user: The user to award points to
            activity: The activity that earned the points (from RewardActivity)
            points: Number of points to award (positive integer)
            description: Optional description of the activity
            reference_type: Optional type of object this activity relates to
            reference_id: Optional ID of the related object
            expiry_days: Optional number of days until points expire
            
        Returns:
            RewardPoints: The newly created reward points entry
        """
        if points <= 0:
            raise ValueError("Points must be a positive integer for add_points")
            
        # Apply tier multiplier if applicable
        current_points = cls.get_user_point_balance(user)
        tier = RewardTier.objects.filter(min_points__lte=current_points)\
                              .order_by('-min_points').first()
        
        if tier and tier.multiplier > 1:
            original_points = points
            points = int(points * tier.multiplier)
            if not description:
                description = f"{activity} ({original_points} × {tier.multiplier} tier bonus)"
        
        if not description:
            description = f"{dict(RewardActivity.choices).get(activity, activity)}"
            
        expiration_date = None
        if expiry_days:
            expiration_date = timezone.now() + datetime.timedelta(days=expiry_days)
            
        return cls.objects.create(
            user=user,
            activity=activity,
            points=points,
            description=description,
            reference_object_type=reference_type,
            reference_object_id=reference_id,
            expiration_date=expiration_date
        )
    
    @classmethod
    def deduct_points(cls, user, points, description, reference_type=None, reference_id=None):
        """
        Deduct points from a user's reward account.
        
        This method creates a new negative points entry for a user,
        typically used for point redemptions or adjustments.
        
        Args:
            user: The user to deduct points from
            points: Number of points to deduct (positive integer)
            description: Description of why points are being deducted
            reference_type: Optional type of object this deduction relates to
            reference_id: Optional ID of the related object
            
        Returns:
            RewardPoints: The newly created negative reward points entry
            bool: False if user doesn't have enough points
        """
        if points <= 0:
            raise ValueError("Points must be a positive integer for deduct_points")
            
        current_balance = cls.get_user_point_balance(user)
        if current_balance < points:
            return False
            
        return cls.objects.create(
            user=user,
            activity='REDEMPTION',
            points=-points,  # Store as negative value
            description=description,
            reference_object_type=reference_type,
            reference_object_id=reference_id
        )
    
    @classmethod
    def check_expired_points(cls):
        """
        Mark expired points as such.
        
        This method should be run periodically to update the is_expired flag
        on points that have reached their expiration date.
        
        Returns:
            int: Number of point entries marked as expired
        """
        now = timezone.now()
        expired_points = cls.objects.filter(
            expiration_date__lte=now,
            is_expired=False
        )
        
        count = expired_points.update(is_expired=True)
        return count
        
    @classmethod
    def get_user_tier(cls, user):
        """
        Get the current reward tier for a user based on their points balance.
        
        This method determines which reward tier the user currently qualifies for
        by comparing their point balance with the minimum points required for each tier.
        
        Args:
            user: The user to check the tier for
            
        Returns:
            RewardTier: The user's current reward tier, or None if no tier is found
        """
        points_balance = cls.get_user_point_balance(user)
        try:
            # Get the highest tier where min_points is less than or equal to user's points
            return RewardTier.objects.filter(
                min_points__lte=points_balance,
                is_active=True
            ).order_by('-min_points').first()
        except RewardTier.DoesNotExist:
            return None
    
    @classmethod
    def get_next_tier(cls, user):
        """
        Get the next reward tier a user can achieve.
        
        This method finds the next tier above the user's current tier that they
        can work towards by earning more points.
        
        Args:
            user: The user to check the next tier for
            
        Returns:
            RewardTier: The next reward tier, or None if user is at the highest tier
        """
        current_tier = cls.get_user_tier(user)
        if not current_tier:
            # If user has no tier, return the lowest tier
            return RewardTier.objects.filter(is_active=True).order_by('min_points').first()
            
        try:
            # Get the next tier with higher min_points than current tier
            return RewardTier.objects.filter(
                min_points__gt=current_tier.min_points,
                is_active=True
            ).order_by('min_points').first()
        except RewardTier.DoesNotExist:
            return None  # User is at the highest tier


class RewardRedemption(models.Model):
    """Track redemptions of reward points for coupons, cash, or other benefits.
    
    This model records each instance of points being redeemed for rewards,
    including the redemption status, processing details, and associated
    reward items or cash transfers.
    """
    class Status(models.TextChoices):
        """Define possible statuses for a redemption.
        
        This enumeration defines the various states a redemption can be in,
        from initial request through processing to completion or cancellation.
        """
        PENDING = 'PENDING', _('Pending')
        PROCESSING = 'PROCESSING', _('Processing')
        COMPLETED = 'COMPLETED', _('Completed')
        CANCELLED = 'CANCELLED', _('Cancelled')
        EXPIRED = 'EXPIRED', _('Expired')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False,
                        help_text=_('Unique identifier for this redemption'))
    # Reference the custom User model from accounts app
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, 
                           related_name='reward_redemptions', db_column='user_id',
                           help_text=_('User who redeemed these points'))
    points_used = models.PositiveIntegerField(help_text=_('Number of points redeemed'))
    redemption_type = models.CharField(max_length=50, choices=RewardRedemptionType.choices,
                                    help_text=_('Type of redemption (coupon, cash, etc.)'))
    redemption_value = models.DecimalField(max_digits=10, decimal_places=2, null=True,
                                          help_text=_('Cash value or discount percentage of the redemption'))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING,
                           help_text=_('Current status of this redemption'))
    code = models.CharField(max_length=50, null=True, blank=True, 
                          help_text=_('Coupon or redemption code if applicable'))
    expiry_date = models.DateTimeField(null=True, blank=True, db_column='expiry_date',
                                     help_text=_('When this redemption expires'))
    created_at = models.DateTimeField(auto_now_add=True,
                                    help_text=_('When this redemption was requested'))
    updated_at = models.DateTimeField(auto_now=True,
                                    help_text=_('When this redemption was last updated'))
    
    def __str__(self):
        """
        Return a string representation of the reward redemption.
        
        Returns:
            str: User, points used, and redemption type
        """
        return f"{self.user.username} - {self.points_used} points for {self.get_redemption_type_display()}"
    
    class Meta:
        """Metadata for the RewardRedemption model."""
        app_label = 'rewards'
        verbose_name = _('Reward Redemption')
        verbose_name_plural = _('Reward Redemptions')
        ordering = ['-created_at']
    
    @classmethod
    def create_redemption(cls, user, points, redemption_type, redemption_value, details=None, 
                         expiry_days=None):
        """
        Create a new redemption and deduct points from the user's balance.
        
        This method handles the entire redemption process, including checking
        if the user has sufficient points, creating the redemption record,
        and deducting points from their balance.
        
        Args:
            user: The user redeeming points
            points: Number of points to redeem
            redemption_type: Type of redemption (from RewardRedemptionType)
            redemption_value: Cash or discount value of the redemption
            details: Additional details for the redemption (dictionary)
            expiry_days: Number of days until the redemption expires
            
        Returns:
            tuple: (RewardRedemption object, bool success flag)
        """
        # Check if user has enough points
        current_balance = RewardPoints.get_user_point_balance(user)
        if current_balance < points:
            return None, False
        
        # Generate a random code for coupons
        code = None
        if redemption_type == RewardRedemptionType.COUPON:
            code = get_random_string(length=12, allowed_chars='ABCDEFGHJKLMNPQRSTUVWXYZ23456789')
        
        # Set expiry date if provided
        expires_at = None
        if expiry_days:
            expires_at = timezone.now() + datetime.timedelta(days=expiry_days)
        
        # Create the redemption record
        redemption = cls.objects.create(
            user=user,
            points_used=points,
            redemption_type=redemption_type,
            redemption_value=redemption_value,
            code=code,
            details=details or {},
            expires_at=expires_at
        )
        
        # Deduct the points
        description = f"Redemption: {redemption.get_redemption_type_display()}"
        point_deduction = RewardPoints.deduct_points(
            user=user,
            points=points,
            description=description,
            reference_type='RewardRedemption',
            reference_id=str(redemption.id)
        )
        
        if not point_deduction:
            redemption.delete()
            return None, False
        
        return redemption, True
    
    def mark_as_processed(self, notes=None):
        """
        Mark a redemption as processed/completed.
        
        This method updates the status of a redemption to COMPLETED
        and records when the processing occurred.
        
        Args:
            notes: Optional notes about the processing
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.status = self.Status.COMPLETED
            self.processed_at = timezone.now()
            if notes:
                self.notes = notes
            self.save()
            return True
        except Exception:
            return False
    
    def cancel_redemption(self, notes=None):
        """
        Cancel a redemption and refund points to the user.
        
        This method cancels a redemption that hasn't been processed yet
        and returns the points to the user's balance.
        
        Args:
            notes: Optional notes about the cancellation reason
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.status in [self.Status.COMPLETED, self.Status.CANCELLED]:
            return False
        
        try:
            self.status = self.Status.CANCELLED
            if notes:
                self.notes = notes
            self.save()
            
            # Refund the points
            RewardPoints.add_points(
                user=self.user,
                activity='REFUND',
                points=self.points_used,
                description=f"Refund for cancelled {self.get_redemption_type_display()}",
                reference_type='RewardRedemption',
                reference_id=str(self.id)
            )
            
            return True
        except Exception:
            return False
