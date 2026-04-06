"""
Views for the transportation app.

This module defines view functions and classes for handling
transportation-related HTTP requests, including displaying and
managing transportation types, providers, routes, and schedules.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Q, Count, Avg
from django.http import JsonResponse
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.http import require_POST, require_GET

from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from destinations.models import Destination
from .models import (
    TransportationType, TransportationProvider, Route,
    Schedule, TransportationOption, TransportationImage
)
from .serializers import (
    TransportationTypeSerializer, 
    TransportationProviderListSerializer,
    TransportationProviderDetailSerializer,
    RouteListSerializer, 
    RouteDetailSerializer,
    ScheduleSerializer, 
    ScheduleDetailSerializer,
    TransportationOptionSerializer,
    TransportationOptionDetailSerializer,
    TransportationImageSerializer
)


# Web Views
class TransportationTypeListView(ListView):
    """
    Display a list of transportation types.
    
    Renders a template with all active transportation types.
    """
    model = TransportationType
    template_name = 'transportation/type_list.html'
    context_object_name = 'types'
    queryset = TransportationType.objects.filter(is_active=True)


class TransportationTypeDetailView(DetailView):
    """
    Display details of a specific transportation type.
    
    Shows detailed information about a transportation type,
    including related routes, providers, and images.
    """
    model = TransportationType
    template_name = 'transportation/type_detail.html'
    context_object_name = 'type'
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        
        Adds routes, providers, and images associated with this type.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with added data
        """
        context = super().get_context_data(**kwargs)
        
        # Get routes using this transportation type
        context['routes'] = self.object.routes.filter(is_active=True)[:10]
        
        # Get providers offering this transportation type
        context['providers'] = self.object.providers.filter(is_active=True)[:10]
        
        # Get images
        content_type = ContentType.objects.get_for_model(TransportationType)
        context['images'] = TransportationImage.objects.filter(
            content_type=content_type,
            object_id=self.object.id
        )
        
        return context


class ProviderListView(ListView):
    """
    Display a list of transportation providers.
    
    Renders a template with transportation providers,
    with optional filtering by transportation type.
    """
    model = TransportationProvider
    template_name = 'transportation/provider_list.html'
    context_object_name = 'providers'
    
    def get_queryset(self):
        """
        Get the list of providers with optional filtering.
        
        Returns:
            QuerySet: Filtered queryset of providers
        """
        queryset = TransportationProvider.objects.filter(is_active=True)
        
        # Filter by transportation type if provided
        type_slug = self.request.GET.get('type')
        if type_slug:
            queryset = queryset.filter(transportation_types__slug=type_slug)
        
        # Filter by partner status if requested
        partners_only = self.request.GET.get('partners')
        if partners_only == 'true':
            queryset = queryset.filter(is_partner=True)
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        
        Adds filter parameters to context.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with added data
        """
        context = super().get_context_data(**kwargs)
        context['type_slug'] = self.request.GET.get('type')
        context['partners_only'] = self.request.GET.get('partners') == 'true'
        
        # Add list of transportation types for filtering
        context['transportation_types'] = TransportationType.objects.filter(is_active=True)
        
        return context


class ProviderDetailView(DetailView):
    """
    Display details of a specific transportation provider.
    
    Shows detailed information about a transportation provider,
    including services, routes, and images.
    """
    model = TransportationProvider
    template_name = 'transportation/provider_detail.html'
    context_object_name = 'provider'
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        
        Adds routes, schedules, and images associated with this provider.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with added data
        """
        context = super().get_context_data(**kwargs)
        
        # Get routes served by this provider
        context['routes'] = self.object.routes.filter(is_active=True)[:15]
        
        # Get schedules operated by this provider
        context['schedules'] = self.object.schedules.filter(is_active=True)[:20]
        
        # Get transportation types offered
        context['transportation_types'] = self.object.transportation_types.filter(is_active=True)
        
        # Get images
        content_type = ContentType.objects.get_for_model(TransportationProvider)
        context['images'] = TransportationImage.objects.filter(
            content_type=content_type,
            object_id=self.object.id
        )
        
        return context


class RouteListView(ListView):
    """
    Display a list of transportation routes.
    
    Renders a template with routes, with filtering options for
    origin, destination, and transportation types.
    """
    model = Route
    template_name = 'transportation/route_list.html'
    context_object_name = 'routes'
    paginate_by = 20
    
    def get_queryset(self):
        """
        Get the list of routes with filtering.
        
        Filters by origin, destination, and transportation type.
        
        Returns:
            QuerySet: Filtered queryset of routes
        """
        queryset = Route.objects.filter(is_active=True)
        
        # Filter by origin if provided
        origin_id = self.request.GET.get('origin')
        if origin_id and origin_id.isdigit():
            queryset = queryset.filter(origin_id=origin_id)
        
        # Filter by destination if provided
        destination_id = self.request.GET.get('destination')
        if destination_id and destination_id.isdigit():
            queryset = queryset.filter(destination_id=destination_id)
        
        # Filter by transportation type if provided
        type_id = self.request.GET.get('type')
        if type_id and type_id.isdigit():
            queryset = queryset.filter(transportation_types__id=type_id)
        
        # Filter by provider if provided
        provider_id = self.request.GET.get('provider')
        if provider_id and provider_id.isdigit():
            queryset = queryset.filter(providers__id=provider_id)
        
        # Popular routes first, then by name
        sort = self.request.GET.get('sort', 'popular')
        if sort == 'popular':
            queryset = queryset.order_by('-is_popular', 'origin__name', 'destination__name')
        elif sort == 'distance':
            queryset = queryset.order_by('distance_km')
        else:
            queryset = queryset.order_by('origin__name', 'destination__name')
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        
        Adds filter parameters and filter options to context.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with added data
        """
        context = super().get_context_data(**kwargs)
        
        # Add filter parameters to context
        context['origin_id'] = self.request.GET.get('origin')
        context['destination_id'] = self.request.GET.get('destination')
        context['type_id'] = self.request.GET.get('type')
        context['provider_id'] = self.request.GET.get('provider')
        context['sort'] = self.request.GET.get('sort', 'popular')
        
        # Add filter options
        context['destinations'] = Destination.objects.filter(is_active=True).order_by('name')
        context['transportation_types'] = TransportationType.objects.filter(is_active=True)
        context['providers'] = TransportationProvider.objects.filter(is_active=True)
        
        # If origin is selected, get origin object
        if context['origin_id'] and context['origin_id'].isdigit():
            context['origin'] = get_object_or_404(Destination, id=context['origin_id'])
            
        # If destination is selected, get destination object
        if context['destination_id'] and context['destination_id'].isdigit():
            context['destination'] = get_object_or_404(Destination, id=context['destination_id'])
        
        return context


class RouteDetailView(DetailView):
    """
    Display details of a specific transportation route.
    
    Shows detailed information about a route, including available
    schedules, providers, and transportation types.
    """
    model = Route
    template_name = 'transportation/route_detail.html'
    context_object_name = 'route'
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        
        Adds schedules, providers, and images associated with this route.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with added data
        """
        context = super().get_context_data(**kwargs)
        
        # Get schedules for this route, grouped by transportation type
        schedules = self.object.schedules.filter(is_active=True)
        
        # Group schedules by transportation type
        grouped_schedules = {}
        for schedule in schedules:
            type_name = schedule.transportation_type.name
            if type_name not in grouped_schedules:
                grouped_schedules[type_name] = []
            grouped_schedules[type_name].append(schedule)
        
        context['grouped_schedules'] = grouped_schedules
        context['schedule_count'] = schedules.count()
        
        # Get images
        content_type = ContentType.objects.get_for_model(Route)
        context['images'] = TransportationImage.objects.filter(
            content_type=content_type,
            object_id=self.object.id
        )
        
        # Get other routes with same origin or destination
        related_routes = Route.objects.filter(
            Q(origin=self.object.origin) | Q(destination=self.object.destination),
            is_active=True
        ).exclude(id=self.object.id)[:5]
        context['related_routes'] = related_routes
        
        return context


@require_GET
def destination_transport_options(request, destination_id):
    """
    View function for displaying transportation options at a destination.
    
    Shows all available transportation options at a specific destination.
    
    Args:
        request: The HTTP request object
        destination_id: ID of the destination
        
    Returns:
        HttpResponse: Rendered template with transportation options
    """
    destination = get_object_or_404(Destination, id=destination_id, is_active=True)
    
    # Get transportation options for this destination
    options = TransportationOption.objects.filter(
        destination=destination,
        is_active=True
    ).select_related('transport_type').order_by('-is_recommended', 'transport_type__name')
    
    # Get routes originating from this destination
    routes_from = Route.objects.filter(
        origin=destination,
        is_active=True
    ).order_by('-is_popular')[:10]
    
    # Get routes ending at this destination
    routes_to = Route.objects.filter(
        destination=destination,
        is_active=True
    ).order_by('-is_popular')[:10]
    
    context = {
        'destination': destination,
        'options': options,
        'routes_from': routes_from,
        'routes_to': routes_to
    }
    
    return render(request, 'transportation/destination_options.html', context)


@login_required
@require_POST
def search_routes(request):
    """
    Handle AJAX search requests for routes.
    
    Processes form submissions to search for routes between destinations.
    
    Args:
        request: The HTTP request object
        
    Returns:
        JsonResponse: JSON with search results or errors
    """
    origin_id = request.POST.get('origin')
    destination_id = request.POST.get('destination')
    transport_type_id = request.POST.get('transport_type')
    
    # Validate inputs
    errors = {}
    if not origin_id:
        errors['origin'] = "Origin is required"
    if not destination_id:
        errors['destination'] = "Destination is required"
    
    if errors:
        return JsonResponse({'success': False, 'errors': errors}, status=400)
    
    # Search for matching routes
    query = Q(origin_id=origin_id, destination_id=destination_id, is_active=True)
    
    # Add transportation type filter if provided
    if transport_type_id:
        query &= Q(transportation_types__id=transport_type_id)
    
    routes = Route.objects.filter(query).distinct()
    
    if not routes.exists():
        return JsonResponse({
            'success': False,
            'message': "No routes found. Try different search criteria."
        })
    
    # Format results
    results = []
    for route in routes:
        # Get available transportation types for this route
        transport_types = route.transportation_types.filter(is_active=True)
        
        # Get schedules for this route
        schedules = route.schedules.filter(is_active=True)[:5]
        
        results.append({
            'id': route.id,
            'name': route.name,
            'slug': route.slug,
            'origin': route.origin.name,
            'destination': route.destination.name,
            'distance_km': float(route.distance_km) if route.distance_km else None,
            'typical_duration': str(route.typical_duration) if route.typical_duration else None,
            'transport_types': [t.name for t in transport_types],
            'schedule_count': schedules.count(),
            'url': reverse_lazy('transportation:route_detail', kwargs={'slug': route.slug})
        })
    
    return JsonResponse({
        'success': True,
        'routes': results
    })


# API Views
class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination for API results.
    
    Configures pagination for transportation API endpoints.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class TransportationTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for transportation type operations.
    
    Provides CRUD operations for transportation types
    with appropriate permissions.
    """
    queryset = TransportationType.objects.filter(is_active=True)
    serializer_class = TransportationTypeSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name']
    ordering = ['name']
    lookup_field = 'slug'
    
    def get_permissions(self):
        """
        Get permissions based on action.
        
        Read actions are allowed for any user, write actions
        require appropriate permissions.
        
        Returns:
            list: Permission classes for the current action
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        return [permission() for permission in permission_classes]


class TransportationProviderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for transportation provider operations.
    
    Provides CRUD operations for transportation providers
    with appropriate permissions.
    """
    queryset = TransportationProvider.objects.filter(is_active=True)
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'is_partner']
    ordering = ['-is_partner', 'name']
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        """
        Return different serializers based on the action.
        
        Uses detail serializer for retrieve actions, list serializer otherwise.
        
        Returns:
            Serializer class: Appropriate serializer for the current action
        """
        if self.action == 'retrieve':
            return TransportationProviderDetailSerializer
        return TransportationProviderListSerializer
    
    def get_permissions(self):
        """
        Get permissions based on action.
        
        Read actions are allowed for any user, write actions
        require appropriate permissions.
        
        Returns:
            list: Permission classes for the current action
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Get queryset with optional filtering.
        
        Filters by transportation type if specified.
        
        Returns:
            QuerySet: Filtered queryset of providers
        """
        queryset = super().get_queryset()
        
        # Filter by transportation type if provided
        transport_type = self.request.query_params.get('type')
        if transport_type:
            queryset = queryset.filter(transportation_types__slug=transport_type)
            
        # Filter by partner status if provided
        partner = self.request.query_params.get('partner')
        if partner == 'true':
            queryset = queryset.filter(is_partner=True)
            
        return queryset.distinct()


class RouteViewSet(viewsets.ModelViewSet):
    """
    API endpoint for route operations.
    
    Provides CRUD operations for transportation routes
    with appropriate permissions.
    """
    queryset = Route.objects.filter(is_active=True)
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'origin__name', 'destination__name']
    ordering_fields = ['name', 'distance_km', 'is_popular']
    ordering = ['-is_popular', 'name']
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        """
        Return different serializers based on the action.
        
        Uses detail serializer for retrieve actions, list serializer otherwise.
        
        Returns:
            Serializer class: Appropriate serializer for the current action
        """
        if self.action == 'retrieve':
            return RouteDetailSerializer
        return RouteListSerializer
    
    def get_permissions(self):
        """
        Get permissions based on action.
        
        Read actions are allowed for any user, write actions
        require appropriate permissions.
        
        Returns:
            list: Permission classes for the current action
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Get queryset with optional filtering.
        
        Filters by origin, destination, and transportation type.
        
        Returns:
            QuerySet: Filtered queryset of routes
        """
        queryset = super().get_queryset()
        
        # Filter by origin if provided
        origin = self.request.query_params.get('origin')
        if origin:
            queryset = queryset.filter(origin_id=origin)
        
        # Filter by destination if provided
        destination = self.request.query_params.get('destination')
        if destination:
            queryset = queryset.filter(destination_id=destination)
        
        # Filter by transportation type if provided
        transport_type = self.request.query_params.get('type')
        if transport_type:
            queryset = queryset.filter(transportation_types__slug=transport_type)
        
        # Filter by provider if provided
        provider = self.request.query_params.get('provider')
        if provider:
            queryset = queryset.filter(providers__slug=provider)
        
        return queryset.distinct()
    
    @action(detail=False)
    def from_destination(self, request):
        """
        Custom action to get routes originating from a destination.
        
        Args:
            request: The request object
            
        Returns:
            Response: API response with routes from the specified destination
        """
        destination_id = request.query_params.get('id')
        if not destination_id:
            return Response(
                {"detail": "Destination ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        routes = self.get_queryset().filter(origin_id=destination_id)
        page = self.paginate_queryset(routes)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(routes, many=True)
        return Response(serializer.data)
    
    @action(detail=False)
    def to_destination(self, request):
        """
        Custom action to get routes ending at a destination.
        
        Args:
            request: The request object
            
        Returns:
            Response: API response with routes to the specified destination
        """
        destination_id = request.query_params.get('id')
        if not destination_id:
            return Response(
                {"detail": "Destination ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        routes = self.get_queryset().filter(destination_id=destination_id)
        page = self.paginate_queryset(routes)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(routes, many=True)
        return Response(serializer.data)


class ScheduleViewSet(viewsets.ModelViewSet):
    """
    API endpoint for schedule operations.
    
    Provides CRUD operations for transportation schedules
    with appropriate permissions.
    """
    queryset = Schedule.objects.filter(is_active=True)
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['departure_time', 'arrival_time', 'price_economy']
    ordering = ['departure_time']
    
    def get_serializer_class(self):
        """
        Return different serializers based on the action.
        
        Uses detail serializer for retrieve actions, base serializer otherwise.
        
        Returns:
            Serializer class: Appropriate serializer for the current action
        """
        if self.action == 'retrieve':
            return ScheduleDetailSerializer
        return ScheduleSerializer
    
    def get_permissions(self):
        """
        Get permissions based on action.
        
        Read actions are allowed for any user, write actions
        require appropriate permissions.
        
        Returns:
            list: Permission classes for the current action
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Get queryset with optional filtering.
        
        Filters by route, provider, and transportation type.
        
        Returns:
            QuerySet: Filtered queryset of schedules
        """
        queryset = super().get_queryset()
        
        # Filter by route if provided
        route = self.request.query_params.get('route')
        if route:
            queryset = queryset.filter(route__slug=route)
        
        # Filter by provider if provided
        provider = self.request.query_params.get('provider')
        if provider:
            queryset = queryset.filter(provider__slug=provider)
        
        # Filter by transportation type if provided
        transport_type = self.request.query_params.get('type')
        if transport_type:
            queryset = queryset.filter(transportation_type__slug=transport_type)
        
        # Filter by amenities if provided
        has_wifi = self.request.query_params.get('wifi')
        if has_wifi == 'true':
            queryset = queryset.filter(has_wifi=True)
            
        has_power = self.request.query_params.get('power')
        if has_power == 'true':
            queryset = queryset.filter(has_power_outlets=True)
            
        has_meals = self.request.query_params.get('meals')
        if has_meals == 'true':
            queryset = queryset.filter(has_meal_service=True)
        
        return queryset


class TransportationOptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for transportation option operations.
    
    Provides CRUD operations for transportation options
    with appropriate permissions.
    """
    queryset = TransportationOption.objects.filter(is_active=True)
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['transport_type__name', 'avg_price_level', 'is_recommended']
    ordering = ['-is_recommended', 'transport_type__name']
    
    def get_serializer_class(self):
        """
        Return different serializers based on the action.
        
        Uses detail serializer for retrieve actions, base serializer otherwise.
        
        Returns:
            Serializer class: Appropriate serializer for the current action
        """
        if self.action == 'retrieve':
            return TransportationOptionDetailSerializer
        return TransportationOptionSerializer
    
    def get_permissions(self):
        """
        Get permissions based on action.
        
        Read actions are allowed for any user, write actions
        require appropriate permissions.
        
        Returns:
            list: Permission classes for the current action
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Get queryset with optional filtering.
        
        Filters by destination and transportation type.
        
        Returns:
            QuerySet: Filtered queryset of transportation options
        """
        queryset = super().get_queryset()
        
        # Filter by destination if provided
        destination = self.request.query_params.get('destination')
        if destination:
            queryset = queryset.filter(destination_id=destination)
        
        # Filter by transportation type if provided
        transport_type = self.request.query_params.get('type')
        if transport_type:
            queryset = queryset.filter(transport_type__slug=transport_type)
        
        # Filter by recommendation status if provided
        recommended = self.request.query_params.get('recommended')
        if recommended == 'true':
            queryset = queryset.filter(is_recommended=True)
        
        return queryset
    
    @action(detail=False)
    def for_destination(self, request):
        """
        Custom action to get all transportation options for a destination.
        
        Args:
            request: The request object
            
        Returns:
            Response: API response with transportation options for the destination
        """
        destination_id = request.query_params.get('id')
        if not destination_id:
            return Response(
                {"detail": "Destination ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        options = self.get_queryset().filter(destination_id=destination_id)
        serializer = self.get_serializer(options, many=True)
        
        return Response(serializer.data)
