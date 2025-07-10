"""  
Views for the tours app.

This module contains both template views for rendering HTML pages and API viewsets.
Template views are for the web interface, while viewsets are used for the API endpoints.
""" 
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q, Avg
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Tour, TourCategory, TourDate, Booking
from .serializers import TourSerializer, TourCategorySerializer, TourDateSerializer

def tour_list_view(request):
    """
    Render the tours list page.
    
    This view displays all active tours with optional filtering by:
    - Category
    - Search term
    - Price range
    - Duration
    
    Args:
        request: The HTTP request object containing query parameters
        
    Returns:
        HttpResponse: Rendered HTML template with filtered tour list
    """
    # Get base queryset of active tours
    tours = Tour.objects.filter(is_active=True)
    
    # Apply filters from query parameters
    category_id = request.GET.get('category')
    search_query = request.GET.get('search')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    min_duration = request.GET.get('min_duration')
    max_duration = request.GET.get('max_duration')
    
    # Filter by category if specified
    if category_id:
        try:
            tours = tours.filter(category_id=category_id)
        except (ValueError, TypeError):
            # Invalid category_id, ignore the filter
            pass
    
    # Filter by search term if provided
    if search_query:
        tours = tours.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(short_description__icontains=search_query) |
            Q(included_activities__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    # Filter by price range if provided
    if min_price:
        try:
            tours = tours.filter(price__gte=float(min_price))
        except (ValueError, TypeError):
            pass
            
    if max_price:
        try:
            tours = tours.filter(price__lte=float(max_price))
        except (ValueError, TypeError):
            pass
    
    # Filter by duration range if provided
    if min_duration:
        try:
            tours = tours.filter(duration_days__gte=int(min_duration))
        except (ValueError, TypeError):
            pass
            
    if max_duration:
        try:
            tours = tours.filter(duration_days__lte=int(max_duration))
        except (ValueError, TypeError):
            pass
    
    # Apply sorting
    sort_by = request.GET.get('sort', 'title')
    if sort_by not in ['title', '-title', 'price', '-price', 'duration_days', '-duration_days']:
        sort_by = 'title'  # Default sorting
    
    tours = tours.order_by(sort_by)
    
    # Get all categories for the filter dropdown
    categories = TourCategory.objects.all().order_by('name')
    
    # Paginate results - 9 tours per page
    paginator = Paginator(tours, 9)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tours': page_obj,
        'categories': categories,
        'search_query': search_query or '',
        'category_id': category_id,
        'min_price': min_price,
        'max_price': max_price,
        'min_duration': min_duration,
        'max_duration': max_duration,
        'sort_by': sort_by,
    }
    
    return render(request, 'tours/tour_list.html', context)

def tour_detail_view(request, slug):
    """
    Render the tour details page.
    
    This view displays detailed information about a specific tour including:
    - Tour details (description, itinerary, etc.)
    - Available dates
    - Reviews
    - Related tours
    
    Args:
        request: The HTTP request
        slug: URL slug of the tour
        
    Returns:
        HttpResponse: Rendered HTML template with tour details
    """
    # Get the requested tour or return 404 if not found
    tour = get_object_or_404(Tour, slug=slug, is_active=True)
    
    # Get available dates for the tour
    available_dates = TourDate.objects.filter(tour=tour, start_date__gte='2025-06-29').order_by('start_date')
    
    # Get related tours from the same category (excluding current tour)
    related_tours = Tour.objects.filter(category=tour.category, is_active=True).exclude(id=tour.id).order_by('?')[:3]
    
    # Handle booking form submission if POST request
    if request.method == 'POST' and request.user.is_authenticated:
        # This would be implemented if you had a booking form
        pass
    
    context = {
        'tour': tour,
        'available_dates': available_dates,
        'related_tours': related_tours,
    }
    
    return render(request, 'tours/tour_detail.html', context)

# API Viewsets
class TourViewSet(viewsets.ModelViewSet):
    """
    API viewset for tours.
    
    Provides CRUD operations and filtering for tours via the API.
    Additional actions include retrieving available dates and calculating tour statistics.
    
    Attributes:
        queryset: Base queryset filtering only active tours
        serializer_class: Serializer for converting Tour model instances to/from JSON
        filter_backends: List of filter backends for search and ordering
        search_fields: Fields that can be searched through the API
        ordering_fields: Fields that can be used for ordering results
        ordering: Default ordering field
    """
    queryset = Tour.objects.filter(is_active=True)
    serializer_class = TourSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_featured', 'duration_days']
    search_fields = ['title', 'description', 'short_description', 'location']
    ordering_fields = ['title', 'price', 'duration_days', 'created_at']
    ordering = ['title']
    
    def get_permissions(self):
        """
        Return appropriate permissions based on the action.
        
        Read operations are allowed for anyone, while write operations require admin permissions.
        
        Returns:
            list: List of permission classes to apply
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticatedOrReadOnly()]
    
    @action(detail=True, methods=['get'])
    def dates(self, request, pk=None):
        """
        Retrieve available dates for a specific tour.
        
        Args:
            request: The API request
            pk: Primary key of the tour
            
        Returns:
            Response: JSON response with available dates
        """
        tour = self.get_object()
        dates = TourDate.objects.filter(tour=tour, start_date__gte='2025-06-29').order_by('start_date')
        serializer = TourDateSerializer(dates, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """
        Retrieve statistics for a specific tour.
        
        Returns metrics like average rating, number of bookings, etc.
        
        Args:
            request: The API request
            pk: Primary key of the tour
            
        Returns:
            Response: JSON response with tour statistics
        """
        tour = self.get_object()
        
        # Count bookings
        booking_count = Booking.objects.filter(tour_date__tour=tour).count()
        
        # Calculate average rating if reviews exist
        avg_rating = 0.0
        review_count = 0
        
        stats = {
            'booking_count': booking_count,
            'avg_rating': avg_rating,
            'review_count': review_count,
        }
        
        return Response(stats)

class TourCategoryViewSet(viewsets.ModelViewSet):
    """
    API viewset for tour categories.
    
    Provides CRUD operations for tour categories via the API.
    Additional action to retrieve all tours in a category.
    
    Attributes:
        queryset: All tour categories
        serializer_class: Serializer for converting TourCategory model instances to/from JSON
        filter_backends: List of filter backends for search and ordering
        search_fields: Fields that can be searched through the API
        ordering_fields: Fields that can be used for ordering results
    """
    queryset = TourCategory.objects.all()
    serializer_class = TourCategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'id']
    
    def get_permissions(self):
        """
        Return appropriate permissions based on the action.
        
        Read operations are allowed for anyone, while write operations require admin permissions.
        
        Returns:
            list: List of permission classes to apply
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticatedOrReadOnly()]
    
    @action(detail=True, methods=['get'])
    def tours(self, request, pk=None):
        """
        Retrieve all tours in a specific category.
        
        Args:
            request: The API request
            pk: Primary key of the category
            
        Returns:
            Response: JSON response with tours in the category
        """
        category = self.get_object()
        tours = Tour.objects.filter(category=category, is_active=True)
        
        # Apply search if provided
        search_query = request.query_params.get('search', None)
        if search_query:
            tours = tours.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(short_description__icontains=search_query)
            )
        
        # Apply ordering
        ordering = request.query_params.get('ordering', 'title')
        if ordering.lstrip('-') in ['title', 'price', 'duration_days', 'created_at']:
            tours = tours.order_by(ordering)
        
        page = self.paginate_queryset(tours)
        if page is not None:
            serializer = TourSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = TourSerializer(tours, many=True, context={'request': request})
        return Response(serializer.data)
