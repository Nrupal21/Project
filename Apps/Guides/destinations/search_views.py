"""
Search views for the destinations app.

This module contains views related to searching destinations and attractions.
It's separated from the main views.py to keep the codebase organized and maintainable.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import Q
from .models import Destination


@require_GET
def destination_search(request):
    """
    AJAX endpoint for searching destinations by name, city, or region.
    
    This view provides autocomplete functionality for the AI Itinerary Generator,
    allowing users to search for destinations by name, city, or region name.
    It returns a JSON response with matching destinations for use in the frontend.
    
    Query Parameters:
        q (str): Search term to filter destinations by name, city, or region
        limit (int): Maximum number of results to return (default: 10, max: 20)
        
    Returns:
        JsonResponse: JSON array of matching destinations with id, name, city, and region
                     Returns empty array if no search term is provided
    """
    search_term = request.GET.get('q', '').strip()
    limit = min(int(request.GET.get('limit', 10)), 20)  # Cap at 20 results for performance
    
    if not search_term:
        return JsonResponse([], safe=False)
    
    # Search in destination names, cities, and region names
    destinations = Destination.objects.filter(
        Q(name__icontains=search_term) |
        Q(city__icontains=search_term) |
        Q(region__name__icontains=search_term),
        is_active=True,
        approval_status=Destination.ApprovalStatus.APPROVED
    ).select_related('region').distinct()[:limit]
    
    # Format results for the frontend autocomplete
    results = [{
        'id': dest.id,
        'name': dest.name,
        'city': dest.city or '',
        'region': dest.region.name,
        'display': f"{dest.name}, {dest.region.name}"
    } for dest in destinations]
    
    return JsonResponse(results, safe=False)
