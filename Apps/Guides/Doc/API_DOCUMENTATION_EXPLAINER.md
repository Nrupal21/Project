# API Documentation - Code Explainer

## Overview
This document provides comprehensive documentation for all REST API endpoints in the TravelGuide project. The API is built using Django REST Framework and provides full CRUD operations for all major entities.

## API Architecture

### Base Configuration
```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}
```

### Authentication System
The API supports multiple authentication methods:
- **Session Authentication**: For web browser access
- **Token Authentication**: For mobile apps and external integrations
- **Basic Authentication**: For development and testing

## Core API Endpoints

### 1. Authentication Endpoints

#### User Registration
```http
POST /api/auth/register/
Content-Type: application/json

{
    "username": "string",
    "email": "string",
    "password": "string",
    "first_name": "string",
    "last_name": "string"
}
```

**Response**:
```json
{
    "user": {
        "id": 1,
        "username": "newuser",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe"
    },
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
    "message": "Registration successful. Please check your email for verification."
}
```

#### User Login
```http
POST /api/auth/login/
Content-Type: application/json

{
    "username": "string",
    "password": "string"
}
```

**Response**:
```json
{
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
    "user": {
        "id": 1,
        "username": "user",
        "email": "user@example.com",
        "profile": {
            "profile_picture": "url",
            "bio": "string"
        }
    }
}
```

### 2. Destinations API

#### List Destinations
```http
GET /api/destinations/
```

**Query Parameters**:
- `region`: Filter by region ID
- `search`: Text search across name and description
- `min_price`: Minimum price filter
- `max_price`: Maximum price filter
- `min_rating`: Minimum rating filter
- `is_featured`: Filter featured destinations
- `ordering`: Sort by field (`name`, `price`, `rating`, `-created_at`)

**Response**:
```json
{
    "count": 150,
    "next": "http://api.example.com/destinations/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Tokyo",
            "slug": "tokyo",
            "region": {
                "id": 1,
                "name": "Japan",
                "slug": "japan"
            },
            "short_description": "Vibrant capital city of Japan",
            "description": "Full description...",
            "latitude": "35.676762",
            "longitude": "139.650311",
            "city": "Tokyo",
            "country": "Japan",
            "price": "1200.00",
            "rating": "4.8",
            "is_featured": true,
            "is_active": true,
            "images": [
                {
                    "id": 1,
                    "image": "http://example.com/media/destinations/tokyo1.jpg",
                    "caption": "Tokyo skyline",
                    "is_primary": true
                }
            ],
            "attractions_count": 15,
            "tours_count": 8,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-15T12:30:00Z"
        }
    ]
}
```

#### Get Destination Detail
```http
GET /api/destinations/{id}/
```

**Response**:
```json
{
    "id": 1,
    "name": "Tokyo",
    "slug": "tokyo",
    "region": {
        "id": 1,
        "name": "Japan",
        "slug": "japan",
        "country": "Japan"
    },
    "short_description": "Vibrant capital city of Japan",
    "description": "Tokyo is the bustling capital of Japan...",
    "latitude": "35.676762",
    "longitude": "139.650311",
    "city": "Tokyo",
    "country": "Japan",
    "price": "1200.00",
    "rating": "4.8",
    "views": 15420,
    "is_featured": true,
    "is_active": true,
    "images": [
        {
            "id": 1,
            "image": "http://example.com/media/destinations/tokyo1.jpg",
            "caption": "Tokyo skyline at night",
            "is_primary": true
        },
        {
            "id": 2,
            "image": "http://example.com/media/destinations/tokyo2.jpg",
            "caption": "Traditional temple in Tokyo",
            "is_primary": false
        }
    ],
    "attractions": [
        {
            "id": 1,
            "name": "Tokyo Tower",
            "slug": "tokyo-tower",
            "category": "landmark",
            "is_featured": true
        }
    ],
    "nearby_destinations": [
        {
            "id": 2,
            "name": "Osaka",
            "distance_km": 400,
            "rating": "4.6"
        }
    ],
    "weather_info": {
        "current_temp": "22°C",
        "condition": "Sunny",
        "best_months": ["March", "April", "May", "October", "November"]
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-15T12:30:00Z"
}
```

### 3. Tours API

#### List Tours
```http
GET /api/tours/
```

**Query Parameters**:
- `category`: Filter by tour category ID
- `destination`: Filter by destination ID
- `min_price`: Minimum price filter
- `max_price`: Maximum price filter
- `duration_min`: Minimum duration in days
- `duration_max`: Maximum duration in days
- `difficulty`: Filter by difficulty level
- `is_featured`: Filter featured tours
- `available_from`: Filter tours available from date (YYYY-MM-DD)

**Response**:
```json
{
    "count": 75,
    "next": "http://api.example.com/tours/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Tokyo Cultural Explorer",
            "slug": "tokyo-cultural-explorer",
            "category": {
                "id": 1,
                "name": "Cultural",
                "slug": "cultural"
            },
            "short_description": "Discover traditional and modern Tokyo",
            "duration_days": 7,
            "group_size_min": 2,
            "group_size_max": 12,
            "price": "2500.00",
            "discount_price": "2250.00",
            "destinations": [
                {
                    "id": 1,
                    "name": "Tokyo",
                    "slug": "tokyo"
                }
            ],
            "difficulty_level": "easy",
            "languages": ["English", "Japanese"],
            "is_featured": true,
            "is_active": true,
            "primary_image": {
                "image": "http://example.com/media/tours/tokyo-cultural.jpg",
                "caption": "Traditional Tokyo temple"
            },
            "rating": "4.9",
            "review_count": 145,
            "next_available_date": "2024-03-15",
            "created_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

#### Get Tour Detail
```http
GET /api/tours/{id}/
```

**Response**:
```json
{
    "id": 1,
    "name": "Tokyo Cultural Explorer",
    "slug": "tokyo-cultural-explorer",
    "category": {
        "id": 1,
        "name": "Cultural",
        "slug": "cultural",
        "description": "Experience local culture and traditions"
    },
    "short_description": "Discover traditional and modern Tokyo",
    "description": "This comprehensive 7-day tour takes you through...",
    "duration_days": 7,
    "group_size_min": 2,
    "group_size_max": 12,
    "price": "2500.00",
    "discount_price": "2250.00",
    "destinations": [
        {
            "id": 1,
            "name": "Tokyo",
            "slug": "tokyo",
            "latitude": "35.676762",
            "longitude": "139.650311"
        }
    ],
    "start_location": "Tokyo Station",
    "end_location": "Tokyo Station",
    "difficulty_level": "easy",
    "languages": ["English", "Japanese"],
    "inclusions": [
        "7 nights accommodation",
        "Daily breakfast",
        "Professional guide",
        "Transportation",
        "Entrance fees"
    ],
    "exclusions": [
        "International flights",
        "Lunch and dinner",
        "Personal expenses",
        "Travel insurance"
    ],
    "is_featured": true,
    "is_active": true,
    "images": [
        {
            "id": 1,
            "image": "http://example.com/media/tours/tokyo-cultural-1.jpg",
            "caption": "Traditional Tokyo temple",
            "is_primary": true
        }
    ],
    "itinerary": [
        {
            "day": 1,
            "title": "Arrival and Traditional Tokyo",
            "description": "Arrive in Tokyo and explore traditional neighborhoods...",
            "attractions": [
                {
                    "id": 1,
                    "name": "Senso-ji Temple",
                    "slug": "senso-ji-temple"
                }
            ],
            "accommodation": "Traditional Ryokan",
            "meals": "Dinner included"
        }
    ],
    "available_dates": [
        {
            "id": 1,
            "start_date": "2024-03-15",
            "end_date": "2024-03-22",
            "price": "2250.00",
            "is_available": true,
            "max_participants": 12,
            "current_participants": 8,
            "spots_remaining": 4
        }
    ],
    "reviews": {
        "average_rating": "4.9",
        "total_reviews": 145,
        "recent_reviews": [
            {
                "id": 1,
                "user": "John D.",
                "rating": 5,
                "comment": "Amazing experience! Highly recommended.",
                "created_at": "2024-01-20T10:30:00Z"
            }
        ]
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-15T12:30:00Z"
}
```

### 4. Bookings API

#### Create Booking
```http
POST /api/bookings/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
Content-Type: application/json

{
    "tour_date": 1,
    "participants": 2,
    "contact_email": "user@example.com",
    "contact_phone": "+1-555-123-4567",
    "special_requests": "Vegetarian meals please",
    "emergency_contact_name": "Jane Doe",
    "emergency_contact_phone": "+1-555-987-6543"
}
```

**Response**:
```json
{
    "id": 1,
    "reference_number": "TG8A9B2C3D",
    "tour": {
        "id": 1,
        "name": "Tokyo Cultural Explorer",
        "duration_days": 7
    },
    "tour_date": {
        "id": 1,
        "start_date": "2024-03-15",
        "end_date": "2024-03-22"
    },
    "participants": 2,
    "total_price": "4500.00",
    "status": "pending",
    "contact_email": "user@example.com",
    "contact_phone": "+1-555-123-4567",
    "special_requests": "Vegetarian meals please",
    "emergency_contact_name": "Jane Doe",
    "emergency_contact_phone": "+1-555-987-6543",
    "created_at": "2024-02-01T14:30:00Z",
    "payment_due_date": "2024-02-08T14:30:00Z"
}
```

#### List User Bookings
```http
GET /api/bookings/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

**Query Parameters**:
- `status`: Filter by booking status
- `tour`: Filter by tour ID
- `date_from`: Bookings from date
- `date_to`: Bookings until date

### 5. Reviews API

#### Create Review
```http
POST /api/reviews/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
Content-Type: application/json

{
    "tour": 1,
    "rating": 5,
    "comment": "Absolutely fantastic tour! The guide was knowledgeable and friendly.",
    "images": [
        "base64_encoded_image_data"
    ]
}
```

**Response**:
```json
{
    "id": 1,
    "tour": {
        "id": 1,
        "name": "Tokyo Cultural Explorer"
    },
    "user": {
        "id": 1,
        "username": "traveler123",
        "profile_picture": "http://example.com/media/profiles/user1.jpg"
    },
    "rating": 5,
    "comment": "Absolutely fantastic tour! The guide was knowledgeable and friendly.",
    "images": [
        {
            "id": 1,
            "image": "http://example.com/media/reviews/review1.jpg",
            "caption": "Beautiful temple visit"
        }
    ],
    "is_approved": false,
    "created_at": "2024-02-01T16:45:00Z",
    "updated_at": "2024-02-01T16:45:00Z"
}
```

## API Error Handling

### Standard Error Response Format
```json
{
    "error": "error_code",
    "message": "Human readable error message",
    "details": {
        "field_name": ["Specific field error messages"]
    },
    "timestamp": "2024-02-01T12:00:00Z"
}
```

### Common Error Codes

#### Authentication Errors
- **401 Unauthorized**: Invalid or missing authentication token
- **403 Forbidden**: User lacks permission for requested action

#### Validation Errors
- **400 Bad Request**: Invalid input data or missing required fields
- **422 Unprocessable Entity**: Valid format but business logic validation failed

#### Resource Errors
- **404 Not Found**: Requested resource doesn't exist
- **409 Conflict**: Resource already exists or conflicts with current state

#### Server Errors
- **500 Internal Server Error**: Unexpected server error
- **503 Service Unavailable**: Service temporarily unavailable

## API Rate Limiting

### Rate Limit Configuration
```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'burst': '60/min',
        'sustained': '1000/day'
    }
}
```

### Rate Limit Headers
All API responses include rate limiting headers:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1643723400
```

## API Versioning

### URL-based Versioning
```http
GET /api/v1/destinations/
GET /api/v2/destinations/
```

### Header-based Versioning
```http
GET /api/destinations/
Accept: application/json; version=2.0
```

## API Testing

### Using cURL
```bash
# Get destinations
curl -H "Authorization: Token your_token_here" \
     http://localhost:8000/api/destinations/

# Create booking
curl -X POST \
     -H "Authorization: Token your_token_here" \
     -H "Content-Type: application/json" \
     -d '{"tour_date": 1, "participants": 2}' \
     http://localhost:8000/api/bookings/
```

### Using Python Requests
```python
import requests

# Authentication
headers = {'Authorization': 'Token your_token_here'}

# Get destinations
response = requests.get('http://localhost:8000/api/destinations/', headers=headers)
destinations = response.json()

# Create booking
booking_data = {
    'tour_date': 1,
    'participants': 2,
    'contact_email': 'user@example.com'
}
response = requests.post(
    'http://localhost:8000/api/bookings/',
    json=booking_data,
    headers=headers
)
booking = response.json()
```

## API Documentation Tools

### Django REST Framework Browsable API
Access at: `http://localhost:8000/api/`
- Interactive API browser
- Built-in authentication
- Form-based testing

### Swagger/OpenAPI Documentation
Access at: `http://localhost:8000/api/docs/`
- Complete API specification
- Interactive testing interface
- Code generation support

This comprehensive API documentation provides all necessary information for integrating with the TravelGuide platform, including authentication, data formats, error handling, and testing procedures.
