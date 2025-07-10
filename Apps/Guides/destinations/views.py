"""
Views for the destinations app.

This module contains views for handling API endpoints related to destinations,
regions, and attractions, as well as template views for the web interface.
"""
from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, F
from math import radians, sin, cos, sqrt, atan2
from django.db.models.functions import Radians, Sin, Cos, ATan2, Sqrt, Radians
from django.db.models.expressions import RawSQL
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import connection
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator

from .models import Region, Destination, Attraction, Season, DestinationImage
from .serializers import (
    RegionSerializer, RegionDetailSerializer,
    DestinationSerializer, DestinationDetailSerializer,
    AttractionSerializer, SeasonSerializer
)

def destination_list_view(request):
    """
    Render the destinations list page.
    
    This view displays all active destinations with optional filtering by:
    - Region
    - Search term
    - Featured status
    """
    # Get base queryset of active destinations
    destinations = Destination.objects.filter(is_active=True)
    
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
    
    Args:
        request: The HTTP request
        slug: The slug of the destination to display
        
    Returns:
        HttpResponse: Rendered template with destination details
    """
    destination = get_object_or_404(Destination, slug=slug, is_active=True)
    
    # Get related attractions
    attractions = destination.attractions.filter(is_active=True)
    
    # Get all images for the destination
    images = destination.images.all()
    
    # Get the main image (first image) for the hero section
    main_image = images.first()
    
    context = {
        'destination': destination,
        'attractions': attractions,
        'images': images,
        'main_image': main_image,
    }
    
    return render(request, 'destinations/destination_detail.html', context)


class RegionDetailView(DetailView):
    """
    Display details for a single region.
    """
    model = Region
    template_name = 'destinations/region_detail.html'
    context_object_name = 'region'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return Region.objects.filter(is_active=True)


class DestinationListView(ListView):
    """
    Display a list of destinations with filtering and pagination.
    """
    model = Destination
    template_name = 'destinations/destination_list.html'
    context_object_name = 'destinations'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Destination.objects.filter(is_active=True)
        
        # Apply filters from query parameters
        region_slug = self.request.GET.get('region')
        search_query = self.request.GET.get('search')
        featured_only = self.request.GET.get('featured') == '1'
        
        if region_slug:
            queryset = queryset.filter(region__slug=region_slug, region__is_active=True)
        
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(short_description__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(city__icontains=search_query) |
                Q(country__icontains=search_query)
            )
        
        if featured_only:
            queryset = queryset.filter(is_featured=True)
        
        return queryset.select_related('region')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['regions'] = Region.objects.filter(is_active=True)
        context['selected_region'] = self.request.GET.get('region')
        context['search_query'] = self.request.GET.get('search', '')
        context['featured_only'] = self.request.GET.get('featured') == '1'
        return context


class DestinationDetailView(DetailView):
    """
    Display details for a single destination.
    """
    model = Destination
    template_name = 'destinations/destination_detail.html'
    context_object_name = 'destination'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return Destination.objects.filter(is_active=True).select_related('region')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        destination = self.get_object()
        
        # Get related data
        context['attractions'] = destination.attractions.filter(is_active=True)
        context['images'] = destination.images.all()
        context['main_image'] = context['images'].first()
        
        # Get related destinations (from the same region)
        context['related_destinations'] = Destination.objects.filter(
            region=destination.region,
            is_active=True
        ).exclude(id=destination.id)[:4]
        
        return context


class AttractionListView(ListView):
    """
    Display a list of attractions with filtering and pagination.
    """
    model = Attraction
    template_name = 'destinations/attraction_list.html'
    context_object_name = 'attractions'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Attraction.objects.filter(is_active=True)
        
        # Apply filters from query parameters
        destination_slug = self.request.GET.get('destination')
        search_query = self.request.GET.get('search')
        
        if destination_slug:
            queryset = queryset.filter(destination__slug=destination_slug, destination__is_active=True)
        
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(address__icontains=search_query) |
                Q(city__icontains=search_query) |
                Q(country__icontains=search_query)
            )
        
        return queryset.select_related('destination')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['destinations'] = Destination.objects.filter(is_active=True)
        context['selected_destination'] = self.request.GET.get('destination')
        context['search_query'] = self.request.GET.get('search', '')
        return context


class AttractionDetailView(DetailView):
    """
    Display details for a single attraction.
    """
    model = Attraction
    template_name = 'destinations/attraction_detail.html'
    context_object_name = 'attraction'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return Attraction.objects.filter(is_active=True).select_related('destination')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attraction = self.get_object()
        
        # Get related attractions (from the same destination)
        context['related_attractions'] = Attraction.objects.filter(
            destination=attraction.destination,
            is_active=True
        ).exclude(id=attraction.id)[:4]
        
        return context


@require_http_methods(["GET"])
def nearby_destinations(request):
    """
    Find destinations within a specified radius (in kilometers) of a given latitude and longitude.
    
    Query Parameters:
    - lat: Latitude of the center point (required)
    - lng: Longitude of the center point (required)
    - radius: Search radius in kilometers (default: 10)
    - limit: Maximum number of results to return (default: 6)
    
    Returns:
        JsonResponse: List of nearby destinations with distance information
    """
    try:
        # Get parameters from request
        lat = float(request.GET.get('lat', 0))
        lng = float(request.GET.get('lng', 0))
        radius_km = float(request.GET.get('radius', 15))  # Default 15km radius
        limit = int(request.GET.get('limit', 6))  # Default to 6 results
        
        # Convert radius from km to degrees (approximate)
        radius_deg = radius_km / 111.32
        
        # Calculate bounding box for initial filtering (performance optimization)
        min_lat = lat - radius_deg
        max_lat = lat + radius_deg
        min_lng = lng - (radius_deg / abs(cos(radians(lat)) if abs(cos(radians(lat))) > 0 else 1))
        max_lng = lng + (radius_deg / abs(cos(radians(lat)) if abs(cos(radians(lat))) > 0 else 1))
        
        # Get destinations within the bounding box
        destinations = Destination.objects.filter(
            latitude__gte=min_lat,
            latitude__lte=max_lat,
            longitude__gte=min_lng,
            longitude__lte=max_lng,
            is_active=True
        )
        
        # Calculate exact distance using Haversine formula for each destination
        nearby_dests = []
        for dest in destinations:
            # Skip if missing coordinates
            if not dest.latitude or not dest.longitude:
                continue
                
            # Calculate distance using Haversine formula
            dlat = radians(dest.latitude - lat)
            dlng = radians(dest.longitude - lng)
            a = (sin(dlat/2) * sin(dlat/2) + 
                 cos(radians(lat)) * cos(radians(dest.latitude)) * 
                 sin(dlng/2) * sin(dlng/2))
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            distance_km = 6371 * c  # Earth's radius in km
            
            # Add to results if within radius
            if distance_km <= radius_km:
                nearby_dests.append({
                    'id': dest.id,
                    'name': dest.name,
                    'slug': dest.slug,
                    'city': dest.city,
                    'country': dest.country,
                    'short_description': dest.short_description,
                    'distance_km': round(distance_km, 1),
                    'latitude': dest.latitude,
                    'longitude': dest.longitude,
                    'image': dest.images.filter(is_primary=True).first().image.url if dest.images.filter(is_primary=True).exists() else None
                })
        
        # Sort by distance and limit results
        nearby_dests = sorted(nearby_dests, key=lambda x: x['distance_km'])[:limit]
        
        return JsonResponse({
            'status': 'success',
            'count': len(nearby_dests),
            'results': nearby_dests
        })
        
    except (ValueError, TypeError) as e:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid parameters. Please provide valid latitude and longitude.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


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
        return RegionSerializer
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        
        Returns:
            list: List of permission classes
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticatedOrReadOnly()]
    
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
        
        # Apply search if provided
        search_query = request.query_params.get('search', None)
        if search_query:
            destinations = destinations.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(short_description__icontains=search_query)
            )
        
        # Apply ordering
        ordering = request.query_params.get('ordering', 'name')
        if ordering.lstrip('-') in ['name', 'created_at']:
            destinations = destinations.order_by(ordering)
        
        page = self.paginate_queryset(destinations)
        if page is not None:
            serializer = DestinationSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = DestinationSerializer(destinations, many=True, context={'request': request})
        return Response(serializer.data)

class DestinationViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing destinations.
    
    Provides list, create, retrieve, update, and delete actions for destinations.
    Includes search, filtering, and geographic querying capabilities.
    """
    queryset = Destination.objects.filter(is_active=True)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['region', 'is_featured']
    search_fields = ['name', 'description', 'short_description', 'city', 'country']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the action.
        
        Returns:
            Serializer: The serializer class to use
        """
        if self.action == 'retrieve':
            return DestinationDetailSerializer
        return DestinationSerializer
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        
        Returns:
            list: List of permission classes
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticatedOrReadOnly()]
    
    def get_queryset(self):
        """
        Get the list of items for this view.
        
        This can be further filtered by query parameters.
        
        Returns:
            QuerySet: The filtered queryset
        """
        queryset = super().get_queryset()
        
        # Filter by proximity if lat/lng and distance are provided
        latitude = self.request.query_params.get('lat')
        longitude = self.request.query_params.get('lng')
        distance = self.request.query_params.get('distance', 50)  # Default 50km
        
        if latitude and longitude:
            try:
                point = Point(float(longitude), float(latitude), srid=4326)
                # Convert distance from km to meters (Django's default unit)
                distance_meters = float(distance) * 1000
                queryset = queryset.filter(
                    location__distance_lte=(point, distance_meters)
                ).distance(point).order_by('distance')
            except (ValueError, TypeError):
                # If lat/lng are invalid, just return the unfiltered queryset
                pass
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def attractions(self, request, pk=None):
        """
        Retrieve all attractions for the specified destination.
        
        Args:
            request: The HTTP request
            pk: Primary key of the destination
            
        Returns:
            Response: List of attractions at the destination
        """
        destination = self.get_object()
        attractions = destination.attractions.all()
        
        # Apply search if provided
        search_query = request.query_params.get('search', None)
        if search_query:
            attractions = attractions.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(category__icontains=search_query)
            )
        
        # Apply category filter if provided
        category = request.query_params.get('category', None)
        if category:
            attractions = attractions.filter(category=category)
        
        # Apply featured filter if provided
        is_featured = request.query_params.get('featured', None)
        if is_featured is not None:
            is_featured = is_featured.lower() in ('true', '1', 'yes')
            attractions = attractions.filter(is_featured=is_featured)
        
        # Apply ordering
        ordering = request.query_params.get('ordering', 'name')
        if ordering.lstrip('-') in ['name', 'created_at', 'category']:
            attractions = attractions.order_by(ordering)
        
        page = self.paginate_queryset(attractions)
        if page is not None:
            serializer = AttractionSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = AttractionSerializer(attractions, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def seasons(self, request, pk=None):
        """
        Retrieve all seasons for the specified destination.
        
        Args:
            request: The HTTP request
            pk: Primary key of the destination
            
        Returns:
            Response: List of seasons for the destination
        """
        destination = self.get_object()
        seasons = destination.seasons.all()
        
        # Apply peak season filter if provided
        is_peak = request.query_params.get('peak', None)
        if is_peak is not None:
            is_peak = is_peak.lower() in ('true', '1', 'yes')
            seasons = seasons.filter(is_peak_season=is_peak)
        
        # Apply ordering
        ordering = request.query_params.get('ordering', 'start_month')
        if ordering.lstrip('-') in ['name', 'start_month', 'end_month']:
            seasons = seasons.order_by(ordering)
        
        page = self.paginate_queryset(seasons)
        if page is not None:
            serializer = SeasonSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = SeasonSerializer(seasons, many=True)
        return Response(serializer.data)

class AttractionViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing attractions.
    
    Provides list, create, retrieve, update, and delete actions for attractions.
    Includes search and filtering capabilities.
    """
    serializer_class = AttractionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['destination', 'category', 'is_featured']
    search_fields = ['name', 'description', 'address', 'city', 'country']
    ordering_fields = ['name', 'category', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """
        Get the list of items for this view.
        
        This can be further filtered by query parameters.
        
        Returns:
            QuerySet: The filtered queryset
        """
        queryset = Attraction.objects.all()
        
        # Filter by proximity if lat/lng and distance are provided
        latitude = self.request.query_params.get('lat')
        longitude = self.request.query_params.get('lng')
        distance = self.request.query_params.get('distance', 10)  # Default 10km
        
        if latitude and longitude:
            try:
                point = Point(float(longitude), float(latitude), srid=4326)
                # Convert distance from km to meters (Django's default unit)
                distance_meters = float(distance) * 1000
                queryset = queryset.filter(
                    location__distance_lte=(point, distance_meters)
                ).distance(point).order_by('distance')
            except (ValueError, TypeError):
                # If lat/lng are invalid, just return the unfiltered queryset
                pass
        
        return queryset
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        
        Returns:
            list: List of permission classes
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticatedOrReadOnly()]

class SeasonViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A read-only viewset for viewing seasons.
    
    Provides list and retrieve actions for seasons.
    """
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['start_month', 'end_month', 'name']
    ordering = ['start_month']
    
    def get_queryset(self):
        """
        Get the list of items for this view.
        
        This can be further filtered by destination_id.
        
        Returns:
            QuerySet: The filtered queryset
        """
        queryset = super().get_queryset()
        
        # Filter by destination if provided
        destination_id = self.request.query_params.get('destination')
        if destination_id:
            queryset = queryset.filter(destination_id=destination_id)
        
        # Filter by peak season if provided
        is_peak = self.request.query_params.get('peak')
        if is_peak is not None:
            is_peak = is_peak.lower() in ('true', '1', 'yes')
            queryset = queryset.filter(is_peak_season=is_peak)
        
        return queryset
