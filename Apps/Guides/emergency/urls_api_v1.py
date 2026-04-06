"""
Emergency API v1 URL configuration.

Mount under: /api/v1/emergency/

Exposes DRF ViewSets and custom endpoints for destination-specific data.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .api_views import (
    destination_emergency_services_api,
    destination_emergency_contacts_api,
    destination_safety_info_api,
)

app_name = "emergency_api_v1"

router = DefaultRouter()
router.register(r"service-types", views.EmergencyServiceTypeViewSet, basename="emergency-service-type")
router.register(r"services", views.EmergencyServiceViewSet, basename="emergency-service")
router.register(r"contacts", views.EmergencyContactViewSet, basename="emergency-contact")
router.register(r"safety", views.SafetyInformationViewSet, basename="safety-information")
router.register(r"guides", views.EmergencyGuideViewSet, basename="emergency-guide")

urlpatterns = [
    # Router-based endpoints
    path("", include(router.urls)),

    # Additional custom endpoints
    path(
        "destination/<slug:destination_slug>/services/",
        destination_emergency_services_api,
        name="destination-emergency-services",
    ),
    path(
        "destination/<slug:destination_slug>/contacts/",
        destination_emergency_contacts_api,
        name="destination-emergency-contacts",
    ),
    path(
        "destination/<slug:destination_slug>/safety/",
        destination_safety_info_api,
        name="destination-safety-info",
    ),
]
