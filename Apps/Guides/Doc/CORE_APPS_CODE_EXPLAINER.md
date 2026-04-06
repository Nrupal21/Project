# Core Apps - Code Explainer

This document explains the remaining core Django apps in the TravelGuide project: bookings, itineraries, reviews, transportation, emergency, security, and core utilities.

## Bookings App

### Overview
The `bookings` app handles the entire booking process, payment processing, and booking management for tour reservations.

### File Structure
```
bookings/
├── __init__.py           # Python package initialization
├── models.py            # Booking and payment models
├── views.py             # Booking process views
├── urls.py              # URL routing for bookings
├── forms.py             # Booking and payment forms
└── admin.py             # Django admin configuration
```

### Key Models

#### Booking Model
**Purpose**: Represents a complete tour booking with all necessary details.

**Key Features**:
- **Reference System**: Unique booking reference numbers for tracking
- **User Association**: Links bookings to authenticated users
- **Tour Integration**: References specific tour and tour date
- **Participant Management**: Tracks number of participants
- **Status Workflow**: Complete booking lifecycle management
- **Contact Information**: Email and phone for booking correspondence
- **Special Requests**: Customer notes and special requirements
- **Price Tracking**: Total booking price with calculations

**Status Workflow**:
```python
STATUS_CHOICES = [
    ('pending', 'Pending'),        # Initial booking state
    ('confirmed', 'Confirmed'),    # Booking confirmed by system
    ('paid', 'Paid'),             # Payment completed
    ('cancelled', 'Cancelled'),    # Booking cancelled
    ('completed', 'Completed'),    # Tour completed
    ('refunded', 'Refunded'),     # Payment refunded
]
```

**Key Functions**:
```python
def generate_reference_number():
    """
    Generate unique booking reference number.
    
    Creates a unique identifier for booking tracking
    using UUID and timestamp components.
    
    Returns:
        str: Unique booking reference number
    """

def calculate_total_price(self):
    """
    Calculate total booking price including discounts.
    
    Considers base tour price, participant count,
    date-specific pricing, and any applicable discounts.
    
    Returns:
        Decimal: Total calculated price
    """

def can_be_cancelled(self):
    """
    Check if booking can be cancelled.
    
    Considers booking status, tour date proximity,
    and cancellation policies.
    
    Returns:
        bool: True if cancellation is allowed
    """

def send_confirmation_email(self):
    """
    Send booking confirmation email to customer.
    
    Sends detailed booking information including
    tour details, dates, and payment information.
    """
```

#### Payment Model
**Purpose**: Manages payment transactions for bookings.

**Key Features**:
- **Transaction Tracking**: Unique transaction IDs for payment tracking
- **Multiple Payment Methods**: Credit card, PayPal, bank transfer support
- **Payment Status**: Complete payment lifecycle management
- **Currency Support**: Multi-currency payment processing
- **Payment Data**: JSON field for gateway-specific data storage
- **Refund Management**: Built-in refund processing capabilities

**Key Functions**:
```python
def process_payment(self):
    """
    Process the payment and update related booking.
    
    Integrates with payment gateways to process transactions
    and updates booking status accordingly.
    
    Returns:
        bool: True if payment was processed successfully
    """

def refund(self):
    """
    Process a refund for this payment.
    
    Handles refund processing through payment gateways
    and updates booking and payment status.
    
    Returns:
        bool: True if refund was processed successfully
    """
```

## Itineraries App

### Overview
The `itineraries` app provides trip planning functionality, allowing users to create custom travel itineraries and day-by-day planning.

### Key Models

#### Itinerary Model
**Purpose**: Represents user-created travel itineraries.

**Key Features**:
- **User Association**: Personal itineraries for authenticated users
- **Trip Details**: Title, description, date ranges
- **Destination Integration**: Links to multiple destinations
- **Sharing Capabilities**: Public/private itinerary sharing
- **Collaboration**: Multi-user itinerary editing

#### ItineraryDay Model
**Purpose**: Represents individual days within an itinerary.

**Key Features**:
- **Daily Planning**: Date-specific activity planning
- **Activity Management**: Multiple activities per day
- **Location Tracking**: Geographic information for each day
- **Notes and Details**: Custom notes and special information

### Key Functions
```python
def calculate_duration(self):
    """
    Calculate total duration of the itinerary.
    
    Returns:
        int: Number of days in the itinerary
    """

def get_total_estimated_cost(self):
    """
    Calculate estimated total cost for the itinerary.
    
    Returns:
        Decimal: Estimated total cost
    """

def export_to_pdf(self):
    """
    Export itinerary to PDF format.
    
    Returns:
        bytes: PDF file content
    """
```

## Reviews App

### Overview
The `reviews` app manages customer reviews and ratings for tours, destinations, and services.

### Key Models

#### Review Model
**Purpose**: Stores customer reviews with ratings and content.

**Key Features**:
- **Multi-entity Reviews**: Reviews for tours, destinations, attractions
- **Rating System**: 5-star rating system with numeric values
- **Content Management**: Review text with moderation support
- **User Association**: Links reviews to authenticated users
- **Moderation Workflow**: Admin approval system

#### ReviewImage Model
**Purpose**: Manages user-uploaded images for reviews.

**Key Features**:
- **Image Uploads**: Customer photos with reviews
- **Image Validation**: File type and size validation
- **Caption Support**: Image descriptions and context

### Key Functions
```python
def calculate_average_rating(entity):
    """
    Calculate average rating for any entity (tour, destination, etc.).
    
    Args:
        entity: The object being reviewed
        
    Returns:
        float: Average rating (0-5 scale)
    """

def is_helpful(self):
    """
    Check if review has been marked as helpful by users.
    
    Returns:
        bool: True if review is considered helpful
    """
```

## Transportation App

### Overview
The `transportation` app manages transportation options, routes, and booking integration for travel logistics.

### Key Models

#### TransportationType Model
**Purpose**: Defines different types of transportation (bus, train, flight, etc.).

#### Transportation Model
**Purpose**: Represents specific transportation options.

**Key Features**:
- **Route Management**: Origin and destination handling
- **Schedule Management**: Departure and arrival times
- **Pricing Information**: Dynamic pricing for different dates
- **Capacity Management**: Seat availability tracking

### Key Functions
```python
def find_routes(origin, destination, date):
    """
    Find available transportation routes.
    
    Args:
        origin: Starting location
        destination: End location
        date: Travel date
        
    Returns:
        QuerySet: Available transportation options
    """

def calculate_travel_time(self):
    """
    Calculate total travel time for the route.
    
    Returns:
        timedelta: Duration of travel
    """
```

## Emergency App

### Overview
The `emergency` app provides safety features, emergency contacts, and risk assessment for travel destinations.

### Key Models

#### EmergencyContact Model
**Purpose**: Stores emergency contact information for destinations.

**Key Features**:
- **Contact Types**: Police, medical, embassy, etc.
- **Location-specific**: Contacts organized by destination
- **Multiple Contact Methods**: Phone, email, address information

#### SafetyAlert Model
**Purpose**: Manages safety alerts and warnings for destinations.

**Key Features**:
- **Alert Types**: Various categories of safety information
- **Severity Levels**: Different urgency levels for alerts
- **Geographic Targeting**: Location-specific alerts

### Key Functions
```python
def get_emergency_contacts(destination):
    """
    Get all emergency contacts for a destination.
    
    Args:
        destination: Destination object
        
    Returns:
        QuerySet: Emergency contacts for the destination
    """

def assess_safety_level(destination):
    """
    Assess overall safety level for a destination.
    
    Args:
        destination: Destination object
        
    Returns:
        str: Safety level (low, medium, high risk)
    """
```

## Security App

### Overview
The `security` app implements advanced security features including two-factor authentication (2FA) and security auditing.

### Key Models

#### TwoFactorAuth Model
**Purpose**: Manages 2FA settings for user accounts.

**Key Features**:
- **TOTP Support**: Time-based one-time passwords
- **Backup Codes**: Recovery codes for 2FA
- **Device Management**: Trusted device tracking

#### SecurityLog Model
**Purpose**: Logs security-related events and actions.

**Key Features**:
- **Action Logging**: Detailed security event tracking
- **IP Address Tracking**: Source IP for security events
- **User Association**: Links security events to users

### Key Functions
```python
def generate_backup_codes(user):
    """
    Generate backup codes for 2FA recovery.
    
    Args:
        user: User object
        
    Returns:
        list: Generated backup codes
    """

def verify_totp_token(user, token):
    """
    Verify TOTP token for 2FA authentication.
    
    Args:
        user: User object
        token: TOTP token to verify
        
    Returns:
        bool: True if token is valid
    """
```

## Core App

### Overview
The `core` app provides shared utilities, context processors, and common functionality used across the entire application.

### Key Components

#### Context Processors (context_processors.py)
**Purpose**: Provides global template context variables.

**Key Functions**:
```python
def site_settings(request):
    """
    Add site-wide settings to template context.
    
    Provides global configuration variables
    available in all templates.
    
    Args:
        request: HTTP request object
        
    Returns:
        dict: Context variables for templates
    """

def user_data(request):
    """
    Add user-specific data to template context.
    
    Provides user profile information and
    preferences for template rendering.
    
    Args:
        request: HTTP request object
        
    Returns:
        dict: User-specific context variables
    """
```

#### Geographic Utilities (geoutils.py)
**Purpose**: Provides geographic calculation utilities.

**Key Functions**:
```python
def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two geographic points.
    
    Uses Haversine formula for accurate distance calculation.
    
    Args:
        lat1, lon1: Coordinates of first point
        lat2, lon2: Coordinates of second point
        
    Returns:
        float: Distance in kilometers
    """

def find_nearby_locations(latitude, longitude, radius_km):
    """
    Find locations within specified radius.
    
    Args:
        latitude: Center point latitude
        longitude: Center point longitude
        radius_km: Search radius in kilometers
        
    Returns:
        QuerySet: Locations within radius
    """

def geocode_address(address):
    """
    Convert address to geographic coordinates.
    
    Args:
        address: Street address string
        
    Returns:
        tuple: (latitude, longitude) or None if not found
    """
```

## Integration and Data Flow

### Booking Process Flow
1. **Tour Selection**: User selects tour and date from tours app
2. **Booking Creation**: Booking record created in bookings app
3. **Payment Processing**: Payment handled through payments system
4. **Confirmation**: Email notifications and booking confirmation
5. **Itinerary Integration**: Optional itinerary creation for booked tours

### Review System Flow
1. **Tour Completion**: After tour completion, review invitation sent
2. **Review Creation**: User creates review with rating and content
3. **Moderation**: Admin review and approval process
4. **Display**: Approved reviews displayed on tour pages
5. **Rating Aggregation**: Average ratings calculated and cached

### Security Integration
1. **Authentication**: User login with optional 2FA
2. **Security Logging**: All critical actions logged
3. **Access Control**: Permission-based access to features
4. **Data Protection**: Encryption and secure data handling

## Performance Optimizations

### Database Optimizations
- **Strategic Indexes**: Key fields indexed for query performance
- **Query Optimization**: Efficient database queries with proper joins
- **Caching Strategy**: Redis caching for frequently accessed data
- **Connection Pooling**: Efficient database connection management

### Application Performance
- **Template Caching**: Cached template rendering for static content
- **Static File Optimization**: CDN integration for static assets
- **Image Optimization**: Automatic image resizing and compression
- **Code Optimization**: Efficient algorithms and data structures

## Security Measures

### Data Security
- **Input Validation**: Comprehensive validation for all user inputs
- **SQL Injection Prevention**: Django ORM prevents SQL injection
- **XSS Protection**: Template auto-escaping and CSP headers
- **CSRF Protection**: Cross-site request forgery protection

### Authentication Security
- **Password Security**: Strong password requirements and hashing
- **Session Security**: Secure session configuration and management
- **Two-Factor Authentication**: Optional 2FA for enhanced security
- **Rate Limiting**: Protection against brute force attacks

## Testing Strategy

Each app includes comprehensive test coverage:
- **Unit Tests**: Model and utility function testing
- **Integration Tests**: Cross-app functionality testing
- **API Tests**: REST API endpoint testing
- **Security Tests**: Authentication and authorization testing
- **Performance Tests**: Load testing for critical paths

## Deployment Considerations

### Production Requirements
- **Database Configuration**: PostgreSQL with proper indexing
- **Cache Configuration**: Redis for session and data caching
- **Static File Serving**: CDN integration for static assets
- **Email Configuration**: SMTP setup for notifications
- **Payment Gateway**: Production payment processor configuration

### Monitoring and Logging
- **Application Monitoring**: Performance and error monitoring
- **Security Monitoring**: Security event tracking and alerting
- **Database Monitoring**: Query performance and optimization
- **User Activity Tracking**: Analytics and usage patterns

This comprehensive code structure provides a robust foundation for a travel guide and booking platform with extensive functionality and security measures.
