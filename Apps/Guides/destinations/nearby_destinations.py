"""
Nearby Destinations API module.

This module implements the API endpoint to find destinations near
a user's location using the Haversine formula for distance calculation.

The Haversine formula determines the great-circle distance between two points
on a sphere given their longitudes and latitudes. It's particularly important
in navigation and is used here to find destinations within a certain radius.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Destination
import math


@require_http_methods(["GET"])
def nearby_destinations(request):
    """
    API endpoint to find destinations near a specified location.
    
    Uses the Haversine formula to calculate distance between coordinates
    and returns destinations within the specified radius, sorted by proximity.
    This endpoint is useful for mobile apps and location-aware features that
    need to show users what destinations are near their current location.
    
    Query parameters:
        lat (float): Latitude of the user's location (required)
        lng (float): Longitude of the user's location (required)
        radius (float, optional): Search radius in kilometers. Default is 10.0.
        limit (int, optional): Maximum number of results to return. Default is 6.
    
    Returns:
        JsonResponse: JSON data with nearby destinations sorted by distance
            Format:
            {
                'success': bool,
                'count': int,
                'radius': float,
                'origin': {'latitude': float, 'longitude': float},
                'destinations': [
                    {
                        'id': int,
                        'name': str,
                        'slug': str,
                        'city': str,
                        'country': str,
                        'short_description': str,
                        'rating': float,
                        'price': float,
                        'latitude': float,
                        'longitude': float,
                        'distance': float,
                        'image_url': str
                    },
                    ...
                ]
            }
    """
    # Get query parameters from the request
    # Convert string parameters to appropriate numeric types
    try:
        latitude = float(request.GET.get('lat', 0))
        longitude = float(request.GET.get('lng', 0))
        radius = float(request.GET.get('radius', 20.0))  # Default 15km radius
        limit = int(request.GET.get('limit', 6))  # Default 6 results
    except (ValueError, TypeError) as e:
        # Return error response if parameters cannot be converted to numeric types
        return JsonResponse({
            'success': False,
            'error': 'Invalid parameters. Latitude, longitude must be valid coordinates.',
            'message': str(e)
        }, status=400)  # HTTP 400 Bad Request
    
    # Validate coordinates are within valid ranges for Earth
    # Latitude: -90° (South Pole) to 90° (North Pole)
    # Longitude: -180° to 180°
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return JsonResponse({
            'success': False,
            'error': 'Invalid coordinates. Latitude must be between -90 and 90, longitude between -180 and 180.'
        }, status=400)  # HTTP 400 Bad Request
    
    # Earth's radius in kilometers - Used in Haversine formula
    EARTH_RADIUS = 6371.0  # Average radius of Earth in km
    
    # Fetch all active destinations that have valid coordinate data
    # We filter out any destinations with NULL latitude or longitude values
    destinations = Destination.objects.filter(
        is_active=True,       # Only include active/published destinations
        latitude__isnull=False,  # Must have latitude
        longitude__isnull=False  # Must have longitude
    )
    
    # Calculate distances using the Haversine formula
    # The Haversine formula calculates the shortest distance between two points
    # on a sphere using their latitudes and longitudes
    nearby_destinations = []
    for destination in destinations:
        # Step 1: Convert latitude and longitude from degrees to radians
        # Math functions in Python require angles in radians, not degrees
        lat1_rad = math.radians(latitude)         # User's latitude
        lng1_rad = math.radians(longitude)        # User's longitude
        lat2_rad = math.radians(destination.latitude)  # Destination's latitude
        lng2_rad = math.radians(destination.longitude) # Destination's longitude
        
        # Step 2: Implement the Haversine formula
        # Formula: d = 2r * arcsin(sqrt(sin²((φ₂-φ₁)/2) + cos(φ₁)cos(φ₂)sin²((λ₂-λ₁)/2)))
        # Where φ is latitude, λ is longitude, and r is Earth's radius
        dlat = lat2_rad - lat1_rad  # Difference in latitudes
        dlng = lng2_rad - lng1_rad  # Difference in longitudes
        
        # Calculate the inner term of the Haversine formula
        # a = sin²(Δφ/2) + cos(φ₁)cos(φ₂)sin²(Δλ/2)
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
        
        # Calculate the central angle (c)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        # Calculate the distance (d = r * c)
        distance = EARTH_RADIUS * c  # Distance in kilometers
        
        # Add to results only if within the specified radius
        if distance <= radius:
            # Attach the calculated distance to the destination object
            # for sorting and display purposes
            destination.distance = round(distance, 1)  # Round to 1 decimal place for better readability
            nearby_destinations.append(destination)
    
    # Sort destinations by distance (closest first) and limit to requested number
    nearby_destinations.sort(key=lambda x: x.distance)
    nearby_destinations = nearby_destinations[:limit]
    
    # Prepare the results for JSON response
    # Convert Django model objects to dictionary format for serialization
    result_data = []
    for dest in nearby_destinations:
        # Get primary image or first image as fallback
        # For each destination, we try to find its primary image first
        primary_image = dest.images.filter(is_primary=True).first()
        if primary_image:
            # Use the primary image if available
            image_url = request.build_absolute_uri(primary_image.image.url)
        else:
            # Fall back to the first image or None if no images exist
            first_image = dest.images.first()
            image_url = request.build_absolute_uri(first_image.image.url) if first_image else None
        
        # Build destination data dictionary with all relevant fields
        # This data structure will be serialized to JSON in the response
        dest_data = {
            'id': dest.id,
            'name': dest.name,
            'slug': dest.slug,
            'city': dest.city,
            'country': dest.country,
            'short_description': dest.short_description,
            'rating': dest.rating,
            'price': dest.price,
            'latitude': dest.latitude,
            'longitude': dest.longitude,
            'distance': dest.distance,  # The calculated distance from query point
            'image_url': image_url,     # URL to the destination's image
        }
        
        result_data.append(dest_data)
    
    # Return a well-structured JSON response with success status and all results
    return JsonResponse({
        'success': True,                   # Indicates successful API call
        'count': len(nearby_destinations), # Number of destinations found
        'radius': radius,                  # The search radius used
        'origin': {'latitude': latitude, 'longitude': longitude},  # The search center point
        'destinations': result_data        # Array of destination data
    })
