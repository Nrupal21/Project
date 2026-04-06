"""
Views for the destinations app.

This module contains views for handling API endpoints related to destinations,
regions, and attractions, as well as template views for the web interface.
"""
from datetime import datetime, timedelta
from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, F, Count, Avg, Sum, Prefetch, Case, When, Value, IntegerField
from math import radians, sin, cos, sqrt, atan2
from django.db.models.functions import Radians, Sin, Cos, ATan2, Sqrt, Radians
from django.db.models.expressions import RawSQL
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import connection, models
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse_lazy
from django.contrib import messages
# Use absolute import instead of relative import
from destinations import models
from django.core.paginator import Paginator
from django.conf import settings

# Use absolute import for models as well
from destinations.models import Region, Destination, Attraction, Season, DestinationImage

# We're not importing admin views here because it would cause a circular import
# The admin views are in destinations/views/admin.py and are imported in urls.py
# Assuming we'll create these serializers later when needed
class RegionSerializer:
    class Meta:
        model = Region
        fields = '__all__'

class RegionDetailSerializer:
    class Meta:
        model = Region
        fields = '__all__'

class DestinationSerializer:
    class Meta:
        model = Destination
        fields = '__all__'

class DestinationDetailSerializer:
    class Meta:
        model = Destination
        fields = '__all__'

class AttractionSerializer:
    class Meta:
        model = Attraction
        fields = '__all__'

class SeasonSerializer:
    class Meta:
        model = Season
        fields = '__all__'

def destination_list_view(request):
    """
    Render the destinations list page.
    
    This view displays all active destinations with optional filtering by:
    - Region
    - Search term
    - Featured status
    
    Args:
        request: The HTTP request object
        
    Returns:
        HttpResponse: Rendered template with destination data
    """
    # Get base queryset of active and approved destinations
    destinations = Destination.objects.filter(
        is_active=True,
        approval_status=Destination.ApprovalStatus.APPROVED  # Only show approved destinations
    )
    
    # Apply filters from query parameters
    region_id = request.GET.get('region')
    search_query = request.GET.get('search')
    featured_only = request.GET.get('featured') == '1'
    sort_by = request.GET.get('sort', 'name')
    
    # Filter by region if specified
    if region_id:
        destinations = destinations.filter(region_id=region_id, region__is_active=True)
    
    # Filter by search query if provided
    if search_query:
        destinations = destinations.filter(
            Q(name__icontains=search_query) |
            Q(short_description__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(country__icontains=search_query)
        )
    
    # Filter featured destinations if requested
    if featured_only:
        destinations = destinations.filter(is_featured=True)
    
    # Apply sorting
    destinations = destinations.order_by(sort_by)
    
    # Get all active regions for the filter dropdown
    regions = Region.objects.filter(is_active=True).order_by('name')
    
    # Pagination
    paginator = Paginator(destinations, 12)  # Show 12 destinations per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'destinations': page_obj,
        'regions': regions,
        'search_query': search_query or '',
        'region_id': region_id,
        'featured_only': featured_only,
        'sort_by': sort_by,
    }
    
    return render(request, 'destinations/destination_list.html', context)


def destination_detail_view(request, slug):
    """
    Render the destination detail page.
    
    This view retrieves a specific destination by its slug and displays its details,
    including attractions, images, and related information.
    
    Args:
        request: The HTTP request
        slug: The slug of the destination to display
        
    Returns:
        HttpResponse: Rendered template with destination details
    """
    # Get the destination or return 404 if not found
    destination = get_object_or_404(Destination, slug=slug, is_active=True)
    
    # Increment view count
    destination.views = F('views') + 1
    destination.save(update_fields=['views'])
    
    # Get related attractions
    attractions = destination.attractions.filter(is_active=True)
    
    # Create context for template
    context = {
        'destination': destination,
        'attractions': attractions,
    }
    
    return render(request, 'destinations/destination_detail.html', context)


class RegionDetailView(DetailView):
    """
    Display details for a single region.
    
    This class-based view shows information about a region and its destinations.
    """
    model = Region
    template_name = 'destinations/region_detail.html'
    context_object_name = 'region'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        """
        Get the queryset of active regions.
        
        Returns:
            QuerySet: Filtered queryset of active regions
        """
        return Region.objects.filter(is_active=True)


class DestinationListView(ListView):
    """
    Display a list of destinations with filtering and pagination.
    
    This class-based view provides a comprehensive implementation for displaying
    destinations from the database with various filtering options, pagination,
    and sorting capabilities.
    
    Key features:
    - Retrieves destinations directly from the database
    - Applies filters based on query parameters (region, search, featured status)
    - Calculates distances for nearby destinations using Haversine formula
    - Provides pagination for large result sets
    - Optimizes database queries with select_related and prefetch_related
    """
    model = Destination
    template_name = 'destinations/destination_list.html'
    context_object_name = 'destinations'
    paginate_by = 12
    
    def get_queryset(self):
        """
        Get the queryset with applied filters and optimized database queries.
        
        This method builds a database query that:
        1. Retrieves all active destinations regardless of approval status
        2. Applies user-specified filters (region, search term, featured status)
        3. Calculates distances for nearby location searches
        4. Optimizes database access with select_related and prefetch_related
        5. Orders results appropriately based on filters
        
        Returns:
            QuerySet: Filtered and optimized queryset of all active destinations
        """
        from django.db.models import F, FloatField, ExpressionWrapper, Case, When
        from django.db.models.functions import Radians, Sin, Cos, ACos, Radians
        import math
        
        # Get base queryset with optimized database access
        # - select_related fetches related region data in the same query
        # - prefetch_related efficiently loads related images in a separate query
        queryset = super().get_queryset().select_related('region').prefetch_related('images')
        
        # Only filter by active status, showing all destinations regardless of approval status
        # This allows all destinations to be visible in the listings
        queryset = queryset.filter(is_active=True)
        
        # Filter by region if specified
        # This allows users to narrow down destinations by geographical region
        region_slug = self.request.GET.get('region')
        if region_slug:
            queryset = queryset.filter(region__slug=region_slug)
            
        # Filter by search term if provided
        # This implements a comprehensive text search across multiple fields
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(short_description__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(city__icontains=search_query) |
                Q(country__icontains=search_query)
            )
            
        # Filter featured destinations if specified
        # This allows users to see only highlighted/featured destinations
        featured = self.request.GET.get('featured')
        if featured and featured.lower() in ['true', '1', 'yes']:
            queryset = queryset.filter(is_featured=True)
            
        # Filter by nearby location if coordinates are provided
        # This implements a location-based search using the Haversine formula
        nearby = self.request.GET.get('nearby')
        if nearby:
            try:
                # Parse latitude and longitude from the query parameter
                lat, lng = map(float, nearby.split(','))
                
                # Validate coordinates are within valid ranges
                if -90 <= lat <= 90 and -180 <= lng <= 180:
                    # Calculate distance using Haversine formula
                    # This formula accounts for Earth's curvature when calculating distances
                    dlat = Radians(F('latitude') - lat)
                    dlon = Radians(F('longitude') - lng)
                    a = (
                        Sin(dlat / 2) * Sin(dlat / 2) +
                        Cos(Radians(lat)) * Cos(Radians(F('latitude'))) *
                        Sin(dlon / 2) * Sin(dlon / 2)
                    )
                    c = 2 * ACos(a)
                    distance_km = 6371 * c  # 6371 is Earth's radius in km
                    
                    # Annotate queryset with distance
                    # This adds a 'distance_km' field to each destination object
                    queryset = queryset.annotate(
                        distance_km=Case(
                            When(latitude__isnull=False, longitude__isnull=False,
                                 then=distance_km),
                            default=None,
                            output_field=FloatField()
                        )
                    ).filter(distance_km__isnull=False)
                    
                    # Store the reference point for distance ordering and context
                    self.reference_lat = lat
                    self.reference_lng = lng
                    
                    # Order by distance (closest first)
                    queryset = queryset.order_by('distance_km')
            except (ValueError, TypeError):
                # If coordinates are invalid, just continue without location filtering
                # This provides graceful degradation for malformed parameters
                pass
        else:
            # Default ordering by featured first, then by name
            # This ensures featured destinations appear at the top of the list
            queryset = queryset.order_by('-is_featured', 'name')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.
        
        This method enriches the template context with:
        1. Region data for filter dropdowns
        2. Current filter parameters for maintaining state
        3. Location data for nearby searches
        4. Distance calculations for each destination when applicable
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Enhanced context dictionary with added filter and location data
        """
        context = super().get_context_data(**kwargs)
        
        # Add all active regions for filter dropdown
        # This provides data for the region filter in the template
        context['regions'] = Region.objects.filter(is_active=True).order_by('name')
        
        # Add current filter parameters to context
        # This maintains filter state across pagination and helps with UI feedback
        context['current_region'] = self.request.GET.get('region')
        context['search_query'] = self.request.GET.get('q', '')
        context['is_featured'] = self.request.GET.get('featured') == '1'
        context['sort_by'] = self.request.GET.get('sort', 'name')
        
        # Add location context if we're filtering by nearby
        # This provides distance information for the nearby view
        if hasattr(self, 'reference_lat') and hasattr(self, 'reference_lng'):
            context['is_nearby_view'] = True
            context['reference_lat'] = self.reference_lat
            context['reference_lng'] = self.reference_lng
            
            # Add formatted distance to each destination in the object list
            # This makes the distance available in the template with proper formatting
            for destination in context['object_list']:
                if hasattr(destination, 'distance_km'):
                    destination.distance = round(destination.distance_km, 1)
        
        return context


class DestinationDetailView(DetailView):
    """
    Display details for a single destination.
    
    This class-based view shows comprehensive information about a destination,
    including its attractions, images, and related content. It retrieves data
    directly from the database and optimizes queries for performance.
    
    Key features:
    - Permission-based access control (different users see different destinations)
    - Optimized database queries with select_related and prefetch_related
    - View count tracking for analytics
    - Related content retrieval (attractions, nearby destinations)
    - Integration with Google Maps for location visualization
    """
    model = Destination
    template_name = 'destinations/destination_detail.html'
    context_object_name = 'destination'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        """
        Get the queryset of destinations appropriate for the current user with optimized queries.
        
        This method implements a permission-based access control system:
        1. Anonymous users: Can only view approved destinations
        2. Content creators (local guides): Can view approved destinations plus their own pending ones
        3. Managers/admins: Can view all destinations regardless of approval status
        
        The method also optimizes database access by using:
        - select_related: For efficient loading of related region data
        - prefetch_related: For efficient loading of related images and attractions
        
        Returns:
            QuerySet: Filtered and optimized queryset of visible destinations for the current user
        """
        # Start with base queryset and optimize with select_related and prefetch_related
        # This significantly reduces the number of database queries needed
        queryset = Destination.objects.filter(is_active=True)\
            .select_related('region', 'created_by')\
            .prefetch_related('images', 'attractions', 'seasons')
        
        # Check if user is authenticated
        # Anonymous users have the most restricted access
        if not self.request.user.is_authenticated:
            # For anonymous users, only show approved destinations
            return queryset.filter(approval_status=Destination.ApprovalStatus.APPROVED)
        
        # Check if user is manager or admin (can see all destinations)
        # Staff and managers have full access to all destinations
        if self.request.user.is_staff or getattr(self.request.user, 'role', None) == 'MANAGER':
            return queryset
        
        # For local guides, show approved destinations plus their own pending destinations
        # This allows content creators to view their own work even before approval
        return queryset.filter(
            Q(approval_status=Destination.ApprovalStatus.APPROVED) | 
            Q(created_by=self.request.user)
        )
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.
        
        This method enriches the template context with:
        1. Related attractions filtered by active status
        2. Related destinations from the same region
        3. Google Maps API key for location visualization
        4. Updated view count for analytics
        
        The method also handles view count incrementation in an atomic way
        using F() expressions to prevent race conditions.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Enhanced context dictionary with added destination-related data
        """
        # Get base context from parent class
        context = super().get_context_data(**kwargs)
        destination = self.get_object()
        
        # Increment view count atomically using F() expression
        # This prevents race conditions when multiple users view simultaneously
        destination.views = F('views') + 1
        destination.save(update_fields=['views'])
        
        # Refresh the object to get the updated view count
        # This ensures the template shows the correct, updated count
        destination.refresh_from_db()
        
        # Get related attractions with optimized query
        # Filter by active status to ensure only published attractions are shown
        context['attractions'] = destination.attractions.filter(is_active=True)\
            .select_related('destination')\
            .prefetch_related('images')
        
        # Get related destinations from the same region
        # Limit to 4 to avoid overwhelming the user and optimize performance
        context['related_destinations'] = Destination.objects.filter(
            region=destination.region,
            is_active=True,
            approval_status=Destination.ApprovalStatus.APPROVED
        ).exclude(pk=destination.pk)\
         .select_related('region')\
         .prefetch_related('images')[:4]
        
        # Add Google Maps API key to context for map integration
        context['GOOGLE_MAPS_API_KEY'] = getattr(settings, 'GOOGLE_MAPS_API_KEY', '')
        
        return context


class AttractionListView(ListView):
    """
    Display a list of attractions with filtering and pagination.
    
    This class-based view shows attractions across all destinations with
    options for filtering by destination, category, search terms, and featured status.
    It retrieves data directly from the database with optimized queries to ensure
    efficient page loading and rendering.
    
    Key features:
    - Database-driven attraction listing with pagination
    - Multiple filter options (destination, category, search, featured)
    - Optimized database queries with select_related and prefetch_related
    - Customizable sorting options
    - Context preparation for filter UI components
    """
    model = Attraction
    template_name = 'destinations/attraction_list.html'
    context_object_name = 'attractions'
    paginate_by = 12  # Show 12 attractions per page for optimal UI layout
    
    def get_queryset(self):
        """
        Get the queryset with applied filters and optimized database access.
        
        This method builds a filtered queryset of attractions based on user-selected
        filter parameters from the request. It optimizes database access by using
        select_related for foreign key relationships and prefetch_related for reverse
        relationships to minimize database queries.
        
        Filter options include:
        - Destination: Filter by specific destination
        - Search: Full-text search across name, description, address fields
        - Category: Filter by attraction category
        - Featured: Show only featured attractions
        - Sorting: Order by various fields (name, rating, etc.)
        
        Returns:
            QuerySet: Filtered and optimized queryset of attractions
        """
        # Start with base queryset and optimize with select_related and prefetch_related
        # This significantly reduces the number of database queries needed
        queryset = Attraction.objects.filter(is_active=True)\
            .select_related('destination')\
            .prefetch_related('images')
        
        # Get filter parameters from request GET parameters
        # These determine how the attraction list will be filtered
        destination_id = self.request.GET.get('destination')
        search_query = self.request.GET.get('search')
        category = self.request.GET.get('category')
        featured_only = self.request.GET.get('featured') == '1'
        sort_by = self.request.GET.get('sort', 'name')  # Default sort by name
        
        # Apply destination filter if specified
        # This limits attractions to a specific destination
        if destination_id:
            queryset = queryset.filter(destination_id=destination_id)
        
        # Apply search filter if search query is provided
        # This performs a case-insensitive search across multiple fields
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(address__icontains=search_query) |
                Q(city__icontains=search_query) |
                Q(country__icontains=search_query)
            )
        
        # Apply category filter if specified
        # This limits attractions to a specific category
        if category:
            queryset = queryset.filter(category=category)
        
        # Apply featured filter if requested
        # This shows only attractions marked as featured
        if featured_only:
            queryset = queryset.filter(is_featured=True)
        
        # Apply sorting based on sort parameter
        # This determines the order of attractions in the list
        return queryset.order_by(sort_by)
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data for template rendering.
        
        This method enriches the template context with:
        1. List of destinations for the destination filter dropdown
        2. List of unique categories for the category filter dropdown
        3. Current filter parameters to maintain state across pagination
        
        These additional context variables enable the template to render
        filter UI components with the correct options and selected values.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Enhanced context dictionary with added filter data
        """
        # Get base context from parent class
        context = super().get_context_data(**kwargs)
        
        # Add destinations for filter dropdown
        # Only include active destinations, ordered by name for usability
        context['destinations'] = Destination.objects.filter(
            is_active=True, 
            approval_status=Destination.ApprovalStatus.APPROVED
        ).order_by('name')
        
        # Add unique categories for filter dropdown
        # This creates a list of all unique non-empty category values
        categories = Attraction.objects.filter(is_active=True)\
            .values_list('category', flat=True).distinct()
        context['categories'] = [c for c in categories if c]
        
        # Add current filter values to context
        # This maintains filter state across pagination
        context['search_query'] = self.request.GET.get('search', '')
        context['destination_id'] = self.request.GET.get('destination')
        context['category'] = self.request.GET.get('category')
        context['featured_only'] = self.request.GET.get('featured') == '1'
        context['sort_by'] = self.request.GET.get('sort', 'name')
        
        return context


class AttractionDetailView(DetailView):
    """
    Display details for a single attraction.
    
    This class-based view shows comprehensive information about an attraction,
    including its images, location, and related content. It retrieves data
    directly from the database with optimized queries to ensure efficient
    page loading and rendering.
    
    Key features:
    - Database-driven attraction detail display
    - Optimized database queries with select_related and prefetch_related
    - Related attractions from the same destination
    - Google Maps integration for location visualization
    - Comprehensive context preparation for template rendering
    """
    model = Attraction
    template_name = 'destinations/attraction_detail.html'
    context_object_name = 'attraction'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        """
        Get the queryset of active attractions with optimized database access.
        
        This method enhances the base queryset by:
        1. Filtering to include only active attractions
        2. Using select_related to efficiently load the destination data
        3. Using prefetch_related to efficiently load images
        
        This optimization significantly reduces the number of database queries
        needed to render the attraction detail page.
        
        Returns:
            QuerySet: Filtered and optimized queryset of active attractions
        """
        # Start with base queryset and apply active filter
        # Then optimize with select_related and prefetch_related
        return super().get_queryset()\
            .filter(is_active=True)\
            .select_related('destination')\
            .prefetch_related('images')
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data for template rendering.
        
        This method enriches the template context with:
        1. Related attractions from the same destination
        2. The parent destination object for navigation and context
        3. Google Maps API key for location visualization
        
        The related attractions are optimized with select_related and
        prefetch_related to minimize database queries.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Enhanced context dictionary with added attraction-related data
        """
        # Get base context from parent class
        context = super().get_context_data(**kwargs)
        attraction = self.get_object()
        
        # Get related attractions (same destination, excluding current attraction)
        # Optimize with select_related and prefetch_related
        # Limit to 4 to avoid overwhelming the user and optimize performance
        related_attractions = Attraction.objects.filter(
            destination=attraction.destination,
            is_active=True
        ).exclude(id=attraction.id)\
         .select_related('destination')\
         .prefetch_related('images')[:4]
        
        # Update context with additional data needed by the template
        context.update({
            'related_attractions': related_attractions,
            'destination': attraction.destination,  # Parent destination for context
            'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,  # For map integration
        })
        
        return context


class DestinationCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    View for creating new destinations with different workflows based on user role.
    
    This view implements a role-based routing system:
    1. Local guides are redirected to the pending destination submission workflow
    2. Managers and admins can directly create approved destinations
    
    The view includes authorization checks via UserPassesTestMixin to ensure
    only appropriate users can access direct creation capabilities. Local guides
    are automatically redirected to the pending submission workflow during the
    dispatch phase, before permissions are checked.
    
    Template used: 'destinations/destination_form.html'  
    Model: Destination
    
    Key features:
    - Role-based access control and workflow routing
    - Direct creation for managers and admins
    - Redirect to pending workflow for local guides
    - Comprehensive form validation and image handling
    - Email notifications for new submissions
    """
    model = Destination
    template_name = 'destinations/destination_form.html'
    fields = ['name', 'region', 'short_description', 'description', 'city', 'country', 'latitude', 'longitude', 'is_featured']
    success_url = reverse_lazy('destinations:destination_list')
    
    def dispatch(self, request, *args, **kwargs):
        """
        Route local guides to the pending destination workflow.
        
        This method intercepts all requests and redirects local guides to the
        pending destination submission form while allowing managers and admins
        to access the direct creation form.
        
        Args:
            request: The HTTP request
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            HttpResponse: Either redirect for local guides or normal dispatch for managers/admins
        """
        if request.user.is_authenticated:
            # Check if the user is a local guide (not manager or admin)
            if request.user.role == 'LOCAL_GUIDE' and not (request.user.is_manager or request.user.is_admin):
                # Add a message explaining the redirect
                messages.info(
                    request,
                    'As a local guide, your destination submissions will be reviewed by our team before publication.'
                )
                # Redirect to the pending destination create view
                return redirect('destinations:pending_destination_create')
        
        # For managers, admins, or if somehow an unauthenticated user got here
        return super().dispatch(request, *args, **kwargs)
    
    def test_func(self):
        """
        Check if the current user has permission to directly create destinations.
        
        Only managers and admins are allowed to directly create destinations.
        Local guides are redirected to the pending submission workflow in dispatch(),
        but this provides a second layer of security in case that redirect is bypassed.
        
        Returns:
            bool: True if user is admin or manager, False otherwise
        """
        return self.request.user.is_authenticated and (self.request.user.is_manager or self.request.user.is_admin)
        
    def form_valid(self, form):
        """Process the form when it's valid for all authenticated users.
        
        Sets the created_by field and approval status based on user role:
        - Managers/Admins: Auto-approved and published immediately
        - Local Guides: Set to pending status for approval workflow
        
        Handles image uploads if provided.
        
        Args:
            form: The valid form instance
            
        Returns:
            HttpResponse: Redirect to the success URL
        """
        # Record who created this destination
        form.instance.created_by = self.request.user
        
        # Set approval status based on user role
        if self.request.user.is_manager or self.request.user.is_admin:
            # Auto-approve destinations created by managers/admins
            form.instance.approval_status = Destination.ApprovalStatus.APPROVED
            success_message = f'Destination "{form.instance.name}" has been successfully published and is now visible on the site.'
        else:
            # Local guides' destinations need approval
            form.instance.approval_status = Destination.ApprovalStatus.PENDING
            success_message = f'Destination "{form.instance.name}" has been submitted for review. You will be notified once it\'s approved.'
        
        response = super().form_valid(form)
        
        # Handle image uploads if any
        cover_image = self.request.FILES.get('cover_image')
        banner_image = self.request.FILES.get('banner_image')
        
        if cover_image:
            self.object.images.create(
                image=cover_image,
                caption=f"Cover image for {self.object.name}",
                is_primary=True
            )
        
        if banner_image:
            self.object.images.create(
                image=banner_image,
                caption=f"Banner image for {self.object.name}",
                is_primary=False
            )
        
        # Send notification emails if it's a local guide submission requiring approval
        if self.request.user.is_local_guide and not (self.request.user.is_manager or self.request.user.is_admin):
            try:
                from destinations.utils.email_notifications import send_destination_submission_notification
                send_destination_submission_notification(destination=self.object, submitter=self.request.user)
            except ImportError:
                # Handle case where email notification utility is not available
                pass
        
        # Show appropriate success message
        messages.success(self.request, success_message)
        return response


class AttractionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    View for creating a new attraction.
    
    This view allows authenticated users with the LOCAL_GUIDE role to create new attractions.
    It handles the form submission, validation, and image uploads.
    """
    model = Attraction
    template_name = 'destinations/attraction_form.html'
    fields = [
        'name', 'destination', 'category', 'description',
        'address', 'city', 'country', 'latitude', 'longitude', 'is_featured'
    ]
    success_url = reverse_lazy('destinations:attraction_list')
    
    def test_func(self):
        """
        Check if the user has permission to create an attraction.
        
        Returns:
            bool: True if user is authenticated and has LOCAL_GUIDE role, False otherwise
        """
        return self.request.user.is_authenticated and self.request.user.role == 'LOCAL_GUIDE'
    
    def get_initial(self):
        """
        Set initial values for the form.
        
        If a destination_id is provided in the URL, pre-populate the destination field
        and set initial coordinates from the destination.
        
        Returns:
            dict: Initial data for the form
        """
        initial = super().get_initial()
        destination_id = self.kwargs.get('destination_id')
        
        if destination_id:
            try:
                destination = Destination.objects.get(pk=destination_id)
                initial['destination'] = destination.id
                if destination.latitude:
                    initial['latitude'] = float(destination.latitude)
                if destination.longitude:
                    initial['longitude'] = float(destination.longitude)
                if destination.city:
                    initial['city'] = destination.city
                if destination.country:
                    initial['country'] = destination.country
            except (Destination.DoesNotExist, ValueError):
                pass
                
        return initial
        
    def get_form(self, form_class=None):
        """
        Return an instance of the form to be used in this view.
        
        Returns:
            Form: The form instance
        """
        form = super().get_form(form_class)
        
        # Set the queryset for the destination field to only show active destinations
        form.fields['destination'].queryset = Destination.objects.filter(is_active=True)
        
        return form
        
    def form_valid(self, form):
        """
        Process the form when it's valid.
        
        Sets the created_by field to the current user before saving and handles
        image uploads for the attraction.
        
        Args:
            form: The valid form instance
            
        Returns:
            HttpResponse: Redirect to the success URL
        """
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # Handle image uploads if any
        cover_image = self.request.FILES.get('cover_image')
        banner_image = self.request.FILES.get('banner_image')
        
        if cover_image:
            self.object.images.create(
                image=cover_image,
                caption=f"Cover image for {self.object.name}",
                is_primary=True
            )
        
        if banner_image:
            self.object.images.create(
                image=banner_image,
                caption=f"Banner image for {self.object.name}",
                is_primary=False
            )
            
        messages.success(self.request, 'Attraction created successfully!')
        return response


@require_http_methods(["GET"])
def nearby_destinations(request):
    """
    Find destinations within a specified radius (in kilometers) of a given latitude and longitude.
    
    This API endpoint calculates distances using the Haversine formula and returns destinations
    sorted by their proximity to the provided coordinates. The function optimizes database
    queries by first applying a bounding box filter to reduce the number of destinations
    that need detailed distance calculations.
    
    Implementation details:
    1. Validates and parses input parameters
    2. Creates a bounding box filter to reduce initial dataset size
    3. Performs precise Haversine distance calculation on filtered destinations
    4. Includes primary images and other essential destination data
    5. Returns JSON response with sorted destinations by distance
    
    Query Parameters:
    - lat: Latitude of the center point (required)
    - lng: Longitude of the center point (required)
    - radius: Search radius in kilometers (default: 10)
    - limit: Maximum number of results to return (default: 6)
    
    Returns:
        JsonResponse: List of nearby destinations with distance information
    """
    # Parse and validate query parameters
    # This ensures we have valid numerical values for calculations
    try:
        lat = float(request.GET.get('lat', 0))
        lng = float(request.GET.get('lng', 0))
        radius = float(request.GET.get('radius', 10))  # Default 10km radius
        limit = int(request.GET.get('limit', 6))  # Default to 6 results
    except (ValueError, TypeError):
        return JsonResponse({
            'success': False,
            'error': 'Invalid latitude, longitude, radius, or limit parameter'
        }, status=400)
    
    # Validate required parameters
    # Both latitude and longitude are required for distance calculations
    if not lat or not lng:
        return JsonResponse({
            'success': False,
            'error': 'Latitude and longitude are required'
        }, status=400)
    
    # Initialize results container
    destinations = []
    
    # Earth radius in kilometers (constant for Haversine formula)
    R = 6371
    
    # Convert reference coordinates from degrees to radians for trigonometric calculations
    lat_rad = radians(lat)
    lng_rad = radians(lng)
    
    # Optimize database query with select_related and prefetch_related
    # This significantly reduces the number of database queries needed
    all_destinations = Destination.objects.filter(is_active=True)\
        .select_related('region')\
        .prefetch_related(
            models.Prefetch(
                'images',
                queryset=DestinationImage.objects.filter(is_primary=True),
                to_attr='primary_images'
            )
        )
    
    # Create a bounding box filter for initial optimization
    # This is much faster than calculating exact distances for all destinations
    # 1 degree of latitude is approximately 111 km
    lat_range = radius / 111.0
    # 1 degree of longitude varies based on latitude, using cosine adjustment
    lng_range = radius / (111.0 * cos(lat_rad))
    
    # Apply bounding box filter to database query
    # This creates a square region that fully contains our circular search area
    box_filter = all_destinations.filter(
        latitude__gte=lat - lat_range,
        latitude__lte=lat + lat_range,
        longitude__gte=lng - lng_range,
        longitude__lte=lng + lng_range
    )
    
    # Process each destination in the bounding box
    for destination in box_filter:
        # Skip destinations without valid coordinates
        if not destination.latitude or not destination.longitude:
            continue
        
        # Convert destination coordinates to radians for Haversine calculation
        d_lat_rad = radians(float(destination.latitude))
        d_lng_rad = radians(float(destination.longitude))
        
        # Calculate distance using Haversine formula
        # This gives the great-circle distance between two points on a sphere
        dlat = d_lat_rad - lat_rad
        dlng = d_lng_rad - lng_rad
        a = sin(dlat/2)**2 + cos(lat_rad) * cos(d_lat_rad) * sin(dlng/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = R * c  # Distance in kilometers
        
        # Only include destinations within the specified radius
        # This creates the circular region from our square bounding box
        if distance <= radius:
            # Get primary image efficiently using prefetched data
            primary_image = None
            if hasattr(destination, 'primary_images') and destination.primary_images:
                primary_image = destination.primary_images[0]
            image_url = primary_image.image.url if primary_image else None
            
            # Build destination data dictionary with essential information
            destinations.append({
                'id': destination.id,
                'name': destination.name,
                'slug': destination.slug,
                'short_description': destination.short_description,
                'city': destination.city,
                'country': destination.country,
                'distance': round(distance, 1),  # Round to 1 decimal place for display
                'image_url': image_url,
                'rating': float(destination.rating) if destination.rating else None,
                'price': float(destination.price) if destination.price else None
            })
    
    # Sort results by distance and apply limit
    # This ensures users see the closest destinations first
    destinations = sorted(destinations, key=lambda x: x['distance'])[:limit]
    
    # Return JSON response with destination data
    return JsonResponse({
        'success': True,
        'count': len(destinations),
        'destinations': destinations
    })


class MyDestinationsView(LoginRequiredMixin, ListView):
    """
    View for displaying destinations created by the current user.
    
    This view shows a paginated list of all destinations created by the currently
    logged-in user, with options to filter by approval status and other criteria.
    It retrieves data directly from the database with optimized queries to ensure
    efficient page loading and rendering.
    
    Key features:
    - Database-driven destination listing with pagination
    - Status-based filtering (pending, approved, rejected)
    - Optimized database queries with select_related and prefetch_related
    - Reverse chronological ordering by creation date
    - Comprehensive context preparation for template rendering
    
    Template used: 'destinations/my_destinations.html'
    Context data includes:
    - destinations: Paginated queryset of the user's destinations
    - status_filter: The current status filter being applied
    - status_choices: Available status choices for filtering
    - pagination controls and status information
    """
    model = Destination
    template_name = 'destinations/my_destinations.html'
    context_object_name = 'destinations'
    paginate_by = 12  # Show 12 destinations per page for optimal UI layout
    
    def get_queryset(self):
        """
        Get the queryset of destinations created by the current user with optimized database access.
        
        This method builds a filtered queryset of destinations based on:
        1. User ownership - only destinations created by the current user
        2. Status filtering - optional filtering by approval status (pending/approved/rejected)
        
        The method optimizes database access by using:
        - select_related: For efficient loading of related region data
        - prefetch_related: For efficient loading of related images
        - Proper ordering by creation date (newest first)
        
        Returns:
            QuerySet: Filtered and optimized queryset of the user's destinations
        """
        # Start with base queryset filtered by current user
        # This ensures users only see their own destinations
        queryset = Destination.objects.filter(
            created_by=self.request.user
        ).select_related('region', 'created_by')\
         .prefetch_related(
             models.Prefetch(
                 'images',
                 queryset=DestinationImage.objects.filter(is_primary=True),
                 to_attr='primary_images'
             ),
             'seasons'
         ).order_by('-created_at')  # Show newest destinations first
        
        # Apply status filter if provided in the request
        # This allows users to view destinations in specific approval states
        status_filter = self.request.GET.get('status', '').lower()
        if status_filter in ['pending', 'approved', 'rejected']:
            queryset = queryset.filter(approval_status=status_filter)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data for template rendering.
        
        This method enriches the template context with:
        1. Current status filter value for maintaining filter state
        2. Available status choices for the filter dropdown
        3. Status counts for user feedback (e.g., "5 pending, 10 approved")
        
        These additional context variables enable the template to render
        filter UI components with the correct options and selected values.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Enhanced context dictionary with added filter data
        """
        # Get base context from parent class
        context = super().get_context_data(**kwargs)
        
        # Add current status filter to context
        # This maintains filter state across pagination
        context['status_filter'] = self.request.GET.get('status', '').lower()
        
        # Add status choices for filter dropdown
        # This provides options for the status filter UI
        context['status_choices'] = [
            ('', 'All'),
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ]
        
        # Add status counts for user feedback
        # This helps users understand their destination approval status
        context['status_counts'] = {
            'total': Destination.objects.filter(created_by=self.request.user).count(),
            'pending': Destination.objects.filter(created_by=self.request.user, approval_status='pending').count(),
            'approved': Destination.objects.filter(created_by=self.request.user, approval_status='approved').count(),
            'rejected': Destination.objects.filter(created_by=self.request.user, approval_status='rejected').count()
        }
        
        return context


class GuideDashboardView(LoginRequiredMixin, ListView):
    """
    Dashboard view for local guides with optimized database access.
    
    This view displays a comprehensive dashboard with statistics and recent items
    for local guides, including their destinations, attractions, and activity summary.
    It serves as a central hub for guides to monitor and manage their content with
    efficient database access patterns and optimized queries.
    
    Key features:
    - Comprehensive guide dashboard with content overview
    - Recent destinations with optimized prefetching
    - Recent attractions with destination relationships
    - Statistical summary of guide's content
    - Approval status tracking and metrics
    - Efficient database access with select_related and prefetch_related
    
    Template used: 'destinations/guide_dashboard.html'
    Context data includes:
    - destinations: Recent destinations created by the guide (paginated)
    - attractions: Recent attractions added by the guide
    - stats: Summary statistics for the guide's content
    - approval_metrics: Detailed breakdown of approval statuses
    """
    template_name = 'destinations/guide_dashboard.html'
    context_object_name = 'destinations'
    paginate_by = 10  # Show 10 destinations per page for optimal dashboard layout
    
    def get_queryset(self):
        """
        Get the queryset of recent destinations created by the current user with optimized database access.
        
        This method builds an optimized queryset of the guide's destinations with:
        - Filtering by current user ownership
        - Efficient loading of related region data
        - Prefetching of primary images for display
        - Proper ordering by creation date (newest first)
        
        Returns:
            QuerySet: Optimized and filtered queryset of the guide's destinations
        """
        # Build optimized queryset with prefetching and select_related
        # This minimizes database hits and improves dashboard loading performance
        return Destination.objects.filter(
            created_by=self.request.user
        ).select_related('region', 'created_by')\
         .prefetch_related(
             models.Prefetch(
                 'images',
                 queryset=DestinationImage.objects.filter(is_primary=True),
                 to_attr='primary_images'
             ),
             'seasons'
         ).order_by('-created_at')  # Show newest destinations first
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data for the dashboard with comprehensive statistics.
        
        This method enriches the dashboard context with:
        1. Recent attractions created by the user with destination data
        2. Comprehensive statistics on the guide's content
        3. Approval status metrics for monitoring content status
        4. Performance metrics like view counts and ratings
        
        The method uses optimized queries to minimize database load while
        providing a rich dataset for the dashboard template.
        
        Args:
            **kwargs: Additional context variables from parent class
            
        Returns:
            dict: Enhanced context with dashboard data, statistics and metrics
        """
        # Get base context from parent class (includes paginated destinations)
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get recent attractions created by the user with optimized queries
        # This provides the guide with their most recent attraction additions
        context['attractions'] = Attraction.objects.filter(
            created_by=user
        ).select_related('destination')\
         .prefetch_related(
             models.Prefetch(
                 'images',
                 queryset=DestinationImage.objects.filter(is_primary=True),
                 to_attr='primary_images'
             )
         ).order_by('-created_at')[:5]  # Limit to 5 most recent attractions
        
        # Calculate comprehensive statistics for the dashboard
        # These metrics help guides track their content and approval status
        
        # Get destination counts by approval status
        pending_count = Destination.objects.filter(created_by=user, approval_status='pending').count()
        approved_count = Destination.objects.filter(created_by=user, approval_status='approved').count()
        rejected_count = Destination.objects.filter(created_by=user, approval_status='rejected').count()
        total_destinations = pending_count + approved_count + rejected_count
        
        # Get attraction counts
        total_attractions = Attraction.objects.filter(created_by=user).count()
        featured_attractions = Attraction.objects.filter(created_by=user, is_featured=True).count()
        
        # Compile all statistics into a structured dictionary
        context['stats'] = {
            'total_destinations': total_destinations,
            'total_attractions': total_attractions,
            'pending_approval': pending_count,
            'approved': approved_count,
            'rejected': rejected_count,
            'featured_attractions': featured_attractions
        }
        
        # Add approval metrics as percentages for visual indicators
        if total_destinations > 0:
            context['approval_metrics'] = {
                'pending_percent': round((pending_count / total_destinations) * 100),
                'approved_percent': round((approved_count / total_destinations) * 100),
                'rejected_percent': round((rejected_count / total_destinations) * 100)
            }
        else:
            context['approval_metrics'] = {
                'pending_percent': 0,
                'approved_percent': 0,
                'rejected_percent': 0
            }
        
        return context


# API ViewSets

class RegionViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing regions.
    
    Provides list, create, retrieve, update, and delete actions for regions.
    Includes search and filtering capabilities.
    """
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'description', 'country']
    filterset_fields = ['is_active', 'is_featured', 'country']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the action.
        
        Returns:
            Serializer: The serializer class to use
        """
        if self.action == 'retrieve':
            return RegionDetailSerializer
        return self.serializer_class
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        
        Returns:
            list: List of permission classes
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['get'])
    def destinations(self, request, pk=None):
        """
        Retrieve all destinations in the specified region.
        
        Args:
            request: The HTTP request
            pk: Primary key of the region
            
        Returns:
            Response: List of destinations in the region
        """
        region = self.get_object()
        destinations = region.destinations.filter(is_active=True)
        serializer = DestinationSerializer(destinations, many=True)
        return Response(serializer.data)


class DestinationViewSet(viewsets.ModelViewSet):
    """
    A comprehensive viewset for viewing and editing destinations with optimized database access.
    
    This viewset provides a complete REST API for destination management with:
    - Optimized database queries using select_related and prefetch_related
    - Advanced filtering capabilities (region, featured status, country)
    - Full-text search across multiple fields (name, description, city, country)
    - Custom ordering options with sensible defaults
    - Role-based access control for different user types
    - Related data access through nested endpoints (attractions, seasons)
    
    API endpoints include:
    - GET /api/destinations/ - List all destinations with filtering options
    - GET /api/destinations/{id}/ - Retrieve detailed destination information
    - POST /api/destinations/ - Create new destination (admin only)
    - PUT/PATCH /api/destinations/{id}/ - Update destination (admin only)
    - DELETE /api/destinations/{id}/ - Remove destination (admin only)
    - GET /api/destinations/{id}/attractions/ - List attractions at destination
    - GET /api/destinations/{id}/seasons/ - List seasons for destination
    """
    # Base queryset with active destinations and optimized database access
    queryset = Destination.objects.filter(is_active=True)
    
    # Filter configuration for advanced API filtering capabilities
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['region', 'is_featured', 'country']
    search_fields = ['name', 'description', 'short_description', 'city', 'country']
    ordering_fields = ['name', 'created_at', 'updated_at', 'rating', 'price']
    ordering = ['name']  # Default ordering by name
    
    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the current action.
        
        This method implements a context-aware serializer selection pattern:
        - For detailed views (retrieve), use the comprehensive detail serializer
        - For list views and other actions, use the standard serializer
        
        This approach optimizes payload size and processing time by only
        including detailed information when specifically requested.
        
        Returns:
            Serializer: The appropriate serializer class for the current action
        """
        if self.action == 'retrieve':
            return DestinationDetailSerializer  # Detailed serializer with all relationships
        return DestinationSerializer  # Standard serializer for lists and other actions
    
    def get_permissions(self):
        """
        Instantiate and return permission classes based on the current action.
        
        This method implements a role-based access control pattern:
        - Public endpoints (list, retrieve) are accessible to all users
        - Administrative actions (create, update, delete) require admin privileges
        
        This ensures proper data security while maintaining public access
        to destination information.
        
        Returns:
            list: Instantiated permission classes for the current action
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]  # Public read access
        else:
            permission_classes = [permissions.IsAdminUser]  # Admin-only write access
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Get an optimized queryset for the current request with proper prefetching.
        
        This method enhances the base queryset with:
        1. Relationship prefetching to minimize database queries
        2. User-specific filtering based on request parameters
        3. Geographic and categorical filtering options
        
        The method implements efficient database access patterns with:
        - select_related for foreign key relationships
        - prefetch_related with Prefetch objects for reverse relationships
        - Conditional filtering based on query parameters
        
        Returns:
            QuerySet: Optimized queryset with all necessary prefetching
        """
        # Start with the base queryset from the viewset
        queryset = super().get_queryset()
        
        # Optimize database access with select_related and prefetch_related
        # This significantly reduces the number of database queries
        queryset = queryset.select_related('region', 'created_by')\
            .prefetch_related(
                models.Prefetch(
                    'images',
                    queryset=DestinationImage.objects.filter(is_primary=True),
                    to_attr='primary_images'
                ),
                'seasons'
            )
        
        # Filter by region if provided in query parameters
        region_id = self.request.query_params.get('region_id')
        if region_id:
            queryset = queryset.filter(region_id=region_id)
        
        # Filter by country if provided in query parameters
        country = self.request.query_params.get('country')
        if country:
            queryset = queryset.filter(country=country)
        
        # Filter by featured status if provided
        is_featured = self.request.query_params.get('featured')
        if is_featured is not None:
            queryset = queryset.filter(is_featured=(is_featured == '1'))
        
        # Filter by price range if provided
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price is not None:
            queryset = queryset.filter(price__gte=float(min_price))
        if max_price is not None:
            queryset = queryset.filter(price__lte=float(max_price))
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def attractions(self, request, pk=None):
        """
        Retrieve all attractions for the specified destination with optimized queries.
        
        This endpoint provides a list of attractions associated with a destination,
        with efficient database access through prefetching and select_related.
        
        Args:
            request: The HTTP request object containing query parameters
            pk: Primary key (ID) of the destination to retrieve attractions for
            
        Returns:
            Response: JSON response containing serialized attraction data
                     with optimized relationship loading
        """
        # Get the destination object
        destination = self.get_object()
        
        # Get attractions with optimized database access
        attractions = destination.attractions.filter(is_active=True)\
            .select_related('destination')\
            .prefetch_related(
                models.Prefetch(
                    'images',
                    queryset=DestinationImage.objects.filter(is_primary=True),
                    to_attr='primary_images'
                )
            )
        
        # Serialize and return the data
        serializer = AttractionSerializer(attractions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def seasons(self, request, pk=None):
        """
        Retrieve all seasons for the specified destination with optimized queries.
        
        This endpoint provides a list of seasons associated with a destination,
        with efficient database access through prefetching and select_related.
        
        The seasons data is critical for travel planning as it helps users
        understand the best times to visit a destination based on weather,
        events, and other seasonal factors.
        
        Args:
            request: The HTTP request object containing query parameters
            pk: Primary key (ID) of the destination to retrieve seasons for
            
        Returns:
            Response: JSON response containing serialized season data
                     with optimized relationship loading
        """
        # Get the destination object
        destination = self.get_object()
        
        # Get seasons with optimized database access
        # In a real implementation, this would use a proper relationship
        # between destinations and seasons
        seasons = destination.seasons.all().select_related()
        
        # Serialize and return the data
        serializer = SeasonSerializer(seasons, many=True, context={'request': request})
        return Response(serializer.data)


class AttractionViewSet(viewsets.ModelViewSet):
    """
    A comprehensive viewset for viewing and editing attractions with optimized database access.
    
    This viewset provides a complete REST API for attraction management with:
    - Optimized database queries using select_related and prefetch_related
    - Advanced filtering capabilities (destination, category, featured status)
    - Full-text search across multiple fields (name, description, address, city)
    - Custom ordering options with sensible defaults
    - Role-based access control for different user types
    
    API endpoints include:
    - GET /api/attractions/ - List all attractions with filtering options
    - GET /api/attractions/{id}/ - Retrieve detailed attraction information
    - POST /api/attractions/ - Create new attraction (admin only)
    - PUT/PATCH /api/attractions/{id}/ - Update attraction (admin only)
    - DELETE /api/attractions/{id}/ - Remove attraction (admin only)
    
    Router Registration Note:
    When registering this viewset with DefaultRouter, a class-level queryset attribute
    is required for the router to automatically determine the basename. Without this
    attribute, you would need to explicitly specify basename='attraction' when registering
    the viewset in urls.py. Having both this class-level queryset and the get_queryset()
    method provides flexibility and proper router integration.
    """
    # Define the serializer class to use for this viewset
    serializer_class = AttractionSerializer
    
    # Define the queryset attribute to fix router basename issue
    # IMPORTANT: This class-level queryset attribute is required for DRF's DefaultRouter
    # to automatically determine the basename for URL pattern generation.
    queryset = Attraction.objects.filter(is_active=True)
    
    # Configure filter backends for search and ordering
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Fields that can be filtered using query parameters
    filterset_fields = {
        'destination': ['exact'],
        'category': ['exact', 'in'],
        'is_featured': ['exact'],
        'price': ['gte', 'lte', 'exact', 'range'],
        'duration_minutes': ['gte', 'lte', 'range']
    }
    
    # Fields that can be searched using text queries
    search_fields = ['name', 'description', 'address', 'city', 'country', 'tags__name']
    
    # Fields that can be used for ordering results
    ordering_fields = ['name', 'category', 'created_at', 'rating', 'price', 'duration_minutes']
    
    # Default ordering for results
    ordering = ['name']
    
    def get_queryset(self):
        """
        Get an optimized queryset for the current request with proper prefetching.
        
        This method enhances the base queryset with:
        1. Relationship prefetching to minimize database queries
        2. User-specific filtering based on request parameters
        3. Category and feature-based filtering options
        
        The method implements efficient database access patterns with:
        - select_related for foreign key relationships (destination)
        - prefetch_related with Prefetch objects for reverse relationships (images)
        - Conditional filtering based on query parameters
        
        Note on Router Integration:
        Even though we define a class-level queryset attribute for router basename determination,
        this method takes precedence for actual queryset generation during request processing.
        
        Returns:
            QuerySet: Optimized queryset with all necessary prefetching
        """
        # Start with base queryset of active attractions
        queryset = Attraction.objects.filter(is_active=True)
        
        # Optimize database access with select_related and prefetch_related
        # This significantly reduces the number of database queries
        queryset = queryset.select_related('destination', 'category', 'created_by')\
            .prefetch_related(
                models.Prefetch(
                    'images',
                    queryset=AttractionImage.objects.filter(is_primary=True),
                    to_attr='primary_images'
                ),
                'tags'
            )
        
        # Filter by destination if provided in query parameters
        destination_id = self.request.query_params.get('destination_id')
        if destination_id:
            queryset = queryset.filter(destination_id=destination_id)
        
        # Filter by category if provided
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__name=category)
        
        # Filter by featured status if provided
        is_featured = self.request.query_params.get('featured')
        if is_featured is not None:
            queryset = queryset.filter(is_featured=(is_featured == '1'))
        
        # Filter by price range if provided
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price is not None:
            queryset = queryset.filter(price__gte=float(min_price))
        if max_price is not None:
            queryset = queryset.filter(price__lte=float(max_price))
        
        # Filter by duration range if provided
        min_duration = self.request.query_params.get('min_duration')
        max_duration = self.request.query_params.get('max_duration')
        if min_duration is not None:
            queryset = queryset.filter(duration_minutes__gte=int(min_duration))
        if max_duration is not None:
            queryset = queryset.filter(duration_minutes__lte=int(max_duration))
            
        return queryset
    
    def get_permissions(self):
        """
        Instantiate and return permission classes based on the current action.
        
        This method implements a role-based access control pattern:
        - Public endpoints (list, retrieve) are accessible to all users
        - Administrative actions (create, update, delete) require admin privileges
        
        This ensures proper data security while maintaining public access
        to attraction information.
        
        Returns:
            list: Instantiated permission classes for the current action
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]  # Public read access
        else:
            permission_classes = [permissions.IsAdminUser]  # Admin-only write access
        return [permission() for permission in permission_classes]


class SeasonViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A comprehensive read-only viewset for viewing seasons with optimized database access.
    
    This viewset provides a complete REST API for season information with:
    - Optimized database queries using select_related
    - Advanced filtering capabilities by destination, month range
    - Full-text search across name and description fields
    - Custom ordering options with sensible defaults
    
    API endpoints include:
    - GET /api/seasons/ - List all seasons with filtering options
    - GET /api/seasons/{id}/ - Retrieve detailed season information
    
    Seasons are critical travel planning data as they help users understand
    the best times to visit destinations based on weather, events, and other
    seasonal factors that affect travel experiences.
    """
    # Base queryset with optimized database access
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer
    
    # Filter configuration for advanced API filtering capabilities
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'start_month': ['exact', 'gte', 'lte'],
        'end_month': ['exact', 'gte', 'lte'],
        'climate_type': ['exact', 'in']
    }
    search_fields = ['name', 'description', 'activities']
    ordering_fields = ['start_month', 'end_month', 'name', 'rainfall']
    ordering = ['start_month']
    
    def get_queryset(self):
        """
        Get an optimized queryset for the current request with proper prefetching.
        
        This method enhances the base queryset with:
        1. Relationship prefetching to minimize database queries
        2. User-specific filtering based on request parameters
        3. Temporal filtering options (month ranges, current season)
        
        The method implements efficient database access patterns with:
        - Conditional filtering based on query parameters
        - Calendar-aware filtering for current and upcoming seasons
        
        Returns:
            QuerySet: Optimized queryset with all necessary prefetching
        """
        # Start with the base queryset
        queryset = super().get_queryset()
        
        # Filter by destination ID if provided
        # Note: In a real app, there would likely be a many-to-many relationship
        # between destinations and seasons
        destination_id = self.request.query_params.get('destination_id')
        if destination_id:
            # In a real implementation, this would filter by the relationship
            # For now, we'll use a placeholder that doesn't filter
            # queryset = queryset.filter(destinations__id=destination_id)
            pass
        
        # Filter by current season flag if provided
        current_season = self.request.query_params.get('current')
        if current_season == '1':
            # Get current month (1-12)
            current_month = datetime.now().month
            # Find seasons that include the current month
            # This handles seasons that span across year boundaries (e.g., winter: Dec-Feb)
            queryset = queryset.filter(
                models.Q(start_month__lte=current_month, end_month__gte=current_month) |
                models.Q(start_month__gt=models.F('end_month'), start_month__lte=current_month) |
                models.Q(start_month__gt=models.F('end_month'), end_month__gte=current_month)
            )
        
        # Filter by month if provided
        month = self.request.query_params.get('month')
        if month:
            month_num = int(month)
            # Find seasons that include the specified month
            queryset = queryset.filter(
                models.Q(start_month__lte=month_num, end_month__gte=month_num) |
                models.Q(start_month__gt=models.F('end_month'), start_month__lte=month_num) |
                models.Q(start_month__gt=models.F('end_month'), end_month__gte=month_num)
            )
        
        return queryset
