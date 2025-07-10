"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# URL patterns for the entire project
urlpatterns = [
    # Core app URLs with namespace
    path('', include(('core.app_urls', 'core'), namespace='core')),
    
    # Admin interface
    path('admin/', admin.site.urls),
    
    # Allauth URLs for authentication
    path('accounts/', include('allauth.urls')),
    
    # Destinations app URLs - include template and API URLs
    path('destinations/', include(('destinations.urls', 'destinations'), namespace='destinations')),
    
    # Tours app URLs - include template and API URLs
    path('tours/', include(('tours.urls', 'tours'), namespace='tours')),
    
    # User authentication - include with app_name from accounts/urls.py
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
