"""
URL patterns for the tours app.

This module defines all URL patterns related to tours functionality,
including tour listing, details, API endpoints, and related views.
Each URL pattern is mapped to its corresponding view function or class.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for REST API views
router = DefaultRouter()
# Using basename parameter since we're not using a queryset in the viewset
router.register(r'api/tours', views.TourViewSet, basename='tour')
router.register(r'api/categories', views.TourCategoryViewSet, basename='tourcategory')

# App namespace for URL reversing
app_name = 'tours'

# URL patterns for the tours app
urlpatterns = [
    # API routes
    path('', include(router.urls)),
    
    # Web view routes
    path('', views.tour_list_view, name='list'),
    path('<slug:slug>/', views.tour_detail_view, name='detail'),
    path('category/<slug:slug>/', views.TourCategoryView.as_view(), name='category_detail'),
    path('book/<slug:slug>/', views.tour_booking_view, name='booking'),
    
    # Tour dates API
    path('api/dates/<int:tour_id>/', views.tour_dates_api, name='tour_dates_api'),
]
