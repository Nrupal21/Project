"""
Tours views module.

This module contains views for handling web interface and API endpoints related to tours,
tour categories, and tour booking functionality.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, Http404
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Avg, Count, Q, Prefetch
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from rest_framework import viewsets
from rest_framework.decorators import action
import logging
from datetime import date

# Forms imports commented out during maintenance mode
# Will be restored when database schema is updated and forms module is ready
# from .forms import TourBookingForm, TourReviewForm
# Models imports updated for maintenance mode
# TourBooking model to be added in the schema updates
from .models import Tour, TourCategory, TourDate, TourImage, TourItinerary, TourReview  # TourBooking removed temporarily
from destinations.models import Destination
# Temporarily commented out during maintenance mode
# from users.models import Profile

# Set up logger
logger = logging.getLogger(__name__)

class TourCategoryView(DetailView):
    """
    Display details for a single tour category with its associated tours.
    
    This view shows all active tours in the selected category with pagination,
    sorting options, and related tour information.
    
    CURRENTLY IN MAINTENANCE MODE
    """
    model = TourCategory
    template_name = 'tours/category_detail.html'
    context_object_name = 'category'
    slug_url_kwarg = 'slug'
    
    def get(self, request, *args, **kwargs):
        # MAINTENANCE MODE: Display maintenance message
        context = {
            'maintenance_mode': True,
            'maintenance_message': 'Tours functionality is temporarily disabled while we update our database.',
            'expected_completion': 'Please check back later.'
        }
        return render(request, self.template_name, context)
    
    # Original code commented out
    # try:
    #     # Get base queryset of active tours with related data
    #     tours = Tour.objects.filter(is_active=True).select_related('category', 'destination')
    #     
    #     # Apply filters from query parameters
    #     category_slug = request.GET.get('category')
    #     search_query = request.GET.get('search')
    #     min_price = request.GET.get('min_price')
    #     max_price = request.GET.get('max_price')
    #     min_duration = request.GET.get('min_duration')
    #     max_duration = request.GET.get('max_duration')
    #     featured_only = request.GET.get('featured') == '1'
    #     sort_by = request.GET.get('sort', 'name')
    #     
    #     # Apply category filter
    #     if category_slug:
    #         tours = tours.filter(category__slug=category_slug, category__is_active=True)
    #     
    #     # Apply search query
    #     if search_query:
    #         tours = tours.filter(
    #             Q(name__icontains=search_query) |
    #             Q(short_description__icontains=search_query) |
    #             Q(description__icontains=search_query) |
    #             Q(start_location__icontains=search_query) |
    #             Q(end_location__icontains=search_query) |
    #             Q(destination__name__icontains=search_query)
    #         )
    #     
    #     # Apply price range filter
    #     if min_price:
    #         try:
    #             tours = tours.filter(price__gte=float(min_price))
    #         except (ValueError, TypeError):
    #             pass
    #             
    #     if max_price:
    #         try:
    #             tours = tours.filter(price__lte=float(max_price))
    #         except (ValueError, TypeError):
    #             pass
    #     
    #     # Apply duration filters
    #     if min_duration:
    #         try:
    #             tours = tours.filter(duration_days__gte=int(min_duration))
    #         except (ValueError, TypeError):
    #             pass
    #             
    #     if max_duration:
    #         try:
    #             tours = tours.filter(duration_days__lte=int(max_duration))
    #         except (ValueError, TypeError):
    #             pass
    #     
    #     # Apply featured filter
    #     if featured_only:
    #         tours = tours.filter(is_featured=True)
    #     
    #     # Apply sorting
    #     if sort_by == 'price':
    #         tours = tours.order_by('price')
    #     elif sort_by == 'price_desc':
    #         tours = tours.order_by('-price')
    #     elif sort_by == 'duration':
    #         tours = tours.order_by('duration_days')
    #     elif sort_by == 'duration_desc':
    #         tours = tours.order_by('-duration_days')
    #     elif sort_by == 'rating':
    #         tours = tours.annotate(
    #             avg_rating=Avg('reviews__rating')
    #         ).order_by('-avg_rating')
    #     else:  # Default sort by name
    #         tours = tours.order_by('name')
    #     
    #     # Prefetch related data for better performance
    #     tours = tours.prefetch_related(
    #         Prefetch(
    #             'images',
    #             queryset=TourImage.objects.filter(is_primary=True),
    #             to_attr='primary_images'
    #         ),
    #         'destinations',
    #         'category'
    #     )
    #     
    #     # Get all active tour categories for the filter
    #     categories = TourCategory.objects.filter(is_active=True).order_by('name')
    #     
    #     # Get featured tours for the sidebar
    #     featured_tours = Tour.objects.filter(
    #         is_active=True,
    #         is_featured=True
    #     ).prefetch_related(
    #         Prefetch(
    #             'images',
    #             queryset=TourImage.objects.filter(is_primary=True),
    #             to_attr='primary_images'
    #         )
    #     ).order_by('?')[:3]  # Random 3 featured tours
    #     
    #     # Pagination
    #     page = request.GET.get('page', 1)
    #     paginator = Paginator(tours, 12)  # Show 12 tours per page
    #     
    #     try:
    #         tours_page = paginator.page(page)
    #     except PageNotAnInteger:
    #         tours_page = paginator.page(1)
    #     except EmptyPage:
    #         tours_page = paginator.page(paginator.num_pages)
    #     
    #     context = {
    #         'tours': tours_page,
    #         'categories': categories,
    #         'featured_tours': featured_tours,
    #         'current_category': category_slug,
    #         'search_query': search_query or '',
    #         'min_price': min_price or '',
    #         'max_price': max_price or '',
    #         'min_duration': min_duration or '',
    #         'max_duration': max_duration or '',
    #         'featured_only': featured_only,
    #         'sort_by': sort_by,
    #     }
    #     
    #     return render(request, self.template_name, context)
    #     
    # except Exception as e:
    #     logger.error(f"Error in tour_list_view: {str(e)}", exc_info=True)
    #     context = {
    #         'error': 'An error occurred while loading tours. Please try again later.'
    #     }
    #     return render(request, self.template_name, context, status=500)
    
    # # Apply filters from query parameters
    # category_id = request.GET.get('category')
    # search_query = request.GET.get('search')
    # min_price = request.GET.get('min_price')
    # max_price = request.GET.get('max_price')
    # min_duration = request.GET.get('min_duration')
    # max_duration = request.GET.get('max_duration')
    # featured_only = request.GET.get('featured') == '1'
    # sort_by = request.GET.get('sort', 'name')
    # 
    # # Filter by category if specified
    # if category_id:
    #     tours = tours.filter(category_id=category_id)
    # 
    # # Filter by search query if provided
    # if search_query:
    #     tours = tours.filter(
    #         Q(name__icontains=search_query) |
    #         Q(short_description__icontains=search_query) |
    #         Q(description__icontains=search_query) |
    #         Q(start_location__icontains=search_query) |
    #         Q(end_location__icontains=search_query)
    #     )
    # 
    # # Filter by price range if provided
    # if min_price:
    #     tours = tours.filter(price__gte=min_price)
    # if max_price:
    #     tours = tours.filter(price__lte=max_price)
    # 
    # # Filter by duration range if provided
    # if min_duration:
    #     tours = tours.filter(duration_days__gte=min_duration)
    # if max_duration:
    #     tours = tours.filter(duration_days__lte=max_duration)
    # 
    # # Filter featured tours if requested
    # if featured_only:
    #     tours = tours.filter(is_featured=True)
    # 
    # # Apply sorting
    # if sort_by == 'price_asc':
    #     tours = tours.order_by('price')
    # elif sort_by == 'price_desc':
    #     tours = tours.order_by('-price')
    # elif sort_by == 'duration':
    #     tours = tours.order_by('duration_days')
    # elif sort_by == 'popularity':
    #     # Using number of reviews as a proxy for popularity
    #     tours = tours.annotate(review_count=Count('reviews')).order_by('-review_count')
    # else:
    #     tours = tours.order_by('name')
    # 
    # # Get all tour categories for the filter dropdown
    # categories = TourCategory.objects.filter(is_active=True).order_by('name')
    # 
    # # Pagination
    # paginator = Paginator(tours, 9)  # Show 9 tours per page
    # page_number = request.GET.get('page', 1)
    # page_obj = paginator.get_page(page_number)
    # 
    # context = {
    #     'tours': page_obj,
    #     'categories': categories,
    #     'current_category': category_id,
    #     'search_query': search_query or '',
    #     'min_price': min_price or '',
    #     'max_price': max_price or '',
    #     'min_duration': min_duration or '',
    #     'max_duration': max_duration or '',
    #     'featured_only': featured_only,
    #     'sort_by': sort_by,
    # }
    # 
    # return render(request, self.template_name, context)


def tour_list_view(request):
    """
    Render the tours list page with filtering and pagination.
    
    This view displays all active tours with optional filtering by
    category, search term, price range, duration, and featured status.
    Currently in maintenance mode and displays only a message.
    
    When active, this function will display a paginated list of tours with
    various filter options including category, price range, duration,
    and featured status. Users can search for tours and sort results.
    
    Args:
        request (HttpRequest): The HTTP request object containing
            query parameters for filtering and pagination
        
    Returns:
        HttpResponse: Rendered template with maintenance message
    """
    # MAINTENANCE MODE: Display maintenance message
    # This function would normally display a filterable list of tours
    # Currently disabled during database schema updates
    context = {
        'maintenance_mode': True,
        'maintenance_message': 'Tours functionality is temporarily disabled while we update our database schema.',
        'expected_completion': 'Please check back later.'
    }
    return render(request, 'tours/tour_list.html', context)

def tour_detail_view(request, slug):
    """
    Render the tour detail page with comprehensive tour information.
    
    This view displays detailed information about a specific tour including:
    - Tour details and description
    - Itinerary with daily activities
    - Reviews and ratings
    - Available dates and booking options
    - Related tours
    
    When active, this function retrieves a tour by its slug and fetches all
    related data including images, itinerary, available dates, and reviews.
    It also calculates average ratings, finds related tours based on destination
    and category, and presents booking options to the user.
    
    Args:
        request: The HTTP request object
        slug: The unique URL slug of the tour to display
        
    Returns:
        HttpResponse: Rendered template with tour details or maintenance message
    """
    # MAINTENANCE MODE: Display maintenance message
    context = {
        'maintenance_mode': True,
        'maintenance_message': 'Tour details are temporarily unavailable while we update our database schema.',
        'expected_completion': 'Please check back later.'
    }
    return render(request, 'tours/tour_detail.html', context)



# Maintenance mode: Added decorator to indicate maintenance mode
@login_required
def tour_booking_view(request, slug):
    """
    Handle tour booking form and submission.
    
    This view displays a booking form for a tour and processes
    the form submission to create a booking. It requires user authentication.
    
    When active, this function will:
    - Display an available dates calendar for the selected tour
    - Show pricing options based on selected dates and number of travelers
    - Process form submission to create a booking record
    - Handle validation of availability, dates, and traveler counts
    - Send confirmation emails to users
    - Redirect to a payment or confirmation page
    
    Args:
        request: The HTTP request containing form data or initial GET request
        slug: The unique URL slug of the tour to book
        
    Returns:
        HttpResponse: Rendered booking form template, success redirect, or error message
    """
    # MAINTENANCE MODE: Display maintenance message
    context = {
        'maintenance_mode': True,
        'maintenance_message': 'Tour booking is temporarily unavailable while we update our database schema.',
        'expected_completion': 'Please check back later.'
    }
    return render(request, 'tours/booking.html', context)

@require_http_methods(["GET"])
def tour_dates_api(request, tour_id):
    """
    API endpoint to get available dates for a tour.
    
    This view returns JSON data with available tour dates
    for use in booking calendars and date selectors.
    
    When active, this function will:
    - Query the database for all available dates for the specified tour
    - Filter dates by availability (not fully booked)
    - Calculate remaining spots for each date
    - Return formatted date information with pricing
    - Handle date ranges and multiple month requests
    - Return properly formatted JSON for frontend calendar components
    
    Args:
        request: The HTTP request with optional date range parameters
        tour_id: Primary key ID of the tour to get dates for
        
    Returns:
        JsonResponse: JSON data with dates or maintenance message
    """
    # MAINTENANCE MODE: Return maintenance message JSON
    # This function is disabled during database schema updates
    # When active, it provides available dates for a specified tour
    return JsonResponse({
        'status': 'maintenance',
        'message': 'Tours functionality is temporarily disabled while we update our database schema.',
        'expected_completion': 'Please try again later.'
    }, status=503)


# API ViewSets

class TourCategoryViewSet(viewsets.ViewSet):
    """
    Temporary maintenance view for Tour Categories API.
    All requests will return a 503 Service Unavailable response.
    
    This class replaces the original TourCategoryViewSet during database maintenance.
    All methods return the same maintenance message with a 503 status code.
    
    When active, this ViewSet will provide a RESTful API for tour categories with:
    - List view with filtering, searching, and sorting
    - Detail view for individual categories
    - Related tours for each category
    - Category statistics (tour counts, average prices, popularity)
    - Documentation for API consumers
    
    The ViewSet supports standard REST operations and uses Django REST Framework's
    filtering, pagination, and permissions system.
    """
    # Define class attributes that would normally be used
    # These are kept for documentation purposes but won't be used in maintenance mode
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    # Add empty queryset to satisfy DRF router
    queryset = []
    
    def list(self, request):
        """
        List all tour categories - currently in maintenance mode.
        
        When active, this method will:
        - Return a paginated list of all active tour categories
        - Support filtering by name, description, or status
        - Allow sorting by name, popularity, or creation date
        - Include tour counts and related information
        - Support search parameters and field selection
        
        Args:
            request: The HTTP request object containing query parameters
            
        Returns:
            JsonResponse: 503 Service Unavailable with maintenance message when in maintenance mode
                          or serialized category data when active
        """
        return JsonResponse({
            'status': 'maintenance',
            'message': 'Tours functionality is temporarily disabled while we update our database schema.',
            'expected_completion': 'Please try again later.'
        }, status=503)
    
    def retrieve(self, request, pk=None):
        """
        Retrieve a specific tour category - currently in maintenance mode.
        
        When active, this method will:
        - Find the category by primary key or return 404
        - Return detailed category information
        - Include related tours in the response
        - Handle field selection for customized responses
        - Track analytics for category viewing
        
        Args:
            request: The HTTP request object
            pk: Primary key of the tour category to retrieve
            
        Returns:
            JsonResponse: 503 Service Unavailable with maintenance message when in maintenance mode
                          or detailed category data when active
        """
        return JsonResponse({
            'status': 'maintenance',
            'message': 'Tours functionality is temporarily disabled while we update our database schema.',
            'expected_completion': 'Please try again later.'
        }, status=503)
    
    def create(self, request):
        """
        Create a new tour category - currently in maintenance mode.
        
        When active, this method will:
        - Validate incoming category data
        - Create a new TourCategory instance
        - Handle image uploads for category thumbnails
        - Set proper permissions and ownership
        - Return the created category with status 201
        - Perform validation and error handling
        
        Args:
            request: The HTTP request object containing category data in request body
            
        Returns:
            JsonResponse: 503 Service Unavailable with maintenance message when in maintenance mode
                          or newly created category data with 201 status when active
        """
        return JsonResponse({
            'status': 'maintenance',
            'message': 'Tours functionality is temporarily disabled while we update our database schema.',
            'expected_completion': 'Please try again later.'
        }, status=503)
    
    def update(self, request, pk=None):
        """
        Update an existing tour category - currently in maintenance mode.
        
        When active, this method will:
        - Find the category by primary key or return 404
        - Validate the incoming update data
        - Update only the provided fields (partial update)
        - Handle permission checks for the requesting user
        - Return the updated category data
        - Track changes for audit purposes
        
        Args:
            request: The HTTP request object containing updated category data
            pk: Primary key of the category to update
            
        Returns:
            JsonResponse: 503 Service Unavailable with maintenance message when in maintenance mode
                          or updated category data when active
        """
        return JsonResponse({
            'status': 'maintenance',
            'message': 'Tours functionality is temporarily disabled while we update our database schema.',
            'expected_completion': 'Please try again later.'
        }, status=503)
        
    def destroy(self, request, pk=None):
        """
        Delete a specific tour category - currently in maintenance mode.
        
        When active, this method will:
        - Find the category by primary key or return 404
        - Check permissions for deletion (admin only)
        - Validate that no active tours are using this category
        - Perform soft deletion (set is_active=False) instead of hard deletion
        - Return success status with no content (204)
        - Log the deletion for audit purposes
        
        Args:
            request: The HTTP request object
            pk: Primary key of the category to delete
            
        Returns:
            JsonResponse: 503 Service Unavailable with maintenance message when in maintenance mode
                          or 204 No Content when active
        """
        return JsonResponse({
            'status': 'maintenance',
            'message': 'Tours functionality is temporarily disabled while we update our database schema.',
            'expected_completion': 'Please try again later.'
        }, status=503)




# Comment out the original ViewSet and use a dummy replacement
# Original class replaced with a simple view function that returns a maintenance message
# This prevents any database queries that would fail due to schema mismatch
class TourViewSet(viewsets.ViewSet):
    """
    Temporary maintenance view for Tours API.
    All requests will return a 503 Service Unavailable response.
    
    This class replaces the original TourViewSet during database maintenance.
    All methods return the same maintenance message with a 503 status code.
    
    When active, this ViewSet will provide a complete RESTful API for tours with:
    - List view with advanced filtering (price, duration, dates, categories)
    - Detail view with comprehensive tour information
    - Search functionality across multiple tour fields
    - Sorting options (price, popularity, duration, rating)
    - Related data (itinerary, reviews, dates, images)
    - Custom actions for specific tour operations
    
    The ViewSet handles permissions, throttling, and authentication for
    both public and authenticated API consumers.
    """
    # Define class attributes that would normally be used for filtering and ordering
    # These are kept for documentation purposes but won't be used in maintenance mode
    search_fields = ['name', 'description', 'short_description', 'start_location', 'end_location']
    ordering_fields = ['name', 'price', 'duration_days', 'created_at']
    ordering = ['name']
    
    # Add empty queryset to satisfy DRF router
    queryset = []
    
    def list(self, request):
        """
        List all tours - currently in maintenance mode.
        
        When active, this method will:
        - Return a paginated list of all active tours
        - Support comprehensive filtering (category, price, duration, dates)
        - Allow sorting by various criteria (name, price, popularity, rating)
        - Include primary images and basic information for each tour
        - Support search functionality across multiple fields
        - Handle various query parameters for customized listings
        
        Args:
            request: The HTTP request object with optional query parameters
            
        Returns:
            JsonResponse: 503 Service Unavailable with maintenance message when in maintenance mode
                          or paginated list of tours when active
        """
        return JsonResponse({
            'status': 'maintenance',
            'message': 'Tours functionality is temporarily disabled while we update our database schema.',
            'expected_completion': 'Please try again later.'
        }, status=503)
    
    def retrieve(self, request, pk=None):
        """
        Retrieve a specific tour - currently in maintenance mode.
        
        When active, this method will:
        - Find the tour by primary key or slug
        - Return detailed tour information including:
          * Full description and details
          * All related images
          * Itinerary information
          * Available dates and pricing
          * Reviews and ratings
          * Related tours and destinations
        - Track view counts for popularity metrics
        - Handle field selection for customized responses
        
        Args:
            request: The HTTP request object
            pk: Primary key or slug of the tour to retrieve
            
        Returns:
            JsonResponse: 503 Service Unavailable with maintenance message when in maintenance mode
                          or detailed tour data when active
        """
        return JsonResponse({
            'status': 'maintenance',
            'message': 'Tours functionality is temporarily disabled while we update our database schema.',
            'expected_completion': 'Please try again later.'
        }, status=503)
    
    def create(self, request):
        """
        Create a new tour - currently in maintenance mode.
        
        When active, this method will:
        - Validate incoming tour data using serializers
        - Create a new Tour instance with proper relationships
        - Handle related data creation (images, itinerary, dates)
        - Validate complex relationships and constraints
        - Apply permission checks (admin/staff only)
        - Return the created tour with all related data
        - Handle errors and validation issues
        
        Args:
            request: The HTTP request object containing complete tour data
            
        Returns:
            JsonResponse: 503 Service Unavailable with maintenance message when in maintenance mode
                          or newly created tour data with 201 status when active
        """
        return JsonResponse({
            'status': 'maintenance',
            'message': 'Tours functionality is temporarily disabled while we update our database schema.',
            'expected_completion': 'Please try again later.'
        }, status=503)
    
    def update(self, request, pk=None):
        """
        Update an existing tour - currently in maintenance mode.
        
        When active, this method will:
        - Find the tour by primary key
        - Validate the incoming update data
        - Support both full and partial updates
        - Handle complex relationship updates
        - Maintain data consistency across related models
        - Apply permission and ownership checks
        - Track changes for audit purposes
        - Return the fully updated tour data
        
        Args:
            request: The HTTP request object containing updated tour data
            pk: Primary key of the tour to update
            
        Returns:
            JsonResponse: 503 Service Unavailable with maintenance message when in maintenance mode
                          or updated tour data when active
        """
        return JsonResponse({
            'status': 'maintenance',
            'message': 'Tours functionality is temporarily disabled while we update our database schema.',
            'expected_completion': 'Please try again later.'
        }, status=503)
        
    def destroy(self, request, pk=None):
        """
        Delete a specific tour - currently in maintenance mode.
        
        When active, this method will:
        - Find the tour by primary key
        - Validate that no active bookings exist for this tour
        - Check permissions (admin only)
        - Perform soft deletion (is_active=False) rather than database deletion
        - Handle related records appropriately
        - Log the deletion for audit purposes
        - Return success status with no content (204)
        
        Args:
            request: The HTTP request object
            pk: Primary key of the tour to delete
            
        Returns:
            JsonResponse: 503 Service Unavailable with maintenance message when in maintenance mode
                          or 204 No Content when active
        """
        return JsonResponse({
            'status': 'maintenance',
            'message': 'Tours functionality is temporarily disabled while we update our database schema.',
            'expected_completion': 'Please try again later.'
        }, status=503)
    
    @action(detail=True, methods=['get'])
    def itinerary(self, request, pk=None):
        """
        Retrieve the itinerary for a specific tour - currently in maintenance mode.
        
        When active, this custom action will:
        - Find the tour by primary key
        - Retrieve all itinerary days in proper order
        - Include detailed daily activities, locations, and times
        - Format the data for display in a timeline/calendar view
        - Include related points of interest and maps
        - Support day-by-day filtering options
        
        Args:
            request: The HTTP request object with optional day parameters
            pk: Primary key of the tour to retrieve itinerary for
            
        Returns:
            JsonResponse: 503 Service Unavailable with maintenance message when in maintenance mode
                          or structured itinerary data when active
        """
        return JsonResponse({
            'status': 'maintenance',
            'message': 'Tours functionality is temporarily disabled while we update our database schema.',
            'expected_completion': 'Please try again later.'
        }, status=503)
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """
        Retrieve reviews for a specific tour - currently in maintenance mode.
        
        When active, this custom action will:
        - Find the tour by primary key
        - Return all approved reviews for the tour
        - Include ratings, review text, and reviewer information
        - Support sorting by date, rating (high/low)
        - Calculate and return aggregate rating statistics
        - Handle pagination for tours with many reviews
        - Filter reviews based on various criteria (verified purchases, date range)
        
        Args:
            request: The HTTP request object with optional filter/sort parameters
            pk: Primary key of the tour to retrieve reviews for
            
        Returns:
            JsonResponse: 503 Service Unavailable with maintenance message when in maintenance mode
                          or paginated list of reviews with statistics when active
        """
        return JsonResponse({
            'status': 'maintenance',
            'message': 'Tours functionality is temporarily disabled while we update our database schema.',
            'expected_completion': 'Please try again later.'
        }, status=503)
    
    @action(detail=True, methods=['get'])
    def dates(self, request, pk=None):
        """
        Retrieve available dates for a specific tour - currently in maintenance mode.
        
        When active, this custom action will:
        - Find the tour by primary key
        - Return all future available tour dates
        - Include pricing, availability, and remaining spots
        - Support date range filtering (start/end date)
        - Format data for easy consumption by calendar components
        - Include special promotions or discounts for specific dates
        - Handle availability calculations based on current bookings
        
        Args:
            request: The HTTP request object with optional date range parameters
            pk: Primary key of the tour to retrieve dates for
            
        Returns:
            JsonResponse: 503 Service Unavailable with maintenance message when in maintenance mode
                          or list of available dates with pricing when active
        """
        return JsonResponse({
            'status': 'maintenance',
            'message': 'Tours functionality is temporarily disabled while we update our database schema.',
            'expected_completion': 'Please try again later.'
        }, status=503)
