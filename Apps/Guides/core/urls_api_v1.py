"""
Core API v1 URL configuration.

This module wires DRF APIViews for core functionality under the versioned path.
Mounted at: /api/v1/core/

Endpoints:
- GET  /nearby-destinations/ -> NearbyDestinationsView
- POST /user-location/       -> UserLocationView
"""
from django.urls import path

from .api_views import NearbyDestinationsView, UserLocationView

# App namespace for URL reversing
app_name = "core_api_v1"

urlpatterns = [
    # Nearby destinations search using Haversine
    path(
        "nearby-destinations/",
        NearbyDestinationsView.as_view(),
        name="nearby_destinations",
    ),
    # Persist user's location in the session
    path(
        "user-location/",
        UserLocationView.as_view(),
        name="user_location",
    ),
]
