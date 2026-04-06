"""
Rewards App Signal Handlers.

This module contains signal handlers for the rewards app that listen for
events across the application and automatically award points to users
when they complete certain activities.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.conf import settings

from .models import RewardActivity, RewardPoints

User = get_user_model()


@receiver(post_save, sender=User)
def award_registration_points(sender, instance, created, **kwargs):
    """
    Award points to users when they register for an account.
    
    This signal handler listens for new user creation events and
    awards points automatically when a new user registers.
    
    Args:
        sender: The model class that sent the signal (User)
        instance: The actual instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        # Check if we should award registration points
        registration_points = getattr(settings, 'REWARD_POINTS_REGISTRATION', 100)
        if registration_points > 0:
            RewardPoints.add_points(
                user=instance,
                activity=RewardActivity.REGISTRATION,
                points=registration_points,
                description="Welcome bonus for registering",
                expiry_days=365  # Points expire after a year
            )


# Import these models here to avoid circular imports
from tours.models import Booking
from reviews.models import Review
from destinations.models import Destination, Attraction


@receiver(post_save, sender=Booking)
def award_booking_points(sender, instance, created, **kwargs):
    """
    Award points to users when they book a tour.
    
    This handler awards points based on the booking amount,
    giving more points for more expensive bookings.
    
    Args:
        sender: The model class that sent the signal (Booking)
        instance: The actual booking instance being saved
        created: Boolean indicating if this is a new booking
        **kwargs: Additional keyword arguments
    """
    if created and hasattr(instance, 'user') and instance.user:
        # Award points based on booking value
        base_points = getattr(settings, 'REWARD_POINTS_BOOKING_BASE', 50)
        points_per_currency = getattr(settings, 'REWARD_POINTS_PER_CURRENCY', 0.1)
        
        # Calculate points based on booking value
        if hasattr(instance, 'total_price') and instance.total_price:
            value_points = int(instance.total_price * points_per_currency)
            total_points = base_points + value_points
        else:
            total_points = base_points
            
        RewardPoints.add_points(
            user=instance.user,
            activity=RewardActivity.BOOKING,
            points=total_points,
            description=f"Points for booking: {instance.tour.title if hasattr(instance, 'tour') else 'Tour'}",
            reference_type='Booking',
            reference_id=str(instance.id),
            expiry_days=365
        )


@receiver(post_save, sender=Review)
def award_review_points(sender, instance, created, **kwargs):
    """
    Award points to users when they write a review.
    
    This handler gives users points for contributing reviews,
    which helps build the platform's content.
    
    Args:
        sender: The model class that sent the signal (Review)
        instance: The actual review instance being saved
        created: Boolean indicating if this is a new review
        **kwargs: Additional keyword arguments
    """
    if created and hasattr(instance, 'user') and instance.user:
        # Base points for any review - configurable via settings
        # Default is 25 points for a basic review with just a rating
        # This encourages users to leave at least some feedback
        review_points = getattr(settings, 'REWARD_POINTS_REVIEW', 25)
        
        # Extra points if the review has written content (not just a star rating)
        # This incentivizes more detailed, helpful reviews that provide context
        # and specific feedback about the user's experience
        has_content = bool(getattr(instance, 'content', None))
        content_bonus = getattr(settings, 'REWARD_POINTS_REVIEW_CONTENT_BONUS', 15) if has_content else 0
        
        # Extra points if the review includes photos
        # Visual content significantly enhances review quality and helpfulness
        # Photos provide social proof and help other users make informed decisions
        has_photos = bool(getattr(instance, 'photos', None) and instance.photos.exists())
        photo_bonus = getattr(settings, 'REWARD_POINTS_REVIEW_PHOTO_BONUS', 10) if has_photos else 0
        
        # Calculate total points by adding base points and any applicable bonuses
        # This tiered approach rewards users more for contributing higher quality content
        total_points = review_points + content_bonus + photo_bonus
        
        # Create the reward points entry using the RewardPoints.add_points method
        # This method handles all the logic for creating the entry and applying any tier multipliers
        RewardPoints.add_points(
            # The user who wrote the review and will receive the points
            user=instance.user,
            
            # Categorize this as a REVIEW activity for reporting and filtering
            activity=RewardActivity.REVIEW,
            
            # Award the calculated total points based on review quality
            points=total_points,
            
            # Generate a descriptive message that explains why points were awarded
            # This helps users understand the value of providing detailed reviews
            description="Points for writing a review" + 
                       (" with detailed content" if has_content else "") +
                       (" and photos" if has_photos else ""),
            
            # Link these points to the specific review for reference and auditing
            reference_type='Review',
            reference_id=str(instance.id),
            
            # Set points to expire after 180 days (6 months)
            # This encourages ongoing engagement with the platform
            expiry_days=180
        )


def award_profile_completion_points(user):
    """
    Award points to users when they complete their profile.
    
    This function should be called when a user completes their profile
    with all required information. Complete profiles enhance the user experience
    by enabling personalized recommendations and improving community trust.
    
    Unlike the signal handlers above, this is a standalone function that must be
    explicitly called from a view or form when profile completion is detected.
    This allows for more complex logic to determine what constitutes a "complete" profile.
    
    Args:
        user: The user who completed their profile
    
    Returns:
        RewardPoints: The newly created reward points entry or None if points were not awarded
    """
    # Get the point value from settings with a default of 50 points
    # This is configurable to adjust the incentive without code changes
    profile_points = getattr(settings, 'REWARD_POINTS_PROFILE_COMPLETION', 50)
    
    # Check if the user has already been awarded these points
    # This prevents duplicate awards if the profile is updated multiple times
    # We filter by both user and the specific activity type
    already_awarded = RewardPoints.objects.filter(
        user=user, 
        activity=RewardActivity.PROFILE_COMPLETION
    ).exists()
    
    # Only award points if they haven't been awarded before and the point value is positive
    if not already_awarded and profile_points > 0:
        # Create and return the new reward points entry
        # Points for profile completion typically have a longer expiry
        # since this is a one-time activity
        return RewardPoints.add_points(
            user=user,
            activity=RewardActivity.PROFILE_COMPLETION,
            points=profile_points,
            description="Profile completion bonus",
            expiry_days=365  # Points valid for a full year
        )
    # Return None if points were not awarded (already received or disabled)
    return None


def award_daily_login_points(user):
    """
    Award points to users for logging in daily.
    
    This function should be called when a user logs in, and will
    award points if they haven't already received login points today.
    The daily login bonus encourages regular engagement with the platform
    and helps build user habits and loyalty.
    
    This function should be called from the authentication system,
    typically in a view or middleware that processes successful logins.
    
    Args:
        user: The user who logged in
    
    Returns:
        RewardPoints: The newly created reward points entry or None if no points were awarded
    """
    # Get the configured point value for daily logins with a default of 5 points
    # This is intentionally a smaller amount since it's awarded frequently
    login_points = getattr(settings, 'REWARD_POINTS_DAILY_LOGIN', 5)
    
    # Check if the user has already been awarded points today
    # We use the current date to ensure users can only get this bonus once per day
    # This prevents abuse by logging in and out repeatedly
    today = now().date()
    already_awarded_today = RewardPoints.objects.filter(
        user=user, 
        activity=RewardActivity.DAILY_LOGIN,
        created_at__date=today  # Date comparison to find entries from today
    ).exists()
    
    # Only award points if they haven't already been awarded today and the point value is positive
    if not already_awarded_today and login_points > 0:
        # Create and return the new reward points entry
        # Daily login points have a shorter expiry period since they're awarded frequently
        # and are meant to encourage regular engagement
        return RewardPoints.add_points(
            user=user,
            activity=RewardActivity.DAILY_LOGIN,
            points=login_points,
            description="Daily login bonus",
            expiry_days=90  # Points expire after 3 months
        )
    # Return None if points were not awarded (already received today or disabled)
    return None


def award_referral_points(referrer, referred_user):
    """
    Award points to users for referring new users.
    
    This function should be called when a referred user signs up
    and the referral is confirmed. Referrals are one of the most valuable
    user acquisition channels, so they typically receive a higher point reward.
    
    This function should be called from the registration process when a new user
    signs up using a referral code or link. The referral should be verified
    before calling this function to prevent abuse.
    
    Args:
        referrer: The user who made the referral (existing user)
        referred_user: The new user who was referred (newly registered user)
    
    Returns:
        RewardPoints: The newly created reward points entry or None if points were not awarded
    """
    # Get the configured point value for referrals with a default of 200 points
    # This is typically one of the highest point values in the rewards system
    # because referrals are highly valuable for growing the user base
    referral_points = getattr(settings, 'REWARD_POINTS_REFERRAL', 200)
    
    # Only award points if the referral point value is positive
    # No need to check for duplicates here as each referred_user is unique
    if referral_points > 0:
        # Create and return the new reward points entry
        # The points are awarded to the referrer (not the new user)
        return RewardPoints.add_points(
            user=referrer,  # The existing user who made the referral
            activity=RewardActivity.REFERRAL,  # Categorize as a referral activity
            points=referral_points,
            # Include the referred user's username in the description for clarity
            description=f"Referral bonus for inviting {referred_user.username}",
            # Link these points to the referred user for reference and tracking
            reference_type='User',
            reference_id=str(referred_user.id),
            # Points expire after 6 months
            expiry_days=180
        )
    # Return None if points were not awarded (disabled in settings)
    return None
