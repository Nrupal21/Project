"""
API views for emergency-related endpoints.
"""
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

from destinations.models import Destination
from .models import EmergencyService, EmergencyContact, SafetyInformation
from .serializers import (
    EmergencyServiceListSerializer as EmergencyServiceSerializer,
    EmergencyContactSerializer,
    SafetyInformationListSerializer as SafetyInformationSerializer
)


@api_view(['GET'])
def destination_emergency_services_api(request, destination_slug):
    """
    API endpoint to get emergency services for a specific destination.
    
    Returns a list of emergency services available in the specified destination.
    """
    destination = get_object_or_404(Destination, slug=destination_slug, is_active=True)
    
    # Get services for this destination and its region
    services = EmergencyService.objects.filter(
        Q(destination=destination) | Q(region=destination.region),
        is_active=True
    ).select_related('service_type', 'region').order_by('service_type__priority_level', 'name')
    
    serializer = EmergencyServiceSerializer(services, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def destination_emergency_contacts_api(request, destination_slug):
    """
    API endpoint to get emergency contacts for a specific destination.
    
    Returns a list of emergency contacts for the destination's country.
    """
    destination = get_object_or_404(Destination, slug=destination_slug, is_active=True)
    
    # Get contacts for this destination's country and global contacts
    contacts = EmergencyContact.objects.filter(
        Q(country=destination.country_code) | Q(is_global=True),
        is_active=True
    ).order_by('is_emergency', 'name')
    
    serializer = EmergencyContactSerializer(contacts, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def destination_safety_info_api(request, destination_slug):
    """
    API endpoint to get safety information for a specific destination.
    
    Returns safety information specific to the destination and its region.
    """
    destination = get_object_or_404(Destination, slug=destination_slug, is_active=True)
    
    # Get safety information for this destination and its region
    safety_info = SafetyInformation.objects.filter(
        Q(destination=destination) | Q(region=destination.region),
        is_active=True
    ).select_related('destination', 'region').order_by('-is_critical', '-last_updated')
    
    serializer = SafetyInformationSerializer(safety_info, many=True, context={'request': request})
    return Response(serializer.data)
