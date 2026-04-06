"""
URL configuration for the itineraries application.

This module defines the URL patterns for the itineraries app.
Each URL is mapped to a specific view function or class.
"""

from django.urls import path
from . import views
from . import views_ai_new as ai_views

app_name = 'itineraries'  # Application namespace for URL naming

urlpatterns = [
    # List views
    path('', views.ItineraryListView.as_view(), 
         name='itinerary_list'),  # List all public itineraries
    
    path('my/', views.MyItinerariesView.as_view(), 
         name='my_itineraries'),  # List current user's itineraries
    
    # Detail, create, update, delete views for itineraries
    path('<int:pk>/', views.ItineraryDetailView.as_view(), 
         name='itinerary_detail'),  # View a specific itinerary
    
    path('create/', views.ItineraryCreateView.as_view(), 
         name='itinerary_create'),  # Create a new itinerary
    
    path('<int:pk>/update/', views.ItineraryUpdateView.as_view(), 
         name='itinerary_update'),  # Update an existing itinerary
    
    path('<int:pk>/delete/', views.ItineraryDeleteView.as_view(), 
         name='itinerary_delete'),  # Delete an existing itinerary
    
    # Day management
    path('day/<int:day_id>/edit/', views.edit_itinerary_day, 
         name='edit_day'),  # Edit day details
    
    # Activity management
    path('day/<int:day_id>/activity/add/', views.add_activity, 
         name='add_activity'),  # Add a new activity to a day
    
    path('activity/<int:activity_id>/edit/', views.edit_activity, 
         name='edit_activity'),  # Edit an existing activity
    
    path('activity/<int:activity_id>/delete/', views.delete_activity, 
         name='delete_activity'),  # Delete an existing activity
    
    # Sharing
    path('<int:pk>/share/', views.itinerary_share, 
         name='itinerary_share'),  # Share an itinerary
         
    # AI Itinerary Generation with provider selection
    path('ai/select-provider/', ai_views.select_ai_provider, 
         name='select_ai_provider'),  # Select AI provider (OpenAI or Gemini)
         
    path('ai/auto/', lambda r: ai_views.select_ai_provider(r, auto_select=True),
         name='ai_auto_select'),  # Auto-select best available AI provider
         
    path('ai/save-preference/', ai_views.save_ai_preference,
         name='save_ai_preference'),  # Save user's preferred AI provider
         
    path('ai/<str:provider>/', ai_views.ai_itinerary_form, 
         name='ai_itinerary_form'),  # Form for AI itinerary generation with specific provider
         
    path('ai/<str:provider>/generate/', ai_views.ai_generate_itinerary, 
         name='ai_generate_itinerary'),  # Process AI itinerary generation with specific provider
         
    # Legacy routes for backward compatibility
    path('ai-generate/', ai_views.select_ai_provider, 
         name='ai_itinerary_legacy'),  # Redirects to provider selection
         
    path('ai/', lambda r: redirect('itineraries:ai_auto_select'), 
         name='ai_itinerary_root'),  # Default to auto-select
         
    # Other AI features
    path('ai-activities/<int:destination_id>/', views.ai_activity_recommendations, 
         name='ai_activity_recommendations'),  # Get AI activity recommendations
         
    path('<int:itinerary_id>/ai-enhance/<int:day_id>/', views.ai_enhance_day, 
         name='ai_enhance_day'),  # Enhance a specific day with AI suggestions
]
