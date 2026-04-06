"""
URL patterns for the core app.

This module defines the URL patterns for the core functionality of the website,
including the home page, about page, contact page, and other general pages.
Each URL pattern is mapped to a specific view function or class.
"""

from django.urls import path
from django.views.decorators.http import require_http_methods
from . import views

# App namespace for URL reversing
app_name = 'core'

# URL patterns for the core app
# Import core views
from .views import (
    HomeView, AboutView, ContactView, PrivacyPolicyView, 
    TermsOfServiceView, get_nearby_destinations_api, set_user_location,
    GalleryView
)
# Import debug views
from .views_debug import DebugDestinationsView
# Import API monitoring view
from .views_api_monitor import APIMonitorView

urlpatterns = [
    # Home page URL - displays featured destinations, tours, and other content
    path('', HomeView.as_view(), name='home'),
    
    # About page URL - displays information about the company
    path('about/', AboutView.as_view(), name='about'),
    
    # Gallery page URL - displays a grid of destination images
    path('gallery/', GalleryView.as_view(), name='gallery'),
    
    # Contact page URL - displays contact information and form
    path('contact/', ContactView.as_view(), name='contact'),
    
    # Privacy policy page URL
    path('privacy-policy/', PrivacyPolicyView.as_view(), name='privacy_policy'),
    
    # Terms of service page URL
    path('terms-of-service/', TermsOfServiceView.as_view(), name='terms_of_service'),
    
    # API Endpoints
    path('api/nearby-destinations/', require_http_methods(['GET'])(get_nearby_destinations_api), name='nearby_destinations_api'),
    path('api/set-location/', set_user_location, name='set_user_location'),
    
    # Debug URLs
    path('debug/destinations/', DebugDestinationsView.as_view(), name='debug_destinations'),
    
    # API Monitoring Dashboard
    path('api-monitor/', APIMonitorView.as_view(), name='api_monitor'),
]
