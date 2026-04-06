"""
Views for destination-specific emergency information.
"""
from django.views.generic import ListView, DetailView, TemplateView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from destinations.models import Destination, Region
from .models import EmergencyService, EmergencyContact, SafetyInformation, EmergencyGuide


class DestinationEmergencyInfoView(TemplateView):
    """
    Display emergency information for a specific destination.
    
    Shows emergency services, contacts, safety information, and guides
    for a specific destination.
    """
    template_name = 'emergency/destination_emergency.html'
    
    def get_context_data(self, **kwargs):
        """
        Add emergency information for the destination to the context.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with added data
        """
        context = super().get_context_data(**kwargs)
        destination_slug = self.kwargs.get('destination_slug')
        
        # Get the destination
        destination = get_object_or_404(Destination, slug=destination_slug, is_active=True)
        context['destination'] = destination
        
        # Get emergency services for this destination
        context['emergency_services'] = EmergencyService.objects.filter(
            Q(destination=destination) | Q(region=destination.region),
            is_active=True
        ).select_related('service_type', 'region').order_by('service_type__priority_level', 'name')
        
        # Get emergency contacts for this destination's country
        context['emergency_contacts'] = EmergencyContact.objects.filter(
            Q(country=destination.country_code) | Q(is_global=True),
            is_active=True
        ).order_by('is_emergency', 'name')
        
        # Get safety information for this destination
        context['safety_information'] = SafetyInformation.objects.filter(
            Q(destination=destination) | Q(region=destination.region),
            is_active=True
        ).select_related('destination', 'region').order_by('-is_critical', '-last_updated')
        
        # Get emergency guides relevant to this destination
        context['emergency_guides'] = EmergencyGuide.objects.filter(
            is_active=True
        ).prefetch_related('related_services').order_by('category', 'title')
        
        return context


class RegionEmergencyInfoView(TemplateView):
    """
    Display emergency information for a specific region.
    
    Shows emergency services, contacts, safety information, and guides
    for a specific region.
    """
    template_name = 'emergency/region_emergency.html'
    
    def get_context_data(self, **kwargs):
        """
        Add emergency information for the region to the context.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with added data
        """
        context = super().get_context_data(**kwargs)
        region_slug = self.kwargs.get('region_slug')
        
        # Get the region
        region = get_object_or_404(Region, slug=region_slug, is_active=True)
        context['region'] = region
        
        # Get emergency services for this region
        context['emergency_services'] = EmergencyService.objects.filter(
            region=region,
            is_active=True
        ).select_related('service_type').order_by('service_type__priority_level', 'name')
        
        # Get emergency contacts for countries in this region
        country_codes = region.destinations.filter(is_active=True).values_list('country_code', flat=True).distinct()
        context['emergency_contacts'] = EmergencyContact.objects.filter(
            Q(country__in=country_codes) | Q(is_global=True),
            is_active=True
        ).order_by('country', 'is_emergency', 'name')
        
        # Get safety information for this region
        context['safety_information'] = SafetyInformation.objects.filter(
            region=region,
            is_active=True
        ).select_related('destination').order_by('-is_critical', '-last_updated')
        
        # Get emergency guides relevant to this region
        context['emergency_guides'] = EmergencyGuide.objects.filter(
            is_active=True
        ).prefetch_related('related_services').order_by('category', 'title')
        
        # Get destinations in this region for navigation
        context['destinations'] = region.destinations.filter(is_active=True).order_by('name')
        
        return context
