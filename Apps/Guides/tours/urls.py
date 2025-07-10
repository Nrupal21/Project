"""
URL configuration for the tours app.

This module defines the URL patterns for the tours app, including:
1. Web template views for rendering tour lists and details
2. API endpoints for accessing tour data
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for API viewsets
router = DefaultRouter()
router.register(r'tours', views.TourViewSet, basename='tour')
router.register(r'categories', views.TourCategoryViewSet, basename='category')

# App namespace
app_name = 'tours'

# Define URL patterns, including both web views and API endpoints
urlpatterns = [
    # Web template views
    path('list/', views.tour_list_view, name='list'),  # URL for tour listing page
    path('<slug:slug>/', views.tour_detail_view, name='detail'),  # URL for tour details page
    
    # API endpoints
    path('api/', include(router.urls)),
]
