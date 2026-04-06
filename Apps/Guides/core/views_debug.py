"""
Debug views to check database and data.
"""
from django.http import JsonResponse
from django.views import View
from destinations.models import Destination, Region

class DebugDestinationsView(View):
    """Debug view to check destinations in the database."""
    
    def get(self, request, *args, **kwargs):
        """Return a JSON response with all destinations."""
        try:
            # Get all destinations
            destinations = list(Destination.objects.all().values(
                'id', 'name', 'city', 'is_featured', 'is_active', 'region__name'
            ))
            
            # Get counts
            total_destinations = len(destinations)
            featured_destinations = len([d for d in destinations if d['is_featured']])
            active_destinations = len([d for d in destinations if d['is_active']])
            
            return JsonResponse({
                'status': 'success',
                'counts': {
                    'total_destinations': total_destinations,
                    'featured_destinations': featured_destinations,
                    'active_destinations': active_destinations,
                },
                'destinations': destinations,
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e),
                'type': type(e).__name__
            }, status=500)
