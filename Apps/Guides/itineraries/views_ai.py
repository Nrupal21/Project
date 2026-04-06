"""
AI Itinerary Generation Views (Legacy).

This module contains legacy views for generating travel itineraries using AI.
These views now redirect to the new provider-aware views in views_ai_new.py.
"""

import os
import json
import logging
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from destinations.models import Destination
from .models import Itinerary, ItineraryDay, Activity
from .forms import ActivityForm
from .ai_services import ItineraryAIService

# Set up logging
logger = logging.getLogger(__name__)

@login_required
def ai_itinerary_form(request):
    """
    Legacy view that redirects to the new provider selection flow.
    
    This view now redirects to the new AI provider selection view,
    which allows users to choose between OpenAI and Gemini.
    
    Args:
        request: The HTTP request object
        
    Returns:
        HttpResponseRedirect: Redirect to the provider selection page
    """
    # Log that the legacy view was accessed
    logger.info("Legacy AI itinerary form view accessed, redirecting to provider selection")
    
    # Redirect to the new provider selection view
    messages.info(request, _("Please select an AI provider to generate your itinerary."))
    return redirect('itineraries:select_ai_provider')

@login_required
@require_POST
def ai_generate_itinerary(request):
    """
    Legacy view that redirects to the new provider selection flow.
    
    This view now redirects to the new AI provider selection view.
    The actual itinerary generation is handled by views_ai_new.py.
    
    Args:
        request: The HTTP request object containing form data
        
    Returns:
        HttpResponseRedirect: Redirect to the provider selection page
    """
    # Log that the legacy view was accessed
    logger.info("Legacy AI generate itinerary view accessed, redirecting to provider selection")
    
    # Redirect to the new provider selection view
    messages.info(request, _("Please select an AI provider to generate your itinerary."))
    return redirect('itineraries:select_ai_provider')
