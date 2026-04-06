"""
Views for the emergency app.

This module defines view functions and classes for handling
emergency-related HTTP requests, including displaying and
managing emergency services, contacts, safety information,
and emergency guides.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q, Count
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib import messages

from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

from destinations.models import Destination, Region
from .models import (
    EmergencyServiceType, EmergencyService, EmergencyContact,
    SafetyInformation, EmergencyGuide
)
from .serializers import (
    EmergencyServiceTypeSerializer, 
    EmergencyContactSerializer,
    EmergencyServiceListSerializer,
    EmergencyServiceDetailSerializer,
    SafetyInformationListSerializer,
    SafetyInformationDetailSerializer,
    EmergencyGuideListSerializer,
    EmergencyGuideDetailSerializer
)


# API Viewsets

class EmergencyServiceTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows emergency service types to be viewed or edited.
    """
    queryset = EmergencyServiceType.objects.filter(is_active=True)
    serializer_class = EmergencyServiceTypeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'priority_level']
    ordering = ['priority_level', 'name']


class EmergencyServiceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows emergency services to be viewed or edited.
    """
    queryset = EmergencyService.objects.filter(is_active=True).select_related('service_type', 'destination', 'region')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'description', 'phone', 'address', 'website']
    ordering_fields = ['name', 'service_type__priority_level']
    ordering = ['service_type__priority_level', 'name']
    filterset_fields = {
        'service_type': ['exact'],
        'destination': ['exact'],
        'region': ['exact'],
        'is_24_hours': ['exact'],
        'serves_foreign_travelers': ['exact']
    }

    def get_serializer_class(self):
        if self.action == 'list':
            return EmergencyServiceListSerializer
        return EmergencyServiceDetailSerializer


class EmergencyContactViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows emergency contacts to be viewed or edited.
    """
    queryset = EmergencyContact.objects.filter(is_active=True)
    serializer_class = EmergencyContactSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'phone', 'email', 'description']
    ordering_fields = ['name', 'country', 'priority']
    ordering = ['country', 'priority', 'name']
    filterset_fields = ['country', 'is_emergency', 'is_medical', 'is_police', 'is_fire']


class SafetyInformationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows safety information to be viewed or edited.
    """
    queryset = SafetyInformation.objects.filter(is_active=True).select_related('destination', 'region')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['title', 'content', 'category', 'risk_level']
    ordering_fields = ['title', 'risk_level', 'last_updated']
    ordering = ['-last_updated']
    filterset_fields = {
        'destination': ['exact'],
        'region': ['exact'],
        'category': ['exact', 'icontains'],
        'risk_level': ['exact'],
        'is_critical': ['exact']
    }

    def get_serializer_class(self):
        if self.action == 'list':
            return SafetyInformationListSerializer
        return SafetyInformationDetailSerializer


class EmergencyGuideViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows emergency guides to be viewed or edited.
    """
    queryset = EmergencyGuide.objects.filter(is_active=True).prefetch_related('related_services')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['title', 'content', 'category']
    ordering_fields = ['title', 'category', 'created_at']
    ordering = ['category', 'title']
    filterset_fields = {
        'category': ['exact', 'icontains'],
        'is_featured': ['exact']
    }

    def get_serializer_class(self):
        if self.action == 'list':
            return EmergencyGuideListSerializer
        return EmergencyGuideDetailSerializer


# Web Views
class EmergencyServiceTypeListView(ListView):
    """
    Display a list of emergency service types.
    
    Renders a template with all active emergency service types,
    ordered by priority level.
    """
    model = EmergencyServiceType
    template_name = 'emergency/service_type_list.html'
    context_object_name = 'service_types'
    queryset = EmergencyServiceType.objects.filter(is_active=True)


class RegionEmergencyContactsView(ListView):
    """
    Display emergency contacts for a specific region.
    
    Shows all active emergency contacts for a given region,
    organized by contact type.
    """
    model = EmergencyContact
    template_name = 'emergency/region_contacts.html'
    context_object_name = 'contacts'
    
    def get_queryset(self):
        """
        Get emergency contacts for the specified region.
        
        Returns:
            QuerySet: Filtered queryset of emergency contacts for the region
        """
        region_slug = self.kwargs.get('region_slug')
        return EmergencyContact.objects.filter(
            region__slug=region_slug,
            is_active=True
        ).select_related('region').order_by('priority', 'name')
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        
        Adds region information and organizes contacts by type.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with added data
        """
        context = super().get_context_data(**kwargs)
        
        # Get region from the first contact (if available)
        contacts = self.get_queryset()
        if contacts.exists():
            context['region'] = contacts[0].region
        
        # Organize contacts by type
        context['emergency_contacts'] = contacts.filter(is_emergency=True)
        context['medical_contacts'] = contacts.filter(is_medical=True)
        context['police_contacts'] = contacts.filter(is_police=True)
        context['fire_contacts'] = contacts.filter(is_fire=True)
        context['other_contacts'] = contacts.filter(
            is_emergency=False,
            is_medical=False,
            is_police=False,
            is_fire=False
        )
        
        return context


class CountryEmergencyContactsView(ListView):
    """
    Display emergency contacts for a specific country.
    
    Shows all active emergency contacts for a given country code,
    organized by contact type.
    """
    model = EmergencyContact
    template_name = 'emergency/country_contacts.html'
    context_object_name = 'contacts'
    
    def get_queryset(self):
        """
        Get emergency contacts for the specified country.
        
        Returns:
            QuerySet: Filtered queryset of emergency contacts for the country
        """
        country_code = self.kwargs.get('country_code').upper()
        return EmergencyContact.objects.filter(
            country_code__iexact=country_code,
            is_active=True
        ).order_by('priority', 'name')
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        
        Adds country code and organizes contacts by type.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with added data
        """
        context = super().get_context_data(**kwargs)
        country_code = self.kwargs.get('country_code').upper()
        
        # Get all contacts for the country
        contacts = self.get_queryset()
        
        # Organize contacts by type
        context['emergency_contacts'] = contacts.filter(is_emergency=True)
        context['medical_contacts'] = contacts.filter(is_medical=True)
        context['police_contacts'] = contacts.filter(is_police=True)
        context['fire_contacts'] = contacts.filter(is_fire=True)
        context['other_contacts'] = contacts.filter(
            is_emergency=False,
            is_medical=False,
            is_police=False,
            is_fire=False
        )
        
        # Add country information
        context['country_code'] = country_code
        
        # Get country name from the first contact (if available)
        if contacts.exists():
            context['country_name'] = contacts[0].country
        
        return context


class EmergencyContactListView(ListView):
    """
    Display a list of emergency contacts.
    
    Renders a template with all active emergency contacts,
    with options for filtering by country and contact type.
    """
    model = EmergencyContact
    template_name = 'emergency/contact_list.html'
    context_object_name = 'contacts'
    paginate_by = 20
    
    def get_queryset(self):
        """
        Get the list of emergency contacts with filtering.
        
        Filters by country and contact type if specified in the request.
        
        Returns:
            QuerySet: Filtered queryset of emergency contacts
        """
        queryset = EmergencyContact.objects.filter(is_active=True)
        
        # Filter by country if provided
        country = self.request.GET.get('country')
        if country:
            queryset = queryset.filter(country__iexact=country)
        
        # Filter by contact type if provided
        contact_type = self.request.GET.get('type')
        if contact_type == 'emergency':
            queryset = queryset.filter(is_emergency=True)
        elif contact_type == 'medical':
            queryset = queryset.filter(is_medical=True)
        elif contact_type == 'police':
            queryset = queryset.filter(is_police=True)
        elif contact_type == 'fire':
            queryset = queryset.filter(is_fire=True)
        
        return queryset.order_by('country', 'priority', 'name')
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        
        Adds filter parameters and available countries to the context.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with added data
        """
        context = super().get_context_data(**kwargs)
        
        # Add filter parameters to context
        context['selected_country'] = self.request.GET.get('country', '')
        context['selected_type'] = self.request.GET.get('type', '')
        
        # Get unique countries for filter dropdown
        context['countries'] = EmergencyContact.objects.filter(
            is_active=True
        ).values_list('country', flat=True).distinct().order_by('country')
        
        return context


class EmergencyServiceTypeDetailView(DetailView):
    """
    Display details of a specific emergency service type.
    
    Shows detailed information about an emergency service type,
    including its description and related services.
    """
    model = EmergencyServiceType
    template_name = 'emergency/service_type_detail.html'
    context_object_name = 'service_type'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        """
        Get the queryset of emergency service types.
        
        Returns only active service types.
        
        Returns:
            QuerySet: Filtered queryset of emergency service types
        """
        return EmergencyServiceType.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        
        Adds related services to the context.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with added data
        """
        context = super().get_context_data(**kwargs)
        
        # Get related services of this type
        context['services'] = EmergencyService.objects.filter(
            service_type=self.object,
            is_active=True
        ).select_related('destination', 'region')
        
        return context


class EmergencyServiceListView(ListView):
    """
    Display a list of emergency services.
    
    Renders a template with emergency services, with options
    for filtering by service type, destination, and region.
    """
    model = EmergencyService
    template_name = 'emergency/service_list.html'
    context_object_name = 'services'
    paginate_by = 20
    
    def get_queryset(self):
        """
        Get the list of emergency services with filtering.
        
        Filters by service type, destination, region, and 24-hour availability.
        
        Returns:
            QuerySet: Filtered queryset of emergency services
        """
        queryset = EmergencyService.objects.filter(is_active=True)
        
        # Filter by service type if provided
        service_type_slug = self.request.GET.get('type')
        if service_type_slug:
            queryset = queryset.filter(service_type__slug=service_type_slug)
        
        # Filter by destination if provided
        destination_id = self.request.GET.get('destination')
        if destination_id and destination_id.isdigit():
            queryset = queryset.filter(destination_id=destination_id)
        
        # Filter by region if provided
        region_id = self.request.GET.get('region')
        if region_id and region_id.isdigit():
            queryset = queryset.filter(region_id=region_id)
        
        # Filter by 24-hour availability if requested
        hours_24 = self.request.GET.get('hours_24')
        if hours_24 == 'true':
            queryset = queryset.filter(is_24_hours=True)
        
        # Filter by services for foreign travelers
        foreign = self.request.GET.get('foreign')
        if foreign == 'true':
            queryset = queryset.filter(serves_foreign_travelers=True)
        
        # Sort by priority level of service type and then by name
        return queryset.select_related('service_type', 'destination', 'region').order_by(
            'service_type__priority_level', 'name'
        )
    
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
        context['service_type_slug'] = self.request.GET.get('type')
        context['destination_id'] = self.request.GET.get('destination')
        context['region_id'] = self.request.GET.get('region')
        context['hours_24'] = self.request.GET.get('hours_24') == 'true'
        context['foreign'] = self.request.GET.get('foreign') == 'true'
        
        # Add filter options
        context['service_types'] = EmergencyServiceType.objects.filter(is_active=True)
        context['destinations'] = Destination.objects.filter(is_active=True).order_by('name')
        context['regions'] = Region.objects.filter(is_active=True).order_by('name')
        
        # If service type is selected, get service type object
        if context['service_type_slug']:
            context['selected_service_type'] = get_object_or_404(
                EmergencyServiceType, slug=context['service_type_slug']
            )
        
        return context


class EmergencyServiceDetailView(DetailView):
    """
    Display details of a specific emergency service.
    
    Shows detailed information about an emergency service,
    including contact details, location, hours, and notes.
    """
    model = EmergencyService
    template_name = 'emergency/service_detail.html'
    context_object_name = 'service'
    
    def get_queryset(self):
        """
        Get the queryset of emergency services.
        
        Returns only active services.
        
        Returns:
            QuerySet: Filtered queryset of emergency services
        """
        return EmergencyService.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        
        Adds related services and guides to context.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with added data
        """
        context = super().get_context_data(**kwargs)
        
        # Get related services of the same type in the same location
        related_services = EmergencyService.objects.filter(is_active=True)
        
        if self.object.destination:
            related_services = related_services.filter(destination=self.object.destination)
        elif self.object.region:
            related_services = related_services.filter(region=self.object.region)
            
        related_services = related_services.exclude(id=self.object.id)[:5]
        context['related_services'] = related_services
        
        # Get emergency guides that reference this service
        context['related_guides'] = self.object.related_guides.filter(is_active=True)[:5]
        
        # Get safety information for this location
        if self.object.destination:
            context['safety_info'] = SafetyInformation.objects.filter(
                Q(destination=self.object.destination) | Q(region=self.object.region),
                is_active=True
            )[:5]
        elif self.object.region:
            context['safety_info'] = SafetyInformation.objects.filter(
                region=self.object.region,
                is_active=True
            )[:5]
        
        return context


class SafetyInformationListView(ListView):
    """
    Display a list of safety information items.
    
    Renders a template with safety information, with filtering options
    for category, risk level, destination, and region.
    """
    model = SafetyInformation
    template_name = 'emergency/safety_list.html'
    context_object_name = 'safety_items'
    paginate_by = 15
    
    def get_queryset(self):
        """
        Get the list of safety information with filtering.
        
        Filters by category, risk level, destination, and region.
        
        Returns:
            QuerySet: Filtered queryset of safety information
        """
        queryset = SafetyInformation.objects.filter(is_active=True)
        
        # Filter by category if provided
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by risk level if provided
        risk_level = self.request.GET.get('risk')
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)
        
        # Filter by destination if provided
        destination_id = self.request.GET.get('destination')
        if destination_id and destination_id.isdigit():
            queryset = queryset.filter(destination_id=destination_id)
        
        # Filter by region if provided
        region_id = self.request.GET.get('region')
        if region_id and region_id.isdigit():
            queryset = queryset.filter(region_id=region_id)
        
        # Sort by featured status and then by update date
        return queryset.select_related('destination', 'region').order_by(
            '-is_featured', '-updated_at'
        )
    
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
        context['category'] = self.request.GET.get('category')
        context['risk_level'] = self.request.GET.get('risk')
        context['destination_id'] = self.request.GET.get('destination')
        context['region_id'] = self.request.GET.get('region')
        
        # Add filter options
        context['category_choices'] = dict(SafetyInformation.CATEGORY_CHOICES)
        context['risk_level_choices'] = dict(SafetyInformation.RISK_LEVEL_CHOICES)
        context['destinations'] = Destination.objects.filter(is_active=True).order_by('name')
        context['regions'] = Region.objects.filter(is_active=True).order_by('name')
        
        # Get featured safety information
        context['featured_items'] = SafetyInformation.objects.filter(
            is_active=True,
            is_featured=True
        )[:5]
        
        return context


class SafetyInformationDetailView(DetailView):
    """
    Display detailed information about a specific safety notice.
    
    Shows comprehensive safety information including description,
    risk level, recommendations, and related services.
    """
    model = SafetyInformation
    template_name = 'emergency/safety_information_detail.html'
    context_object_name = 'safety_info'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        """
        Get the safety information with related data.
        
        Returns:
            QuerySet: Filtered queryset of safety information
        """
        return SafetyInformation.objects.filter(is_active=True).select_related('destination', 'region')
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        
        Adds related services and other relevant information to the context.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with added data
        """
        context = super().get_context_data(**kwargs)
        safety_info = self.get_object()
        
        # Add related services if available
        if safety_info.related_services.exists():
            context['related_services'] = safety_info.related_services.filter(is_active=True)
        
        # Add similar safety information (same category or risk level)
        similar_safety_info = SafetyInformation.objects.filter(
            is_active=True
        ).exclude(pk=safety_info.pk)
        
        if safety_info.category:
            similar_safety_info = similar_safety_info.filter(category=safety_info.category)
        if safety_info.risk_level:
            similar_safety_info = similar_safety_info.filter(risk_level=safety_info.risk_level)
        
        context['similar_safety_info'] = similar_safety_info[:5]  # Limit to 5 similar items
        
        # Add navigation context
        context['previous'] = SafetyInformation.objects.filter(
            is_active=True,
            last_updated__lt=safety_info.last_updated
        ).order_by('-last_updated').first()
        
        context['next'] = SafetyInformation.objects.filter(
            is_active=True,
            last_updated__gt=safety_info.last_updated
        ).order_by('last_updated').first()
        
        return context


class SafetyInformationListView(ListView):
    """
    Display a list of safety information.
    
    Renders a template with all active safety information,
    with options for filtering by destination, region, and category.
    """
    model = SafetyInformation
    template_name = 'emergency/safety_information_list.html'
    context_object_name = 'safety_info_list'
    paginate_by = 10
    
    def get_queryset(self):
        """
        Get the list of safety information with filtering.
        
        Filters by destination, region, and category if specified in the request.
        
        Returns:
            QuerySet: Filtered queryset of safety information
        """
        queryset = SafetyInformation.objects.filter(is_active=True).select_related('destination', 'region')
        
        # Filter by destination if provided
        destination_slug = self.request.GET.get('destination')
        if destination_slug:
            queryset = queryset.filter(destination__slug=destination_slug)
        
        # Filter by region if provided
        region_slug = self.request.GET.get('region')
        if region_slug:
            queryset = queryset.filter(region__slug=region_slug)
        
        # Filter by category if provided
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__iexact=category)
        
        # Filter by risk level if provided
        risk_level = self.request.GET.get('risk_level')
        if risk_level:
            queryset = queryset.filter(risk_level__iexact=risk_level)
        
        # Filter by critical status if provided
        is_critical = self.request.GET.get('is_critical')
        if is_critical is not None:
            queryset = queryset.filter(is_critical=is_critical.lower() == 'true')
        
        return queryset.order_by('-last_updated')
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        
        Adds filter parameters and available categories to the context.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with added data
        """
        context = super().get_context_data(**kwargs)
        
        # Add filter parameters to context
        context['selected_destination'] = self.request.GET.get('destination', '')
        context['selected_region'] = self.request.GET.get('region', '')
        context['selected_category'] = self.request.GET.get('category', '')
        context['selected_risk_level'] = self.request.GET.get('risk_level', '')
        context['is_critical'] = self.request.GET.get('is_critical', '')
        
        # Get unique categories for filter dropdown
        context['categories'] = SafetyInformation.objects.filter(
            is_active=True
        ).values_list('category', flat=True).distinct().order_by('category')
        
        # Get unique risk levels for filter dropdown
        context['risk_levels'] = SafetyInformation.objects.filter(
            is_active=True
        ).values_list('risk_level', flat=True).distinct().order_by('risk_level')
        
        return context
