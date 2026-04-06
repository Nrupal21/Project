"""
Core API views (v1).

This module defines DRF-based API endpoints for core functionality, providing
consistent JSON responses and detailed inline documentation for developers.

Endpoints provided (mounted under /api/v1/core/):
- GET  /nearby-destinations/  -> NearbyDestinationsView
- POST /user-location/        -> UserLocationView

Notes:
- Responses follow a consistent envelope: {success, data, count?, message?, errors?}
- CSRF is disabled for the user-location POST to maintain parity with the legacy endpoint.
- Heavy logic (Haversine etc.) is re-used from `core.views.get_nearby_destinations()`.
"""
from typing import Any, Dict
import logging

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from destinations.serializers import NearbyDestinationSerializer
from .views import get_nearby_destinations

logger = logging.getLogger(__name__)


class NearbyDestinationsView(APIView):
    """
    Return destinations near a given lat/lng within an optional radius and limit.

    Query Parameters:
    - lat (float, required): Latitude of the reference point.
    - lng (float, required): Longitude of the reference point.
    - radius (float, optional): Search radius in km. Default: 15.
    - limit (int, optional): Max number of results. Default: 4.

    Returns:
    - 200 OK with {success, count, data: [Destination...]} on success
    - 400 Bad Request with {success: False, errors} for invalid inputs
    - 500 Internal Server Error with {success: False, errors} if something fails

    Example:
    GET /api/v1/core/nearby-destinations/?lat=28.6139&lng=77.2090&radius=50&limit=4
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):  # noqa: D401
        """Handle GET requests for nearby destinations using validated query params."""
        try:
            # Parse and validate query params
            lat_str = request.query_params.get("lat")
            lng_str = request.query_params.get("lng")
            if lat_str is None or lng_str is None:
                return Response(
                    {
                        "success": False,
                        "errors": {"detail": "lat and lng are required query parameters"},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            lat = float(lat_str)
            lng = float(lng_str)
            radius = float(request.query_params.get("radius", 15))
            limit = int(request.query_params.get("limit", 4))

            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                return Response(
                    {"success": False, "errors": {"detail": "Invalid latitude or longitude values"}},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Fetch nearby destinations (adds .distance attribute)
            nearby = get_nearby_destinations(lat, lng, radius, limit)

            # Serialize using a dedicated serializer that includes distance + image
            serializer = NearbyDestinationSerializer(nearby, many=True, context={"request": request})
            data = serializer.data

            return Response({"success": True, "count": len(data), "data": data}, status=status.HTTP_200_OK)

        except (ValueError, TypeError) as e:
            logger.exception("Invalid parameters for NearbyDestinationsView")
            return Response(
                {"success": False, "errors": {"detail": "Invalid parameters", "info": str(e)}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:  # pragma: no cover - defensive
            logger.exception("Unexpected error in NearbyDestinationsView")
            return Response(
                {
                    "success": False,
                    "errors": {"detail": "An error occurred while fetching nearby destinations", "info": str(e)},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
class UserLocationView(APIView):
    """
    Store the user's location (lat/lng) in the session for personalization.

    Body (JSON):
    - lat (float, required): Latitude
    - lng (float, required): Longitude

    Returns:
    - 200 OK with {success: True, message}
    - 400 Bad Request with {success: False, errors} for invalid inputs

    Security:
    - CSRF is explicitly disabled to match legacy endpoint behavior and to allow
      setting location from JS without a CSRF token. Adjust as needed.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):  # noqa: D401
        """Handle POST requests to persist user location in the session."""
        try:
            data = request.data or {}
            lat = float(data.get("lat"))
            lng = float(data.get("lng"))

            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                return Response(
                    {"success": False, "errors": {"detail": "Invalid coordinates"}},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Store in session
            request.session["user_lat"] = lat
            request.session["user_lng"] = lng
            request.session.modified = True

            return Response({"success": True, "message": "Location updated"}, status=status.HTTP_200_OK)

        except (ValueError, TypeError):
            return Response(
                {"success": False, "errors": {"detail": "Invalid data"}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:  # pragma: no cover - defensive
            logger.exception("Unexpected error in UserLocationView")
            return Response(
                {"success": False, "errors": {"detail": "An error occurred", "info": str(e)}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
