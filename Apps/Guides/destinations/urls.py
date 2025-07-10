"""
URL configuration for the destinations app.

This module defines the URL patterns for the destinations app, including:
1. API endpoints using DRF router
2. Web page views for rendering HTML templates
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for our API viewsets
router = DefaultRouter()
router.register(r'regions', views.RegionViewSet, basename='region')
router.register(r'destinations', views.DestinationViewSet, basename='destination')
router.register(r'attractions', views.AttractionViewSet, basename='attraction')
router.register(r'seasons', views.SeasonViewSet, basename='season')

# The app name for URL namespacing
app_name = 'destinations'

# Define URL patterns, including both API and template views
urlpatterns = [
    # Web template views
    path('list/', views.destination_list_view, name='list'),  # This matches {% url 'destinations:list' %}
    path('<slug:slug>/', views.DestinationDetailView.as_view(), name='detail'),  # Detail view for a single destination
    
    # API endpoints
    path('api/', include(router.urls)),
    
    # Nearby destinations API
    path('api/nearby/', views.nearby_destinations, name='nearby_destinations'),
]
