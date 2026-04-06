"""
Views for the guides app.

This module contains view functions and classes for the guides app.
It includes views for the guide dashboard and other guide-specific functionality.
"""

from django.db.models import Avg
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

# Import models from other apps
try:
    from destinations.models import Destination, Attraction
except ImportError:
    pass  # Handle case where destinations app is not available

try:
    from reviews.models import Review
except ImportError:
    pass  # Handle case where reviews app is not available

class GuideDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    View for the guide dashboard.
    
    This view is only accessible to users with the 'LOCAL_GUIDE' role.
    It displays a dashboard with guide-specific information and actions.
    """
    template_name = 'guides/dashboard.html'
    
    def test_func(self):
        """
        Test if the user has the 'LOCAL_GUIDE' role.
        
        Returns:
            bool: True if the user is a local guide, False otherwise.
        """
        return hasattr(self.request.user, 'role') and self.request.user.role == 'LOCAL_GUIDE'
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.
        
        Returns:
            dict: Context data for the template with guide-specific information.
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Set page title
        context['page_title'] = 'Guide Dashboard'
        
        # Initialize default values in case models aren't available
        context.update({
            'user_destinations_count': 0,
            'user_attractions_count': 0,
            'average_rating': 'N/A',
            'recent_activity': []
        })
        
        try:
            # Get guide's destinations and attractions count
            if 'destinations' in self.request.apps.get_app_configs():
                context['user_destinations_count'] = Destination.objects.filter(created_by=user).count()
                context['user_attractions_count'] = Attraction.objects.filter(created_by=user).count()
            
            # Get average rating if reviews app is available
            if 'reviews' in self.request.apps.get_app_configs():
                from reviews.models import Review
                reviews = Review.objects.filter(guide=user)
                if reviews.exists():
                    context['average_rating'] = round(reviews.aggregate(Avg('rating'))['rating__avg'], 1)
            
            # Generate recent activity
            context['recent_activity'] = self.get_recent_activity()
            
        except Exception as e:
            # Log error but don't crash the view
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in GuideDashboardView.get_context_data: {str(e)}")
        
        return context
    
    def get_recent_activity(self):
        """
        Generate recent activity data for the guide.
        
        Returns:
            list: List of recent activity items.
        """
        user = self.request.user
        recent_activity = []
        
        # Add recent destinations (last 3)
        if 'destinations' in self.request.apps.get_app_configs():
            recent_destinations = Destination.objects.filter(
                created_by=user
            ).order_by('-created_at')[:3]
            
            for dest in recent_destinations:
                recent_activity.append({
                    'title': f'Destination: {dest.name}',
                    'description': f'Added {dest.name} to destinations',
                    'status': 'Completed',
                    'date': dest.created_at
                })
        
        # Add recent attractions (last 3)
        if 'destinations' in self.request.apps.get_app_configs():
            recent_attractions = Attraction.objects.filter(
                created_by=user
            ).order_by('-created_at')[:3]
            
            for attr in recent_attractions:
                recent_activity.append({
                    'title': f'Attraction: {attr.name}',
                    'description': f'Added {attr.name} to {attr.destination.name}',
                    'status': 'Completed',
                    'date': attr.created_at
                })
        
        # Sort all activities by date, newest first
        recent_activity.sort(key=lambda x: x['date'], reverse=True)
        
        # Return only the 5 most recent activities
        return recent_activity[:5]
