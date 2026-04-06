"""
URL configuration for guides project.

This module contains the URL patterns for the main project.
It includes URLs for admin, API endpoints, and app-specific URLs.
All routes are organized here for centralized management.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Define URL patterns for the entire project
urlpatterns = [
    # Admin interface URL - provides access to Django admin panel
    path('admin/', admin.site.urls),
    
    # Core app URLs - includes home page, about, contact, etc.
    path('', include('core.urls')),
    
    # Destinations app URLs - includes destination listings and details
    path('destinations/', include('destinations.urls')),
    
    # Tours app URLs - includes tour packages and bookings
    path('tours/', include('tours.urls')),

    # Versioned API v1 (DRF)
    # These routes expose JSON APIs using DRF ViewSets and APIViews
    path('api/v1/core/', include('core.urls_api_v1')),
    path('api/v1/destinations/', include('destinations.urls_api_v1')),
    path('api/v1/emergency/', include('emergency.urls_api_v1')),
    path('api/v1/transportation/', include('transportation.urls_api_v1')),
    path('api/v1/tours/', include('tours.urls_api_v1')),

    # API endpoints for REST framework (login/logout for browsable API)
    path('api/', include('rest_framework.urls')),

    # Authentication URLs - combines Django auth, social auth, and custom auth views
    path('accounts/', include('accounts.urls')),  # Our custom account management views
    path('accounts/', include('allauth.urls')),  # Django-allauth authentication
    path('social-auth/', include('social_django.urls', namespace='social')),  # Social auth
    
    # Additional app URLs
    path('bookings/', include('bookings.urls')),
    # Reviews app with enhanced features and indigo/violet styled UI
    path('reviews/', include('reviews.urls')),
    path('emergency/', include('emergency.urls')),
    path('transportation/', include('transportation.urls')),
    path('itineraries/', include('itineraries.urls')),
    path('security/', include('security.urls', namespace='security')),
    
    # Rewards system URLs - includes points dashboard, redemption, and history
    path('rewards/', include('rewards.urls', namespace='rewards')),
    
    # Notification system URLs - includes notification listing, marking as read, etc.
    path('notifications/', include('notifications.urls', namespace='notifications')),
    
    # Travel Gallery app URLs - includes photo gallery with locations and metadata
    # Namespaced as 'travel_gallery' for URL reversing
    path('gallery/', include('travel_gallery.urls', namespace='travel_gallery')),
    
    # Guides app URLs - includes guide dashboard and management
    path('guides/', include('guides.app_urls', namespace='guides')),
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
