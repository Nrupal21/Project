"""
Profile Management Views Module.

This module contains views for handling user profile management in the TravelGuide application.
It provides functionality for viewing and updating user profile information, preferences,
notifications settings, and other account-related data.

All views in this module require user authentication and include appropriate
form validation, error handling, and success messages.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import update_session_auth_hash
from django.utils.translation import gettext_lazy as _

from .forms import (
    UserProfileForm, 
    ProfileForm, 
    CustomPasswordChangeForm,
    PreferencesForm
)
from .models import UserProfile, UserPreference

import logging
logger = logging.getLogger(__name__)

@login_required
def profile_view(request):
    """
    Display the user's profile information and settings.
    
    This view loads the user's profile data and renders the settings template with 
    multiple tabs including profile information, password change, travel preferences,
    and notification settings. All forms are pre-populated with the user's current data.
    
    Args:
        request: HttpRequest object containing metadata about the request
        
    Returns:
        HttpResponse: Rendered settings template with user profile data and forms
    """
    # Initialize forms with user's current data
    user_form = UserProfileForm(instance=request.user)
    
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    profile_form = ProfileForm(instance=profile)
    
    # Get or create user preferences
    preferences, created = UserPreference.objects.get_or_create(user=request.user)
    preferences_form = PreferencesForm(instance=preferences)
    
    # Initialize password change form
    password_form = CustomPasswordChangeForm(request.user)
    
    # Create context with all necessary forms and data
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'password_form': password_form,
        'preferences_form': preferences_form,  # Add preferences form to context
        'user_profile': profile,
        'user_preferences': preferences,  # Add preferences model to context
    }
    
    return render(request, 'accounts/settings.html', context)

@login_required
@require_http_methods(["POST"])
def update_profile(request):
    """
    Update the user's basic profile information.
    
    This view handles the form submission for updating a user's basic profile 
    information including name, email, location, bio, and profile picture. 
    Form validation ensures data integrity and appropriate feedback is provided.
    
    Args:
        request: HttpRequest object containing form data in POST
        
    Returns:
        HttpResponse: Redirects to profile view with success/error message
    """
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Process both user and profile forms
    user_form = UserProfileForm(request.POST, instance=request.user)
    profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
    
    # Validate both forms
    if user_form.is_valid() and profile_form.is_valid():
        try:
            # Save user form data
            user_form.save()
            
            # Save profile form data
            profile = profile_form.save(commit=False)
            profile.user = request.user
            profile.save()
            
            # Add success message
            messages.success(request, _('Your profile has been updated successfully!'))
            logger.info(f"Profile updated for user: {request.user.username}")
            
            # Redirect back to profile
            return redirect('accounts:profile')
        except Exception as e:
            # Log error and show message
            logger.error(f"Error updating profile: {str(e)}")
            messages.error(request, _('An error occurred while updating your profile.'))
    else:
        # Form validation errors
        for field, errors in user_form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
                
        for field, errors in profile_form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    
    # Re-render form with errors
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'password_form': CustomPasswordChangeForm(request.user),
        'user_profile': profile,
    }
    
    return render(request, 'accounts/settings.html', context)

@login_required
@require_http_methods(["POST"])
def update_password(request):
    """
    Update the user's password.
    
    This view handles the form submission for changing the user's password.
    It validates the current password, ensures new password meets requirements,
    and updates the session to maintain login state after password change.
    
    Args:
        request: HttpRequest object containing password form data in POST
        
    Returns:
        HttpResponse: Redirects to profile view with success/error message
    """
    password_form = CustomPasswordChangeForm(request.user, request.POST)
    
    if password_form.is_valid():
        try:
            # Save new password
            user = password_form.save()
            
            # Update session to prevent logging out
            update_session_auth_hash(request, user)
            
            # Add success message
            messages.success(request, _('Your password was successfully updated!'))
            logger.info(f"Password changed for user: {request.user.username}")
            
            return redirect('accounts:profile')
        except Exception as e:
            # Log error and show message
            logger.error(f"Error changing password: {str(e)}")
            messages.error(request, _('An error occurred while changing your password.'))
    else:
        # Form validation errors
        for field, errors in password_form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    
    # Re-render form with errors
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    context = {
        'user_form': UserProfileForm(instance=request.user),
        'profile_form': ProfileForm(instance=profile),
        'password_form': password_form,
        'user_profile': profile,
        'active_tab': 'password',  # Indicate active tab
    }
    
    return render(request, 'accounts/settings.html', context)

@login_required
@require_http_methods(["POST"])
def update_preferences(request):
    """
    Update the user's travel preferences.
    
    This view processes form submissions for updating a user's travel preferences
    such as preferred destinations, travel styles, and accommodation preferences.
    These settings help personalize the user experience and recommendations.
    
    Args:
        request: HttpRequest object containing preferences form data in POST
        
    Returns:
        HttpResponse: Redirects to profile view with success/error message
    """
    # Get or create user preference
    preference, created = UserPreference.objects.get_or_create(user=request.user)
    
    # Create form with POST data
    form = PreferencesForm(request.POST, instance=preference)
    
    # Validate preference fields
    if form.is_valid():
        try:
            # Save preference fields
            form.save()
            
            # Add success message
            messages.success(request, _('Your travel preferences have been updated!'))
            logger.info(f"Travel preferences updated for user: {request.user.username}")
            
            return redirect('accounts:profile')
        except Exception as e:
            # Log error and show message
            logger.error(f"Error updating travel preferences: {str(e)}")
            messages.error(request, _('An error occurred while updating your preferences.'))
    else:
        # Form validation errors
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    
    # Get or create user profile for context
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    # Re-render form with errors
    context = {
        'user_form': UserProfileForm(instance=request.user),
        'profile_form': ProfileForm(instance=profile),
        'password_form': CustomPasswordChangeForm(request.user),
        'preferences_form': form,  # Add the preferences form to context
        'user_profile': profile,
        'active_tab': 'preferences',  # Indicate active tab
    }
    
    return render(request, 'accounts/settings.html', context)

@login_required
@require_http_methods(["POST"])
def update_notifications(request):
    """
    Update the user's notification preferences.
    
    This view handles form submissions for updating notification settings,
    including email updates and marketing communication preferences.
    These settings control what types of communications the user receives.
    
    Args:
        request: HttpRequest object containing notification settings in POST
        
    Returns:
        HttpResponse: Redirects to profile view with success/error message
    """
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Create form with POST data
    form = ProfileForm(request.POST, instance=profile)
    
    # Only validate notification fields
    if form.is_valid():
        try:
            # Save only notification fields
            profile = form.save(commit=False)
            
            # Update notification settings
            profile.email_updates = form.cleaned_data.get('email_updates', profile.email_updates)
            profile.email_marketing = form.cleaned_data.get('email_marketing', profile.email_marketing)
            profile.save()
            
            # Add success message
            messages.success(request, _('Your notification settings have been updated!'))
            logger.info(f"Notification settings updated for user: {request.user.username}")
            
            return redirect('accounts:profile')
        except Exception as e:
            # Log error and show message
            logger.error(f"Error updating notification settings: {str(e)}")
            messages.error(request, _('An error occurred while updating your notification settings.'))
    else:
        # Form validation errors
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    
    # Re-render form with errors
    context = {
        'user_form': UserProfileForm(instance=request.user),
        'profile_form': form,
        'password_form': CustomPasswordChangeForm(request.user),
        'user_profile': profile,
        'active_tab': 'notifications',  # Indicate active tab
    }
    
    return render(request, 'accounts/settings.html', context)
