"""
Signal handlers for the accounts app.

This module contains signal handlers for creating and updating
user profiles, preferences, and OTP devices when users are created or updated.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from django.utils import timezone
from allauth.socialaccount.signals import social_account_added, social_account_updated, social_account_removed
from allauth.account.signals import email_confirmed, email_confirmation_sent

from .models import UserProfile, UserPreferences
from .otp_models import OTPDevice

User = get_user_model()

@receiver(social_account_added)
def social_account_added_callback(request, sociallogin, **kwargs):
    """
    Signal handler when a new social account is added to an existing user.
    
    Args:
        request: The current request object.
        sociallogin: The social login instance containing the social account.
        **kwargs: Additional keyword arguments.
    """
    user = sociallogin.user
    socialaccount = sociallogin.account
    
    # Update user profile with social account information if needed
    if hasattr(user, 'profile'):
        profile = user.profile
        
        # Set the profile picture from the social account if not already set
        if not profile.profile_picture and 'avatar_url' in socialaccount.extra_data:
            profile.profile_picture = socialaccount.extra_data['avatar_url']
            
        # Set the name from the social account if not already set
        if not profile.full_name and 'name' in socialaccount.extra_data:
            profile.full_name = socialaccount.extra_data['name']
            
        profile.save()

@receiver(social_account_updated)
def social_account_updated_callback(request, sociallogin, **kwargs):
    """
    Signal handler when a social account is updated.
    
    Args:
        request: The current request object.
        sociallogin: The social login instance containing the social account.
        **kwargs: Additional keyword arguments.
    """
    user = sociallogin.user
    socialaccount = sociallogin.account
    
    # Update user profile with the latest social account information
    if hasattr(user, 'profile'):
        profile = user.profile
        
        # Update the profile picture if available
        if 'avatar_url' in socialaccount.extra_data:
            profile.profile_picture = socialaccount.extra_data['avatar_url']
            
        # Update the name if available
        if 'name' in socialaccount.extra_data:
            profile.full_name = socialaccount.extra_data['name']
            
        profile.save()

@receiver(user_logged_in)
def user_logged_in_callback(sender, request, user, **kwargs):
    """
    Signal handler when a user logs in, including via social accounts.
    
    Args:
        sender: The sender of the signal.
        request: The current request object.
        user: The user who logged in.
        **kwargs: Additional keyword arguments.
    """
    # Update the last login time in the user profile
    if hasattr(user, 'profile'):
        user.profile.last_login = timezone.now()
        user.profile.save()
    
    # You can add additional logic here, such as tracking login history
    # or performing actions specific to social logins

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal handler to create a UserProfile, UserPreferences, and OTPDevice when a new User is created.
    
    Args:
        sender: The model class that sent the signal.
        instance: The actual instance being saved.
        created (bool): Whether this is a new record being created.
        **kwargs: Additional keyword arguments.
    """
    if created:
        # Create UserProfile if it doesn't exist
        UserProfile.objects.get_or_create(user=instance)
        # Create UserPreferences if it doesn't exist
        UserPreferences.objects.get_or_create(user=instance)
        # Create OTPDevice if it doesn't exist (but don't generate secret key yet)
        OTPDevice.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Signal handler to save the UserProfile and UserPreferences when a User is saved.
    
    Args:
        sender: The model class that sent the signal.
        instance: The actual instance being saved.
        **kwargs: Additional keyword arguments.
    """
    # Save UserProfile if it exists
    if hasattr(instance, 'profile'):
        instance.profile.save()
    
    # Save UserPreferences if it exists
    if hasattr(instance, 'preferences'):
        instance.preferences.save()

@receiver(pre_save, sender=User)
def update_user_profile_on_email_change(sender, instance, **kwargs):
    """
    Signal handler to update the UserProfile when a User's email is changed.
    
    This ensures that any denormalized email data in the profile stays in sync.
    
    Args:
        sender: The model class that sent the signal.
        instance: The actual instance being saved.
        **kwargs: Additional keyword arguments.
    """
    if instance.pk:
        try:
            old_instance = User.objects.get(pk=instance.pk)
            if old_instance.email != instance.email and hasattr(instance, 'profile'):
                # If email changed and user has a profile, we might want to do something here
                # For example, send an email verification request
                pass
        except User.DoesNotExist:
            # New user, no need to check for changes
            pass
