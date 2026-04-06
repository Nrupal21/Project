# Tours App - Code Explainer

## Overview
The `tours` app manages the core tour booking functionality of the TravelGuide platform. It handles tour packages, categories, scheduling, itineraries, pricing, and customer reviews.

## File Structure

```
tours/
├── __init__.py           # Python package initialization
├── models.py            # Database models for tours and related entities
├── views.py             # View functions for tour management
├── urls.py              # URL routing for tours app
├── admin.py             # Django admin configuration
├── forms.py             # Forms for tour creation and management
└── serializers.py       # DRF serializers for API endpoints
```

## Core Components

### 1. Models (models.py)

The tours app implements a comprehensive tour management system with the following models:

#### TourCategory Model
**Purpose**: Organizes tours into categories (adventure, cultural, culinary, etc.).

**Key Features**:
- **Name and Slug**: Category name with URL-friendly slug
- **Description**: Detailed category description
- **Status Management**: Active/inactive flags for content control
- **Auto-slug Generation**: Automatically creates URL slug from name
- **Timestamps**: Creation and update tracking

**Key Functions**:
```python
def save(self, *args, **kwargs):
    """
    Override save to ensure slug is created from name if not provided.
    
    Automatically generates URL-friendly slug for SEO purposes.
    Ensures consistent URL structure across the application.
    
    Args:
        *args: Variable length argument list
        **kwargs: Arbitrary keyword arguments
    """

def __str__(self):
    """
    Return a string representation of the tour category.
    
    Used in admin interface, forms, and debugging.
    
    Returns:
        str: The name of the category
    """

def get_active_tours(self):
    """
    Get all active tours in this category.
    
    Returns only tours that are currently active and available for booking.
    
    Returns:
        QuerySet: Active tours in this category
    """
```

#### Tour Model
**Purpose**: Represents individual tour packages with comprehensive details.

**Key Features**:
- **Basic Information**: Name, slug, description, duration
- **Pricing**: Base price and optional discount pricing
- **Group Management**: Minimum and maximum group sizes
- **Destination Association**: Many-to-many with destinations
- **Location Details**: Start and end locations for tour
- **Tour Characteristics**: Difficulty level, languages offered
- **Inclusions/Exclusions**: JSON fields for flexible content
- **Status Management**: Featured and active flags

**Key Functions**:
```python
def save(self, *args, **kwargs):
    """
    Override save to ensure slug is created from name if not provided.
    
    Maintains URL consistency and SEO optimization.
    Generates unique slug from tour name.
    
    Args:
        *args: Variable length argument list
        **kwargs: Arbitrary keyword arguments
    """

def get_effective_price(self):
    """
    Get the current effective price for the tour.
    
    Returns discount price if available, otherwise regular price.
    Used for pricing display and booking calculations.
    
    Returns:
        Decimal: Current effective price
    """

def get_primary_image(self):
    """
    Get the primary image for the tour.
    
    Returns the image marked as primary, or the first image if none marked.
    Used for tour cards and list displays.
    
    Returns:
        TourImage: Primary image object or None
    """

def get_available_dates(self):
    """
    Get all available dates for this tour.
    
    Returns only future dates that are marked as available.
    Excludes fully booked dates.
    
    Returns:
        QuerySet: Available tour dates
    """

def calculate_average_rating(self):
    """
    Calculate average rating from approved reviews.
    
    Computes average rating from all approved customer reviews.
    Updates cached rating field for performance.
    
    Returns:
        float: Average rating (0-5 scale)
    """
```

#### TourImage Model
**Purpose**: Manages photo galleries for tours.

**Key Features**:
- **Multiple Images**: Each tour can have multiple photos
- **Primary Image**: One image designated as main representation
- **Image Metadata**: Captions for accessibility and context
- **Upload Management**: Organized file storage in tours/ directory

**Key Functions**:
```python
def save(self, *args, **kwargs):
    """
    Ensure only one primary image per tour.
    
    When an image is marked as primary, removes primary flag
    from other images of the same tour.
    
    Args:
        *args: Variable length argument list
        **kwargs: Arbitrary keyword arguments
    """

def __str__(self):
    """
    Return descriptive string for admin interface.
    
    Shows tour name and indicates if this is the primary image.
    
    Returns:
        str: Descriptive string for the image
    """
```

#### TourDate Model
**Purpose**: Manages scheduled tour dates and availability.

**Key Features**:
- **Date Range**: Start and end dates for tour instances
- **Dynamic Pricing**: Optional price override per date
- **Availability Management**: Available/unavailable status
- **Capacity Management**: Max participants and current booking count
- **Booking Tracking**: Tracks current participant count

**Key Functions**:
```python
def is_full(self):
    """
    Check if the tour date is fully booked.
    
    Compares current participants with maximum capacity.
    Used for availability checking in booking system.
    
    Returns:
        bool: True if tour is fully booked, False otherwise
    """

def get_available_spots(self):
    """
    Get number of available spots for this tour date.
    
    Calculates remaining capacity based on max participants
    and current bookings.
    
    Returns:
        int: Number of available spots (0 if unlimited capacity)
    """

def is_booking_open(self):
    """
    Check if booking is still open for this tour date.
    
    Considers availability status, capacity, and date proximity.
    
    Returns:
        bool: True if booking is open, False otherwise
    """

def __str__(self):
    """
    Return descriptive string for tour date.
    
    Includes tour name and date range for identification.
    
    Returns:
        str: Descriptive string for the tour date
    """
```

#### TourItinerary Model
**Purpose**: Manages day-by-day tour itineraries.

**Key Features**:
- **Daily Planning**: Day number and title for each day
- **Detailed Descriptions**: Rich content for daily activities
- **Attraction Integration**: Links to specific attractions to visit
- **Accommodation Info**: Daily accommodation details
- **Meal Planning**: Meal inclusion information per day

**Key Functions**:
```python
def get_attractions_for_day(self):
    """
    Get all attractions planned for this day.
    
    Returns attraction objects for mapping and detailed information.
    
    Returns:
        QuerySet: Attractions for this itinerary day
    """

def __str__(self):
    """
    Return descriptive string for itinerary item.
    
    Includes tour name and day number for identification.
    
    Returns:
        str: Descriptive string for the itinerary item
    """
```

#### TourReview Model
**Purpose**: Manages customer reviews and ratings for tours.

**Key Features**:
- **Rating System**: Numeric rating (1-5 scale)
- **Review Content**: Detailed customer comments
- **User Association**: Links to authenticated users
- **Moderation System**: Approval workflow for reviews
- **Timestamp Tracking**: Creation and update times

**Key Functions**:
```python
def is_recent(self):
    """
    Check if review was posted recently (within 30 days).
    
    Used for highlighting recent reviews and engagement metrics.
    
    Returns:
        bool: True if review is recent, False otherwise
    """

def get_rating_stars(self):
    """
    Get rating as star representation for templates.
    
    Converts numeric rating to star display format.
    
    Returns:
        dict: Star representation with filled and empty counts
    """

def __str__(self):
    """
    Return descriptive string for review.
    
    Includes tour name and rating for identification.
    
    Returns:
        str: Descriptive string for the review
    """
```

### 2. Views Structure (views.py)

#### Core View Functions
```python
def tour_list_view(request):
    """
    Display paginated list of active tours.
    
    Features:
    - Category-based filtering
    - Price range filtering
    - Duration filtering
    - Featured tours highlighting
    - Search functionality
    - Sorting by price, rating, duration
    
    Returns:
        HttpResponse: Rendered tour list page
    """

def tour_detail_view(request, slug):
    """
    Display detailed information for a specific tour.
    
    Features:
    - Complete tour information and pricing
    - Photo gallery with navigation
    - Detailed itinerary display
    - Available dates and booking
    - Customer reviews and ratings
    - Related tour suggestions
    
    Args:
        slug (str): URL slug for the tour
        
    Returns:
        HttpResponse: Rendered tour detail page
    """

def tour_booking_view(request, slug, date_id):
    """
    Handle tour booking process.
    
    Features:
    - Date selection and validation
    - Participant count selection
    - Price calculation with discounts
    - User authentication check
    - Booking form processing
    - Payment integration preparation
    
    Args:
        slug (str): URL slug for the tour
        date_id (int): ID of the tour date
        
    Returns:
        HttpResponse: Booking page or redirect to payment
    """

def tour_search_view(request):
    """
    Advanced search functionality for tours.
    
    Features:
    - Text search across name and description
    - Category-based filtering
    - Price range filtering
    - Duration filtering
    - Destination-based filtering
    - Date availability filtering
    
    Returns:
        HttpResponse: Search results page
    """
```

### 3. URL Configuration (urls.py)

**URL Patterns**:
```python
urlpatterns = [
    # Tour Listing and Search
    path('', views.tour_list_view, name='tour_list'),
    path('search/', views.tour_search_view, name='tour_search'),
    path('category/<slug:category_slug>/', views.tours_by_category_view, name='tours_by_category'),
    
    # Tour Details and Booking
    path('<slug:slug>/', views.tour_detail_view, name='tour_detail'),
    path('<slug:slug>/book/', views.tour_booking_view, name='tour_booking'),
    path('<slug:slug>/book/<int:date_id>/', views.tour_booking_with_date_view, name='tour_booking_date'),
    
    # Reviews and Ratings
    path('<slug:slug>/review/', views.add_tour_review_view, name='add_tour_review'),
    path('review/<int:review_id>/edit/', views.edit_tour_review_view, name='edit_tour_review'),
    
    # API Endpoints
    path('api/tours/', views.TourListAPIView.as_view(), name='api_tour_list'),
    path('api/tours/<slug:slug>/', views.TourDetailAPIView.as_view(), name='api_tour_detail'),
    path('api/tours/<slug:slug>/dates/', views.TourDatesAPIView.as_view(), name='api_tour_dates'),
    
    # Admin and Management
    path('admin/tours/create/', views.create_tour_view, name='create_tour'),
    path('admin/tours/<slug:slug>/edit/', views.edit_tour_view, name='edit_tour'),
]
```

## Key Features

### 1. Tour Management
- **Comprehensive Tour Data**: Complete tour information with flexible structure
- **Category Organization**: Logical grouping of tours by type
- **Rich Media Support**: Multiple images with primary image selection
- **Flexible Pricing**: Base pricing with optional date-specific overrides
- **Detailed Itineraries**: Day-by-day planning with attraction integration

### 2. Booking System
- **Date-based Booking**: Tours scheduled on specific dates
- **Capacity Management**: Maximum participant limits with booking tracking
- **Dynamic Pricing**: Date-specific pricing overrides
- **Availability Management**: Real-time availability checking
- **Group Size Management**: Minimum and maximum group size constraints

### 3. Review System
- **Customer Reviews**: User-generated reviews with ratings
- **Moderation Workflow**: Admin approval system for quality control
- **Rating Aggregation**: Automatic calculation of average ratings
- **Review Display**: Comprehensive review display with user information

### 4. Search and Discovery
- **Advanced Search**: Multi-criteria search across tour attributes
- **Category Filtering**: Browse tours by category
- **Price and Duration Filters**: Budget and time-based filtering
- **Destination Integration**: Filter tours by included destinations
- **Featured Tours**: Highlighting of premium or popular tours

### 5. Integration Features
- **Destination Integration**: Tours linked to multiple destinations
- **Attraction Integration**: Itineraries linked to specific attractions
- **User Integration**: User accounts for bookings and reviews
- **Booking Integration**: Seamless integration with booking system

## Database Relationships

```
TourCategory (1:Many) → Tour (1:Many) → TourDate
                         ↓ (1:Many)
                    TourImage, TourItinerary, TourReview
                         ↓ (Many:Many)
                    Destination, Attraction (via itinerary)
```

**Relationship Details**:
- **TourCategory to Tour**: One category contains many tours
- **Tour to TourDate**: One tour has multiple scheduled dates
- **Tour to TourImage**: One tour has multiple images
- **Tour to TourItinerary**: One tour has multiple itinerary days
- **Tour to TourReview**: One tour has multiple customer reviews
- **Tour to Destination**: Many-to-many relationship for multi-destination tours
- **TourItinerary to Attraction**: Many-to-many for daily attractions

## Integration Points

### 1. With Other Apps
- **Bookings App**: Tour booking and payment processing
- **Destinations App**: Tour destinations and attraction integration
- **Accounts App**: User authentication and review authorship
- **Reviews App**: Enhanced review system integration

### 2. External Services
- **Payment Gateways**: Integration with payment processing services
- **Email Services**: Booking confirmations and notifications
- **Map Services**: Location display for tour routes
- **Calendar Services**: Date selection and availability display

## Performance Considerations

### 1. Database Optimization
- **Strategic Indexes**: Indexes on frequently queried fields (slug, category, dates)
- **Query Optimization**: Use of select_related and prefetch_related
- **Caching Strategy**: Redis caching for popular tours and search results
- **Image Optimization**: Automatic image resizing and CDN integration

### 2. Search Performance
- **Database Indexes**: Full-text search indexes for tour content
- **Search Caching**: Cached search results for common queries
- **Pagination**: Efficient pagination for large result sets
- **Filter Optimization**: Optimized database queries for filtering

## Security Considerations

### 1. Data Validation
- **Input Sanitization**: All user inputs validated and sanitized
- **Price Validation**: Ensure valid pricing data and prevent manipulation
- **Date Validation**: Validate tour dates and prevent past bookings
- **Capacity Validation**: Prevent overbooking through proper validation

### 2. Access Control
- **Admin Functions**: Tour creation and editing restricted to admin users
- **Review Moderation**: Admin approval required for public reviews
- **Booking Authentication**: User authentication required for bookings
- **API Security**: Proper authentication and rate limiting for API endpoints

## Testing

The tours app includes comprehensive tests for:
- **Model Validation**: All model fields, relationships, and business logic
- **View Functionality**: All view functions including edge cases
- **Booking Logic**: Tour booking process and capacity management
- **Search Functionality**: Search and filtering features
- **Review System**: Review creation and moderation workflow

## Future Enhancements

Planned improvements include:
- **Dynamic Pricing**: AI-based dynamic pricing based on demand
- **Group Booking**: Special features for group bookings and discounts
- **Multi-language Support**: Itineraries and descriptions in multiple languages
- **Mobile App Integration**: Enhanced mobile booking experience
- **Virtual Tours**: Integration with VR/AR for virtual tour previews
- **Recommendation Engine**: AI-powered tour recommendations based on user preferences
