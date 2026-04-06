"""
AI Itinerary Generation Views.

This module contains views for generating travel itineraries using AI providers
like OpenAI and Google Gemini.
"""

import os
import json
import logging
from datetime import timedelta, datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext as _

from destinations.models import Destination, Attraction
from .models import Itinerary, ItineraryDay, Activity
from .forms import ActivityForm
from .ai_service import AIServiceFactory, get_default_ai_service

# Set up logging
logger = logging.getLogger(__name__)

@login_required
def select_ai_provider(request, auto_select=False):
    """
    Handle AI provider selection with intelligent auto-selection capability.
    
    This view can either:
    1. Auto-select the best available AI provider based on configuration, performance metrics,
       and user preferences
    2. Show a selection page if multiple providers are available and auto_select is False
    
    Args:
        request: The HTTP request object
        auto_select: If True, automatically selects the best available provider
                    If False, shows the provider selection page when multiple providers are available
        
    Returns:
        HttpResponse: Redirect to the selected provider's form or render selection page
    """
    # Check which AI providers are configured using multiple methods
    # This ensures we detect API keys even if they're not in os.environ
    
    # Check OpenAI API key
    openai_env_key = os.environ.get('OPENAI_API_KEY')
    openai_getenv_key = os.getenv('OPENAI_API_KEY')
    openai_hardcoded_key = "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"
    openai_configured = bool(openai_env_key or openai_getenv_key or openai_hardcoded_key)
    
    # Check Gemini API key
    gemini_env_key = os.environ.get('GEMINI_API_KEY')
    gemini_getenv_key = os.getenv('GEMINI_API_KEY')
    gemini_hardcoded_key = "AIzaSyDJ177kr7nMG-74rB4cbAZmbpFEuk_XoRo"
    gemini_configured = bool(gemini_env_key or gemini_getenv_key or gemini_hardcoded_key)
    
    # Log API key configuration status
    logger.info(f"OpenAI API key configured: {openai_configured}")
    logger.info(f"Gemini API key configured: {gemini_configured}")
    
    # If no providers are configured, show error
    if not openai_configured and not gemini_configured:
        messages.error(request, _("No AI providers are currently available. Please try again later or contact support."))
        return redirect('itineraries:itinerary_list')
    
    # If only one provider is configured, use it
    if openai_configured and not gemini_configured:
        return redirect('itineraries:ai_itinerary_form', provider='openai')
    elif not openai_configured and gemini_configured:
        return redirect('itineraries:ai_itinerary_form', provider='gemini')
    
    # If we get here, both providers are configured
    if auto_select:
        # Get user's preferred provider if set in session or profile
        user_preferred_provider = None
        if request.user.is_authenticated:
            # Try to get from user profile if available
            user_preferred_provider = getattr(request.user, 'preferred_ai_provider', None)
        
        # If no user preference, check session
        if not user_preferred_provider and 'preferred_ai_provider' in request.session:
            user_preferred_provider = request.session.get('preferred_ai_provider')
            
        # If user has a preference and it's configured, use it
        if user_preferred_provider in ['openai', 'gemini']:
            if (user_preferred_provider == 'openai' and openai_configured) or \
               (user_preferred_provider == 'gemini' and gemini_configured):
                return redirect('itineraries:ai_itinerary_form', provider=user_preferred_provider)
        
        # No valid user preference, select based on performance metrics
        try:
            # Get performance metrics from cache or database
            from django.core.cache import cache
            openai_metrics = cache.get('openai_performance_metrics', {'avg_response_time': 2.0, 'success_rate': 0.95})
            gemini_metrics = cache.get('gemini_performance_metrics', {'avg_response_time': 1.8, 'success_rate': 0.92})
            
            # Simple scoring algorithm: lower response time is better, higher success rate is better
            # Normalize and combine scores (70% weight on success rate, 30% on response time)
            openai_score = (0.7 * openai_metrics['success_rate']) + (0.3 * (1.0 / openai_metrics['avg_response_time']))
            gemini_score = (0.7 * gemini_metrics['success_rate']) + (0.3 * (1.0 / gemini_metrics['avg_response_time']))
            
            # Select the provider with the better score
            selected_provider = 'openai' if openai_score >= gemini_score else 'gemini'
            logger.info(f"Auto-selected AI provider: {selected_provider} (scores: OpenAI={openai_score:.2f}, Gemini={gemini_score:.2f})")
            
            return redirect('itineraries:ai_itinerary_form', provider=selected_provider)
            
        except Exception as e:
            # If there's any error in the performance-based selection, default to OpenAI
            logger.warning(f"Error during AI provider auto-selection: {str(e)}. Defaulting to OpenAI.")
            return redirect('itineraries:ai_itinerary_form', provider='openai')
    
    # If auto_select is False, show the provider selection page
    return render(request, 'itineraries/ai_provider_selection.html', {
        'openai_configured': openai_configured,
        'gemini_configured': gemini_configured,
    })

@login_required
def save_ai_preference(request):
    """
    Save the user's preferred AI provider to their session and profile if available.
    
    This view handles the POST request from the AI itinerary form when a user
    chooses to save their preferred AI provider. The preference is stored both in
    the session for immediate use and in the user profile for long-term persistence
    if the user model supports it.
    
    Args:
        request: The HTTP request object containing the preferred_provider in POST data
        
    Returns:
        HttpResponse: Redirect back to the AI itinerary form with the selected provider
    """
    if request.method == 'POST':
        preferred_provider = request.POST.get('preferred_provider')
        
        # Validate the provider
        if preferred_provider not in ['openai', 'gemini']:
            messages.error(request, _("Invalid AI provider selected."))
            return redirect('itineraries:ai_auto_select')
        
        # Save to session for immediate use
        request.session['preferred_ai_provider'] = preferred_provider
        
        # Try to save to user profile if available
        if request.user.is_authenticated:
            try:
                # Check if user model has the field
                if hasattr(request.user, 'preferred_ai_provider'):
                    request.user.preferred_ai_provider = preferred_provider
                    request.user.save(update_fields=['preferred_ai_provider'])
                # If not, try to get or create user profile
                elif hasattr(request.user, 'profile'):
                    profile = request.user.profile
                    if hasattr(profile, 'preferred_ai_provider'):
                        profile.preferred_ai_provider = preferred_provider
                        profile.save(update_fields=['preferred_ai_provider'])
            except Exception as e:
                # Log the error but don't interrupt the user experience
                logger.warning(f"Error saving AI provider preference to user profile: {str(e)}")
        
        messages.success(request, _(f"{preferred_provider.title()} has been set as your default AI provider."))
        
        # Redirect back to the form with the selected provider
        return redirect('itineraries:ai_itinerary_form', provider=preferred_provider)
    
    # If not POST, redirect to auto-select
    return redirect('itineraries:ai_auto_select')

@login_required
def ai_itinerary_form(request, provider='openai'):
    """
    Display form for AI itinerary generation with the specified provider.
    
    This view shows the form for users to input their preferences for 
    AI-generated travel itineraries using the specified AI provider.
    
    Args:
        request: The HTTP request object
        provider: The AI provider to use ('openai' or 'gemini')
        
    Returns:
        HttpResponse: Rendered template with the itinerary form
    """
    # Validate provider
    provider = provider.lower()
    if provider not in ['openai', 'gemini']:
        messages.error(request, _("Invalid AI provider specified."))
        return redirect('itineraries:select_ai_provider')
    
    # Check if the selected provider is configured using multiple methods
    # This ensures we detect the API key even if it's not in os.environ
    env_api_key = os.environ.get(f'{provider.upper()}_API_KEY')
    getenv_api_key = os.getenv(f'{provider.upper()}_API_KEY')
    
    # For OpenAI, also check for the hardcoded fallback key
    hardcoded_key = None
    if provider == 'openai':
        hardcoded_key = "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"
    elif provider == 'gemini':
        hardcoded_key = "AIzaSyDJ177kr7nMG-74rB4cbAZmbpFEuk_XoRo"
    
    # Check if any of the methods found a key
    provider_configured = bool(env_api_key or getenv_api_key or hardcoded_key)
    
    # Log which source we're using for debugging
    if env_api_key:
        logger.info(f"Using {provider.upper()}_API_KEY from os.environ.get()")
    elif getenv_api_key:
        logger.info(f"Using {provider.upper()}_API_KEY from os.getenv()")
    elif hardcoded_key:
        logger.info(f"Using hardcoded {provider.capitalize()} API key as fallback")
    
    if not provider_configured:
        messages.error(request, _(f"{provider.capitalize()} API key is not configured."))
        return redirect('itineraries:select_ai_provider')
    
    # Get all active destinations for the form and order by city name
    destinations = Destination.objects.filter(is_active=True).order_by('city', 'name')
    # Annotate each destination with a display name that shows city name
    for dest in destinations:
        dest.display_name = dest.city or dest.name
    
    # Common interests for the form
    interests = [
        'History', 'Art', 'Culture', 'Food', 'Shopping', 
        'Nature', 'Adventure', 'Relaxation', 'Architecture', 
        'Nightlife', 'Family-friendly', 'Photography'
    ]
    
    # Budget levels
    budget_levels = ['budget', 'medium', 'luxury']
    
    # Travel pace options
    travel_paces = ['relaxed', 'moderate', 'intensive']
    
    # Default start date (30 days from now)
    default_start_date = timezone.now().date() + timedelta(days=30)
    
    # Default end date (7 days after start date)
    default_end_date = default_start_date + timedelta(days=7)
    
    # Check API key configuration using multiple methods for both providers
    # This ensures we detect the API key even if it's not in os.environ
    
    # Check OpenAI API key
    openai_env_key = os.environ.get('OPENAI_API_KEY')
    openai_getenv_key = os.getenv('OPENAI_API_KEY')
    openai_hardcoded_key = "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"
    openai_configured = bool(openai_env_key or openai_getenv_key or openai_hardcoded_key)
    
    # Check Gemini API key
    gemini_env_key = os.environ.get('GEMINI_API_KEY')
    gemini_getenv_key = os.getenv('GEMINI_API_KEY')
    gemini_hardcoded_key = "AIzaSyDJ177kr7nMG-74rB4cbAZmbpFEuk_XoRo"
    gemini_configured = bool(gemini_env_key or gemini_getenv_key or gemini_hardcoded_key)
    
    # Log API key configuration status
    logger.info(f"OpenAI API key configured: {openai_configured}")
    logger.info(f"Gemini API key configured: {gemini_configured}")
    
    context = {
        'provider': provider,
        'destinations': destinations,
        'interests': interests,
        'budget_levels': budget_levels,
        'travel_paces': travel_paces,
        'default_start_date': default_start_date.strftime('%Y-%m-%d'),
        'default_end_date': default_end_date.strftime('%Y-%m-%d'),
        'openai_configured': openai_configured,
        'gemini_configured': gemini_configured,
    }
    
    # Render the main AI itinerary form template with all necessary context
    return render(request, 'itineraries/ai_itinerary_form.html', context)

@login_required
@require_http_methods(["GET", "POST"])
def ai_generate_itinerary(request, provider='openai'):
    """
    Process the AI itinerary generation form and create a new itinerary.
    
    This view handles the form submission, calls the appropriate AI service to generate
    the itinerary, and creates the corresponding database records.
    
    Args:
        request: The HTTP request object containing form data
        provider: The AI provider to use ('openai' or 'gemini')
        
    Returns:
        HttpResponse: Redirect to the new itinerary or back to the form with errors
    """
    # Handle GET requests by redirecting to the form
    if request.method != 'POST':
        return redirect('itineraries:ai_itinerary_form', provider=provider)
    
    # Validate provider
    provider = provider.lower()
    if provider not in ['openai', 'gemini']:
        messages.error(request, _("Invalid AI provider specified."))
        return redirect('itineraries:select_ai_provider')
    
    # Check if the selected provider is configured using multiple methods
    # This ensures we detect the API key even if it's not in os.environ
    env_api_key = os.environ.get(f'{provider.upper()}_API_KEY')
    getenv_api_key = os.getenv(f'{provider.upper()}_API_KEY')
    
    # For OpenAI, also check for the hardcoded fallback key
    hardcoded_key = None
    if provider == 'openai':
        hardcoded_key = "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"
    elif provider == 'gemini':
        hardcoded_key = "AIzaSyDJ177kr7nMG-74rB4cbAZmbpFEuk_XoRo"
    
    # Check if any of the methods found a key
    provider_configured = bool(env_api_key or getenv_api_key or hardcoded_key)
    
    # Log which source we're using for debugging
    if env_api_key:
        logger.info(f"Using {provider.upper()}_API_KEY from os.environ.get() in itinerary generation")
    elif getenv_api_key:
        logger.info(f"Using {provider.upper()}_API_KEY from os.getenv() in itinerary generation")
    elif hardcoded_key:
        logger.info(f"Using hardcoded {provider.capitalize()} API key as fallback in itinerary generation")
    
    if not provider_configured:
        messages.error(request, _(f"{provider.capitalize()} API key is not configured."))
        return redirect('itineraries:select_ai_provider')
    
    # Get form data
    destination_id = request.POST.get('destination_id')
    start_date_str = request.POST.get('start_date')
    end_date_str = request.POST.get('end_date')
    interests = request.POST.getlist('interests')
    budget_level = request.POST.get('budget_level', 'medium')
    travel_pace = request.POST.get('travel_pace', 'moderate')
    accessibility_needs = request.POST.getlist('accessibility_needs')
    title = request.POST.get('title', f'AI-Generated Itinerary ({provider.capitalize()})')
    description = request.POST.get('description', '')
    is_public = request.POST.get('is_public') == 'on'
    
    # Validate required fields
    if not all([destination_id, start_date_str, end_date_str, interests]):
        messages.error(request, _("Please fill in all required fields."))
        return redirect('itineraries:ai_itinerary_form', provider=provider)
    
    try:
        # Parse dates
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Validate date range
        if start_date >= end_date:
            messages.error(request, _("End date must be after start date."))
            return redirect('itineraries:ai_itinerary_form', provider=provider)
        
        # Get destination
        destination = Destination.objects.get(id=destination_id, is_active=True)
        
        # Create itinerary
        itinerary = Itinerary.objects.create(
            user=request.user,
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            is_public=is_public,
            is_ai_generated=True,
            ai_provider=provider  # Store which AI provider was used
        )
        
        # Get the appropriate AI service with proper error handling
        try:
            # Create the AI service instance with the selected provider
            ai_service = AIServiceFactory.get_service(provider)
            
            # Log which AI provider is being used
            logger.info(f"Using {provider.capitalize()} AI service for itinerary generation")
        except Exception as e:
            # Log the error with the AI service initialization
            logger.error(f"Error initializing {provider} AI service: {str(e)}", exc_info=True)
            
            # Delete the partially created itinerary
            itinerary.delete()
            
            # Show error message to the user
            messages.error(
                request,
                _(f"Could not initialize {provider.capitalize()} AI service. Please check your API key and try again.")
            )
            return redirect('itineraries:ai_itinerary_form', provider=provider)
        
        try:
            # Generate the itinerary using the selected AI service
            ai_itinerary = ai_service.generate_itinerary(
                destination=destination,
                start_date=start_date,
                end_date=end_date,
                interests=interests,
                budget_level=budget_level,
                travel_pace=travel_pace,
                accessibility_needs=accessibility_needs
            )
            
            # Check for errors in the AI response
            if 'error' in ai_itinerary:
                raise Exception(ai_itinerary['error'])
            
            # Create itinerary days and activities from AI response
            for day_data in ai_itinerary.get('days', []):
                day = ItineraryDay.objects.create(
                    itinerary=itinerary,
                    date=day_data['date'],
                    title=day_data.get('title', f"Day {day_data['day_number']}"),
                    notes=day_data.get('notes', '')
                )
                
                # Add activities for the day
                for activity_data in day_data.get('activities', []):
                    Activity.objects.create(
                        day=day,
                        title=activity_data['title'],
                        description=activity_data.get('description', ''),
                        start_time=activity_data.get('start_time'),
                        end_time=activity_data.get('end_time'),
                        location=activity_data.get('location', ''),
                        notes=activity_data.get('notes', '')
                    )
            
            # Add success message and redirect to the new itinerary
            messages.success(request, _("Your AI-generated itinerary is ready!"))
            return redirect('itineraries:itinerary_detail', pk=itinerary.pk)
            
        except Exception as e:
            # Log the error and show a user-friendly message
            logger.error(f"Error generating {provider} itinerary: {str(e)}", exc_info=True)
            
            # Delete the partially created itinerary
            itinerary.delete()
            
            messages.error(
                request, 
                _(f"An error occurred while generating your itinerary with {provider.capitalize()}. Please try again later.")
            )
            return redirect('itineraries:ai_itinerary_form', provider=provider)
            
    except Destination.DoesNotExist:
        messages.error(request, _("Selected destination not found."))
        return redirect('itineraries:ai_itinerary_form', provider=provider)
    except ValueError as e:
        messages.error(request, _("Invalid date format. Please use YYYY-MM-DD."))
        return redirect('itineraries:ai_itinerary_form', provider=provider)
    except Exception as e:
        logger.error(f"Unexpected error in ai_generate_itinerary: {str(e)}", exc_info=True)
        messages.error(request, _("An unexpected error occurred. Please try again."))
        return redirect('itineraries:ai_itinerary_form', provider=provider)

# Legacy view for backward compatibility
def ai_generate_itinerary_legacy(request):
    """
    Legacy view for backward compatibility with old URLs.
    Redirects to the provider selection page.
    """
    return redirect('itineraries:select_ai_provider')
