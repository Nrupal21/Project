"""
URL patterns for the transportation app.

This module defines URL patterns for the transportation app,
including web views and API endpoints for transportation types,
providers, routes, schedules, and options.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

# Create a router for API views
router = DefaultRouter()
router.register(r'types', views.TransportationTypeViewSet, basename='api-transportation-type')
router.register(r'providers', views.TransportationProviderViewSet, basename='api-provider')
router.register(r'routes', views.RouteViewSet, basename='api-route')
router.register(r'schedules', views.ScheduleViewSet, basename='api-schedule')
router.register(r'options', views.TransportationOptionViewSet, basename='api-transportation-option')

# URL namespace
app_name = 'transportation'

# URL patterns for web views
urlpatterns = [
    # Transportation Type views
    path('types/', 
         views.TransportationTypeListView.as_view(), 
         name='type_list'),
    
    path('types/<slug:slug>/', 
         views.TransportationTypeDetailView.as_view(), 
         name='type_detail'),
    
    # Transportation Provider views
    path('providers/', 
         views.ProviderListView.as_view(), 
         name='provider_list'),
    
    path('providers/<slug:slug>/', 
         views.ProviderDetailView.as_view(), 
         name='provider_detail'),
    
    # Route views
    path('routes/', 
         views.RouteListView.as_view(), 
         name='route_list'),
    
    path('routes/<slug:slug>/', 
         views.RouteDetailView.as_view(), 
         name='route_detail'),
    
    # Destination transportation options
    path('destination/<int:destination_id>/', 
         views.destination_transport_options, 
         name='destination_options'),
    
    # Route search
    path('search/', 
         views.search_routes, 
         name='search_routes'),
    
    # API endpoints
    path('api/', include(router.urls)),
]
