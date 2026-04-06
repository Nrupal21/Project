"""
URL patterns for the emergency app.

This module defines the URL patterns for emergency services, contacts, 
safety information, and emergency guides for both web views and API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .category_safety_view import CategorySafetyInfoView
from .risk_level_view import RiskLevelSafetyInfoView
from .guide_views import EmergencyGuideListView, EmergencyGuideDetailView
from .destination_views import DestinationEmergencyInfoView, RegionEmergencyInfoView
from .api_views import (
    destination_emergency_services_api,
    destination_emergency_contacts_api,
    destination_safety_info_api
)

# Create a router for DRF API viewsets
router = DefaultRouter()

# Register all API viewsets with appropriate base names
# Each viewset handles its own CRUD operations and additional actions
router.register(r'service-types', views.EmergencyServiceTypeViewSet, basename='api-emergency-service-type')
router.register(r'services', views.EmergencyServiceViewSet, basename='api-emergency-service')
router.register(r'contacts', views.EmergencyContactViewSet, basename='api-emergency-contact')
router.register(r'safety', views.SafetyInformationViewSet, basename='api-safety-information')
router.register(r'guides', views.EmergencyGuideViewSet, basename='api-emergency-guide')

# App namespace for URL reversing
app_name = 'emergency'

urlpatterns = [
    # Web view URLs
    # --------------
    # Service types list and detail views
    path('service-types/', views.EmergencyServiceTypeListView.as_view(), name='service-types-list'),
    path('service-types/<slug:slug>/', views.EmergencyServiceTypeDetailView.as_view(), name='service-type-detail'),
    
    # Emergency services list and detail views
    path('services/', views.EmergencyServiceListView.as_view(), name='services-list'),
    path('services/<slug:slug>/', views.EmergencyServiceDetailView.as_view(), name='service-detail'),
    
    # Emergency contacts views
    path('contacts/', views.EmergencyContactListView.as_view(), name='contacts-list'),
    path('contacts/country/<str:country_code>/', views.CountryEmergencyContactsView.as_view(), name='country-contacts'),
    path('contacts/region/<slug:region_slug>/', views.RegionEmergencyContactsView.as_view(), name='region-contacts'),
    
    # Safety information views
    path('safety/', views.SafetyInformationListView.as_view(), name='safety-list'),
    path('safety/<slug:slug>/', views.SafetyInformationDetailView.as_view(), name='safety-detail'),
    path('safety/category/<slug:category>/', CategorySafetyInfoView.as_view(), name='category-safety'),
    path('safety/risk-level/<str:risk_level>/', RiskLevelSafetyInfoView.as_view(), name='risk-level-safety'),
    
    # Emergency guides views
    path('guides/', EmergencyGuideListView.as_view(), name='guides-list'),
    path('guides/<slug:slug>/', EmergencyGuideDetailView.as_view(), name='guide-detail'),
    
    # Destination-specific emergency information
    path('destination/<slug:destination_slug>/', DestinationEmergencyInfoView.as_view(), 
         name='destination-emergency'),
    path('region/<slug:region_slug>/emergency/', RegionEmergencyInfoView.as_view(), 
         name='region-emergency'),
    
    # API endpoints
    # ------------
    # Include all viewset routes from the DRF router
    path('api/', include(router.urls)),
    
    # Additional custom API endpoints
    path('api/destination/<slug:destination_slug>/services/', 
         destination_emergency_services_api, 
         name='api-destination-emergency-services'),
         
    path('api/destination/<slug:destination_slug>/contacts/', 
         destination_emergency_contacts_api, 
         name='api-destination-emergency-contacts'),
         
    path('api/destination/<slug:destination_slug>/safety/', 
         destination_safety_info_api, 
         name='api-destination-safety-info'),
]
