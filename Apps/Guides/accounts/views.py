"""
Views for the accounts app.

This module contains view functions and classes for handling user account-related
operations such as profile management, preferences, favorites, user activity,
email verification, and profile API endpoints.
"""

# Django imports for core functionality
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest, Http404, HttpResponseForbidden
from django.views.decorators.http import require_http_methods, require_POST
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.conf import settings

from .forms import (
    UserProfileForm, 
    ProfileForm,
    PreferencesForm
)
# Import models from the current app's models.py
# Using absolute imports to avoid circular dependencies
from .models import (
    UserProfile,         # User profile information
    UserPreference,      # User preferences and settings
    UserFavorite,        # User's favorited items
    VerificationToken,   # Email verification tokens
    GuideApplication     # Guide application records
)
from destinations.models import Destination
from tours.models import Tour

# Python standard library imports
import json
import secrets
import logging

from .models import UserProfile, UserFavorite, UserPreference
from destinations.models import Destination
from tours.models import Tour

# Configure logger for this module
logger = logging.getLogger(__name__)


@login_required
def profile_view(request):
    """
    Display the user's profile information.
    
    Retrieves and displays the logged-in user's profile information including
    personal details, preferences, activity statistics, and guide application status.
    The view also shows any pending, approved, or rejected guide applications
    with detailed status information and appropriate actions.
    
    Args:
        request: The HTTP request object
        
    Returns:
        HttpResponse: Rendered template with user profile data and guide application info
    """
    # Get user profile
    user = request.user
    profile = user.profile
    
    # Get recent activity data
    favorites_count = UserFavorite.objects.filter(user=user).count()
    
    # Get booking and review counts - these would come from your booking and review models
    bookings_count = 0  # placeholder, replace with actual query
    reviews_count = 0   # placeholder, replace with actual query
    
    # Get the user's guide application if it exists
    # This is used to display application status in the profile page
    guide_application = None
    has_pending_application = False
    try:
        guide_application = GuideApplication.objects.filter(user=user).order_by('-application_date').first()
        if guide_application and guide_application.status == 'PENDING':
            has_pending_application = True
    except GuideApplication.DoesNotExist:
        pass
    
    # Initialize reward points variables with defaults
    points_balance = 0
    current_tier = None
    next_tier = None
    points_to_next_tier = 0
    progress_percentage = 0
    
    # Get user's points information from the rewards system if available
    try:
        from rewards.models import RewardPoints, RewardTier
        
        # Get points balance
        points_balance = RewardPoints.get_user_point_balance(user)
        
        # Get current tier if tiers exist
        if RewardTier.objects.exists():
            current_tier = RewardPoints.get_user_tier(user)
            next_tier = RewardPoints.get_next_tier(user)
            
            # Calculate points needed for next tier if there is a next tier
            if next_tier and hasattr(next_tier, 'min_points'):
                points_to_next_tier = max(0, next_tier.min_points - points_balance)
                progress_percentage = min(100, int((points_balance / next_tier.min_points) * 100)) if next_tier.min_points > 0 else 0
            elif current_tier:
                # User is at the highest tier
                progress_percentage = 100
            else:
                # No tiers configured or user has no tier yet
                progress_percentage = 0
    except ImportError:
        # If rewards app is not available, use default values
        pass
    except Exception as e:
        # Log the error but don't break the profile page
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error loading rewards data: {str(e)}", exc_info=True)
    
    # Create context with all necessary data for the template
    context = {
        'user': user,
        'profile': profile,
        'favorites_count': favorites_count,
        'guide_application': guide_application,  # Add guide application to context
        'has_pending_application': has_pending_application,  # Add pending application status
        'points_balance': points_balance,
        'current_tier': current_tier,
        'next_tier': next_tier,
        'points_to_next_tier': points_to_next_tier,
        'progress_percentage': progress_percentage,
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile_view(request):
    """
    Allow user to edit their profile information.
    
    Displays a form for users to update their profile information and
    processes the form submission to save changes. Uses the ProfileForm
    for validation and processing of profile data.
    
    Args:
        request: The HTTP request object
        
    Returns:
        HttpResponse: Rendered form template or redirect after save
    """
    user = request.user
    profile = user.profile
    
    if request.method == 'POST':
        # Create form instances with submitted data and files
        user_form = UserProfileForm(request.POST, instance=user)
        profile_form = ProfileForm(
            request.POST, 
            request.FILES, 
            instance=profile
        )
        
        if user_form.is_valid() and profile_form.is_valid():
            # Save the user and profile data
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user  # Ensure user is set on profile
            profile.save()
            
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('accounts:profile')
    else:
        # Initialize forms with current user and profile data
        user_form = UserProfileForm(instance=user)
        profile_form = ProfileForm(instance=profile)
    
    context = {
        'user': user,
        'user_form': user_form,
        'profile_form': profile_form
    }
    
    return render(request, 'accounts/edit_profile.html', context)


@login_required
def preferences_view(request):
    """
    Allow user to set and update their preferences.
    
    Displays a form for users to update their travel preferences and
    processes the form submission to save changes. Uses the PreferencesForm
    for validation and processing of preferences data.
    
    Args:
        request: The HTTP request object
        
    Returns:
        HttpResponse: Rendered form template or redirect after save
    """
    user = request.user
    
    # Get or create user preferences
    preferences, created = UserPreference.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        # Create form instance with submitted data
        preferences_form = PreferencesForm(
            request.POST, 
            instance=preferences
        )
        
        if preferences_form.is_valid():
            # Save the preferences data
            preferences = preferences_form.save(commit=False)
            preferences.user = user  # Ensure user is set on preferences
            
            # Handle newsletter and notification preferences from the form
            user.profile.newsletter_subscription = preferences_form.cleaned_data.get('newsletter_subscription', False)
            user.profile.email_notifications = preferences_form.cleaned_data.get('email_notifications', False)
            
            # Save both preferences and profile
            preferences.save()
            user.profile.save()
            
            messages.success(request, "Your preferences have been updated successfully.")
            return redirect('accounts:preferences')
    else:
        # Initialize form with current preferences data
        preferences_form = PreferencesForm(instance=preferences)
    
    context = {
        'user': user,
        'preferences_form': preferences_form,
        'profile': user.profile
    }
    
    return render(request, 'accounts/preferences.html', context)


@login_required
def favorites_view(request):
    """
    Display all items favorited by the user.
    
    Retrieves and displays all destinations, tours, and other items
    that the user has marked as favorites.
    
    Args:
        request: The HTTP request object
        
    Returns:
        HttpResponse: Rendered template with user's favorites
    """
    user = request.user
    
    # Get all favorites
    favorites = UserFavorite.objects.filter(user=user).order_by('-created_at')
    
    # Group favorites by content type
    destination_favorites = []
    tour_favorites = []
    
    for favorite in favorites:
        if favorite.content_type == 'destination':
            try:
                destination = Destination.objects.get(id=favorite.object_id)
                destination_favorites.append({
                    'favorite': favorite,
                    'object': destination
                })
            except Destination.DoesNotExist:
                pass
                
        elif favorite.content_type == 'tour':
            try:
                tour = Tour.objects.get(id=favorite.object_id)
                tour_favorites.append({
                    'favorite': favorite,
                    'object': tour
                })
            except Tour.DoesNotExist:
                pass
    
    context = {
        'destination_favorites': destination_favorites,
        'tour_favorites': tour_favorites
    }
    
    return render(request, 'accounts/favorites.html', context)


@login_required
@require_http_methods(["POST"])
def add_favorite_view(request):
    """
    Add an item to user's favorites.
    
    Processes a request to add a destination, tour, or other item
    to the user's list of favorites.
    
    Args:
        request: The HTTP request object
        
    Returns:
        JsonResponse: Success status and message
    """
    user = request.user
    content_type = request.POST.get('content_type')
    object_id = request.POST.get('object_id')
    
    # Validate input
    if not content_type or not object_id:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request parameters'
        }, status=400)
    
    # Check if already favorited
    existing = UserFavorite.objects.filter(
        user=user,
        content_type=content_type,
        object_id=object_id
    ).exists()
    
    if existing:
        return JsonResponse({
            'success': False,
            'message': 'Item is already in your favorites'
        })
    
    # Create new favorite
    UserFavorite.objects.create(
        user=user,
        content_type=content_type,
        object_id=object_id
    )
    
    return JsonResponse({
        'success': True,
        'message': 'Added to favorites successfully'
    })


@login_required
def remove_favorite_view(request, favorite_id):
    """
    Remove an item from user's favorites.
    
    Deletes a specific favorite item from the user's list of favorites.
    
    Args:
        request: The HTTP request object
        favorite_id: ID of the favorite to remove
        
    Returns:
        JsonResponse or HttpResponse: Response after deletion
    """
    user = request.user
    
    # Get the favorite or return 404
    favorite = get_object_or_404(UserFavorite, id=favorite_id, user=user)
    
    # Delete the favorite
    favorite.delete()
    
    # If AJAX request, return JSON response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Removed from favorites successfully'
        })
    
    # Otherwise redirect back to favorites page
    messages.success(request, "Item removed from favorites successfully.")
    return redirect('accounts:favorites')


@login_required
def activity_view(request):
    """
    Display the user's recent activity.
    
    Shows a timeline of the user's recent activity including bookings,
    reviews, favorites, and other interactions with the site.
    
    Args:
        request: The HTTP request object
        
    Returns:
        HttpResponse: Rendered template with user activity data
    """
    user = request.user
    
    # Placeholder for activity data
    # In a real app, you would query various models for user activity
    activities = []
    
    context = {
        'activities': activities
    }
    
    return render(request, 'accounts/activity.html', context)


@login_required
def user_bookings_view(request):
    """
    Display the user's bookings.
    
    Retrieves and displays all tour bookings made by the user,
    organized by upcoming, past, and cancelled bookings.
    
    Args:
        request: The HTTP request object
        
    Returns:
        HttpResponse: Rendered template with user bookings
    """
    user = request.user
    
    # Placeholder for booking data
    # In a real app, you would query the Booking model for user bookings
    upcoming_bookings = []
    past_bookings = []
    cancelled_bookings = []
    
    context = {
        'upcoming_bookings': upcoming_bookings,
        'past_bookings': past_bookings,
        'cancelled_bookings': cancelled_bookings
    }
    
    return render(request, 'accounts/bookings.html', context)


@login_required
def user_reviews_view(request):
    """
    Display the user's reviews.
    
    Retrieves and displays all reviews submitted by the user
    for destinations, tours, and other reviewable items.
    
    Args:
        request: The HTTP request object
        
    Returns:
        HttpResponse: Rendered template with user reviews
    """
    user = request.user
    
    # Placeholder for review data
    # In a real app, you would query review models for user reviews
    reviews = []
    
    context = {
        'reviews': reviews
    }
    
    return render(request, 'accounts/reviews.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def preferences_api(request):
    """
    API endpoint to get or update user preferences.
    
    Handles GET requests to retrieve current preferences and
    POST requests to update preferences via API.
    
    Args:
        request: The HTTP request object
        
    Returns:
        JsonResponse: User preferences data or update status
    """
    user = request.user
    preferences, created = UserPreference.objects.get_or_create(user=user)
    
    if request.method == 'GET':
        # Return current preferences
        return JsonResponse({
            'travel_interests': preferences.travel_interests or [],
            'budget_preference': preferences.budget_preference,
            'newsletter_subscription': user.profile.newsletter_subscription,
            'email_notifications': user.profile.email_notifications
        })
    
    elif request.method == 'POST':
        # Update preferences from JSON data
        import json
        
        try:
            data = json.loads(request.body)
            
            # Update preferences
            if 'travel_interests' in data:
                preferences.travel_interests = data['travel_interests']
            
            if 'budget_preference' in data:
                preferences.budget_preference = data['budget_preference']
            
            # Update profile settings
            if 'newsletter_subscription' in data:
                user.profile.newsletter_subscription = data['newsletter_subscription']
            
            if 'email_notifications' in data:
                user.profile.email_notifications = data['email_notifications']
            
            # Save changes
            preferences.save()
            user.profile.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Preferences updated successfully'
            })
        
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            }, status=400)


@login_required
@require_http_methods(["GET"])
def favorites_api(request):
    """
    API endpoint to get user favorites.
    
    Returns a list of the user's favorite items with detailed information.
    
    Args:
        request: The HTTP request object
        
    Returns:
        JsonResponse: User favorites data
    """
    user = request.user
    
    # Get content type filter from query params
    content_type = request.GET.get('type')
    
    # Base query
    favorites = UserFavorite.objects.filter(user=user)
    
    # Filter by content type if specified
    if content_type:
        favorites = favorites.filter(content_type=content_type)
    
    # Order by most recent
    favorites = favorites.order_by('-created_at')
    
    # Format response data
    result = []
    
    for favorite in favorites:
        item = {
            'id': favorite.id,
            'content_type': favorite.content_type,
            'object_id': favorite.object_id,
            'created_at': favorite.created_at.isoformat()
        }
        
        # Add object details if available
        if favorite.content_type == 'destination':
            try:
                dest = Destination.objects.get(id=favorite.object_id)
                item['name'] = dest.name
                item['url'] = f"/destinations/{dest.slug}/"
                
                # Get primary image if available
                primary_image = dest.images.filter(is_primary=True).first()
                if primary_image:
                    item['image_url'] = primary_image.image.url
                
            except Destination.DoesNotExist:
                pass
                
        elif favorite.content_type == 'tour':
            try:
                tour = Tour.objects.get(id=favorite.object_id)
                item['name'] = tour.name
                item['url'] = f"/tours/{tour.slug}/"
                
                # Get primary image if available
                primary_image = tour.images.filter(is_primary=True).first()
                if primary_image:
                    item['image_url'] = primary_image.image.url
                
            except Tour.DoesNotExist:
                pass
        
        result.append(item)
    
    return JsonResponse({
        'success': True,
        'count': len(result),
        'favorites': result
    })


@login_required
def resend_verification_email(request):
    """
    Resend email verification link to the user's email.
    
    This view handles requests to resend the verification email when a user
    hasn't received the original email or the original link has expired.
    It creates a new verification token and sends a fresh email.
    
    Args:
        request: The HTTP request object containing user data
        
    Returns:
        JsonResponse: JSON with success status and message
        
    Notes:
        - Only accessible to logged-in users
        - Uses POST method to prevent CSRF attacks
        - Rate-limited to prevent abuse
    """
    # Only allow POST requests to prevent CSRF attacks
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Only POST requests are allowed'
        }, status=405)
    
    # Get the current user - we know they're authenticated due to @login_required
    user = request.user
    
    # Check if user's email is already verified
    user_profile = UserProfile.objects.get(user=user)
    if user_profile.email_verified:
        return JsonResponse({
            'success': False,
            'message': 'Your email is already verified'
        })
    
    # Check for rate limiting - prevent abuse by limiting frequency of resends
    # This uses a Django cache to track resend attempts
    cache_key = f"email_verification_resend_{user.id}"
    resend_timestamp = cache.get(cache_key)
    
    if resend_timestamp and (timezone.now() - resend_timestamp).total_seconds() < 300:  # 5 minutes
        return JsonResponse({
            'success': False,
            'message': 'Please wait 5 minutes before requesting another verification email'
        })
    
    # Generate a new verification token
    # In a real implementation, you'd use a secure token generation method
    verification_token = secrets.token_urlsafe(32)
    
    # Store the token with the user profile or in a separate verification model
    # with an expiration time, for example:
    user_profile.verification_token = verification_token
    user_profile.token_created_at = timezone.now()
    user_profile.save()
    
    # Construct verification URL
    verification_url = request.build_absolute_uri(
        reverse('accounts:verify_email', args=[verification_token])
    )
    
    # Send verification email
    # This is a placeholder - in a real app, you'd configure email settings
    # and use a template for the email body
    try:
        send_mail(
            subject='Verify your TravelGuide account email',
            message=f'Please click the link to verify your email: {verification_url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        # Update cache to implement rate limiting
        cache.set(cache_key, timezone.now(), 300)  # Cache for 5 minutes
        
        return JsonResponse({
            'success': True,
            'message': 'Verification email has been sent to your registered email address'
        })
        
    except Exception as e:
        # Log the error for server-side debugging
        logger.error(f"Failed to send verification email: {str(e)}")
        
        return JsonResponse({
            'success': False,
            'message': 'Failed to send verification email. Please try again later.'
        }, status=500)


@login_required
def profile_api(request):
    """
    API endpoint for retrieving and updating user profile data.
    
    This view handles both GET requests to retrieve profile data and
    PUT/PATCH requests to update profile information via AJAX calls.
    
    Args:
        request: The HTTP request object containing user data and possibly
                profile updates
                
    Returns:
        JsonResponse: User profile data or update confirmation
        
    Notes:
        - Only accessible to logged-in users
        - GET: Returns profile data as JSON
        - PUT/PATCH: Updates profile with provided data
        - POST: Not allowed (use PUT/PATCH for updates)
    """
    # Get the current user's profile
    try:
        profile = UserProfile.objects.select_related('user').get(user=request.user)
    except UserProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Profile not found'
        }, status=404)
    
    if request.method == 'GET':
        # Return the user's profile data as JSON
        data = {
            'success': True,
            'profile': {
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'date_joined': request.user.date_joined.isoformat(),
                'profile_picture': profile.profile_picture.url if profile.profile_picture else None,
                'bio': profile.bio,
                'phone': profile.phone,
                'address': profile.address,
                'city': profile.city,
                'country': profile.country,
                'email_verified': profile.email_verified,
                'account_verified': profile.account_verified,
                'travel_experience_level': profile.travel_experience_level,
                'interests': list(profile.interests.all().values('name', 'id')) if hasattr(profile, 'interests') else [],
                'notification_preferences': {
                    'email_notifications': profile.email_notifications,
                    'push_notifications': profile.push_notifications,
                    'marketing_emails': profile.marketing_emails
                }
            }
        }
        return JsonResponse(data)
        
    elif request.method in ['PUT', 'PATCH']:
        # Update the profile with data from the request
        try:
            # Parse the JSON data from the request body
            data = json.loads(request.body)
            
            # Update User model fields
            user_fields = ['first_name', 'last_name']
            user_updates = {}
            
            for field in user_fields:
                if field in data:
                    user_updates[field] = data[field]
            
            # If any User model fields are being updated
            if user_updates:
                # Update User fields
                User.objects.filter(id=request.user.id).update(**user_updates)
            
            # Update UserProfile fields (excluding relationships and file fields)
            profile_fields = ['bio', 'phone', 'address', 'city', 'country',
                             'travel_experience_level']
            profile_updates = {}
            
            for field in profile_fields:
                if field in data:
                    profile_updates[field] = data[field]
            
            # Update notification preferences if provided
            if 'notification_preferences' in data:
                notifications = data['notification_preferences']
                if 'email_notifications' in notifications:
                    profile_updates['email_notifications'] = notifications['email_notifications']
                if 'push_notifications' in notifications:
                    profile_updates['push_notifications'] = notifications['push_notifications']
                if 'marketing_emails' in notifications:
                    profile_updates['marketing_emails'] = notifications['marketing_emails']
            
            # If any profile fields are being updated
            if profile_updates:
                # Update Profile fields
                UserProfile.objects.filter(user=request.user).update(**profile_updates)
                
            # Refresh profile from database
            profile.refresh_from_db()
            
            return JsonResponse({
                'success': True,
                'message': 'Profile updated successfully'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data in request'
            }, status=400)
            
        except Exception as e:
            # Log the error for debugging
            logger.error(f"Error updating profile via API: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error updating profile: {str(e)}'
            }, status=500)
            
    else:  # Unsupported HTTP method
        return JsonResponse({
            'success': False,
            'message': f'Method {request.method} not allowed'
        }, status=405)


def user_profile_view(request, user_id):
    """
    Display a user's profile by their ID.
    
    This view allows administrators and staff to view another user's profile
    information. It includes basic user details, profile information, and
    activity statistics. Access control ensures only authorized users can
    view other profiles.
    
    Args:
        request: The HTTP request object
        user_id: The ID of the user whose profile is being viewed
        
    Returns:
        HttpResponse: Rendered template with user profile data
        HttpResponseForbidden: If the requesting user doesn't have permission
    """
    # Get the target user or return 404
    from django.contrib.auth import get_user_model
    User = get_user_model()
    target_user = get_object_or_404(User, id=user_id)
    
    # Security check: Only allow staff, admins, or the user themselves to view profiles
    if not (request.user.is_staff or request.user.is_superuser or request.user.id == user_id):
        return HttpResponseForbidden("You don't have permission to view this profile.")
    
    # Get user profile
    try:
        profile = target_user.profile
    except UserProfile.DoesNotExist:
        # Create profile if it doesn't exist
        profile = UserProfile.objects.create(user=target_user)
    
    # Get recent activity data
    favorites_count = UserFavorite.objects.filter(user=target_user).count()
    
    # Get guide application if it exists
    guide_application = None
    has_pending_application = False
    try:
        guide_application = GuideApplication.objects.filter(user=target_user).order_by('-application_date').first()
        if guide_application and guide_application.status == 'PENDING':
            has_pending_application = True
    except GuideApplication.DoesNotExist:
        pass
    
    # Initialize reward points variables with defaults
    points_balance = 0
    current_tier = None
    next_tier = None
    points_to_next_tier = 0
    progress_percentage = 0
    
    # Get user's points information from the rewards system if available
    try:
        from rewards.models import RewardPoints, RewardTier
        
        # Get points balance
        points_balance = RewardPoints.get_user_point_balance(target_user)
        
        # Get current tier if tiers exist
        if RewardTier.objects.exists():
            current_tier = RewardPoints.get_user_tier(target_user)
            next_tier = RewardPoints.get_next_tier(target_user)
            
            # Calculate points needed for next tier if there is a next tier
            if next_tier and hasattr(next_tier, 'min_points'):
                points_to_next_tier = max(0, next_tier.min_points - points_balance)
                progress_percentage = min(100, int((points_balance / next_tier.min_points) * 100)) if next_tier.min_points > 0 else 0
            elif current_tier:
                # User is at the highest tier
                progress_percentage = 100
            else:
                # No tiers configured or user has no tier yet
                progress_percentage = 0
    except ImportError:
        # If rewards app is not available, use default values
        pass
    except Exception as e:
        # Log the error but don't break the profile page
        logger.error(f"Error loading rewards data: {str(e)}", exc_info=True)
    
    # Create context with all necessary data for the template
    context = {
        'user': target_user,
        'profile': profile,
        'favorites_count': favorites_count,
        'guide_application': guide_application,
        'has_pending_application': has_pending_application,
        'points_balance': points_balance,
        'current_tier': current_tier,
        'next_tier': next_tier,
        'points_to_next_tier': points_to_next_tier,
        'progress_percentage': progress_percentage,
        'is_profile_owner': request.user.id == user_id,
    }
    
    return render(request, 'accounts/user_profile.html', context)
