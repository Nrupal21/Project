"""
Destinations API v1 URL configuration.

Mount under: /api/v1/destinations/

Provides REST endpoints via DRF ViewSets:
- /destinations/
- /regions/
- /attractions/
- /seasons/

Also provides AJAX API endpoints for destination management:
- /admin/approve-destination/<pk>/
- /admin/reject-destination/<pk>/
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DestinationViewSet, RegionViewSet, AttractionViewSet, SeasonViewSet
from .views.admin_api import api_approve_destination, api_reject_destination

app_name = "destinations_api_v1"

router = DefaultRouter()
router.register(r"destinations", DestinationViewSet)
router.register(r"regions", RegionViewSet)
# AttractionViewSet uses get_queryset; specify basename explicitly
router.register(r"attractions", AttractionViewSet, basename="attraction")
router.register(r"seasons", SeasonViewSet)

urlpatterns = [
    path("", include(router.urls)),
    # AJAX API endpoints for destination management
    path("admin/approve-destination/<int:pk>/", api_approve_destination, name="api_approve_destination"),
    path("admin/reject-destination/<int:pk>/", api_reject_destination, name="api_reject_destination"),
]
