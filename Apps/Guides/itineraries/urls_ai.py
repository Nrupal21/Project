"""
URL configuration for AI-related views in the itineraries application.

This module defines the URL patterns for AI-powered itinerary generation.
It's separated from the main URLs file for better organization.
"""

from django.urls import path
from . import views_ai

app_name = 'itineraries'  # Use the same app namespace as main URLs

urlpatterns = [
    # AI Itinerary Generation
    path('ai-generate/', views_ai.ai_itinerary_form, 
         name='ai_itinerary_form'),  # Form for AI itinerary generation
         
    path('ai-generate/create/', views_ai.ai_generate_itinerary, 
         name='ai_generate_itinerary'),  # Process AI itinerary generation
         
    # Note: The following URLs are kept in the main urls.py for now
    # as they might have dependencies on other views
    # path('ai-activities/<int:destination_id>/', views_ai.ai_activity_recommendations, 
    #      name='ai_activity_recommendations'),
    # path('<int:itinerary_id>/ai-enhance/<int:day_id>/', views_ai.ai_enhance_day, 
    #      name='ai_enhance_day'),
]
