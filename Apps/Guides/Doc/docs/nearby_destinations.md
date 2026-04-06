# Nearby Destinations Feature Documentation

## Overview

The Nearby Destinations feature allows users to find travel destinations within a specified radius of their current location. This feature is implemented using the Haversine formula, which calculates the great-circle distance between two points on a sphere given their longitudes and latitudes.

## Technical Implementation

### Core Components

1. **API Endpoint**: `/api/nearby/`
   - Implemented in `nearby_destinations.py`
   - Uses the Django view decorator `@require_http_methods(["GET"])`

2. **URL Configuration**: 
   - Registered in `destinations/urls.py`
   - Path: `path('api/nearby/', nearby_destinations, name='nearby_destinations')`

3. **Mathematical Foundation**: 
   - Uses the Haversine formula for calculating distances on Earth's surface
   - Accounts for Earth's curvature when determining proximity

## Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `lat` | float | Yes | N/A | Latitude of the user's location |
| `lng` | float | Yes | N/A | Longitude of the user's location |
| `radius` | float | No | 10.0 | Search radius in kilometers |
| `limit` | int | No | 6 | Maximum number of results to return |

## Haversine Formula Implementation

The Haversine formula calculates the shortest distance between two points on a sphere:

```
d = 2r * arcsin(sqrt(sin²((φ₂-φ₁)/2) + cos(φ₁)cos(φ₂)sin²((λ₂-λ₁)/2)))
```

Where:
- φ is latitude in radians
- λ is longitude in radians 
- r is Earth's radius (approximately 6371 km)

Our implementation:
1. Converts latitude/longitude from degrees to radians
2. Calculates differences in coordinates
3. Applies the formula to get distance in kilometers
4. Filters destinations within the specified radius
5. Sorts by proximity (closest first)

## Response Format

```json
{
    "success": true,
    "count": <number_of_results>,
    "radius": <search_radius_used>,
    "origin": {
        "latitude": <user_latitude>,
        "longitude": <user_longitude>
    },
    "destinations": [
        {
            "id": <destination_id>,
            "name": <destination_name>,
            "slug": <destination_slug>,
            "city": <city_name>,
            "country": <country_name>,
            "short_description": <brief_description>,
            "rating": <average_rating>,
            "price": <average_price>,
            "latitude": <destination_latitude>,
            "longitude": <destination_longitude>,
            "distance": <distance_from_user_in_km>,
            "image_url": <url_to_primary_image>
        },
        // Additional destinations...
    ]
}
```

## Usage Examples

### Find destinations within 5km of a location

```
GET /api/nearby/?lat=37.7749&lng=-122.4194&radius=5
```

### Find the 10 closest destinations to a location

```
GET /api/nearby/?lat=37.7749&lng=-122.4194&limit=10
```

## Potential Optimizations

1. **Spatial Indexing**: For large datasets, implementing PostgreSQL's PostGIS extension would improve performance by using spatial indexes.

2. **Bounding Box Pre-filtering**: Before applying the exact Haversine formula, use a bounding box filter to narrow down candidate locations.

3. **Caching**: Cache commonly requested location searches to improve response time.

4. **Pagination**: For very large result sets, implement cursor-based pagination.

## Related Components

- **AttractionViewSet**: Can be extended to offer similar proximity searches for attractions
- **NearbyDestinationSerializer**: Handles serialization of destination data with distance field
