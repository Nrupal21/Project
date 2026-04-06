"""
API Monitor Views Module

This module contains views for the API monitoring dashboard.
"""
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class APIMonitorView(LoginRequiredMixin, TemplateView):
    """
    API Monitoring Dashboard view.
    
    This view renders a dashboard for monitoring and testing API endpoints.
    Access is restricted to logged-in users only for security purposes.
    
    Attributes:
        template_name: The template to render
        login_url: Where to redirect if user is not authenticated
    """
    template_name = 'core/api_monitor.html'
    login_url = '/accounts/login/'
    
    def get_context_data(self, **kwargs):
        """
        Get context data for the template.
        
        Adds additional context data for the API monitor template.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: The context data dictionary
        """
        context = super().get_context_data(**kwargs)
        # Add available API endpoints as suggestions
        context['api_endpoints'] = [
            # Core v1
            {'name': 'Core • Nearby Destinations', 'endpoint': 'core/nearby-destinations/?lat=35.6762&lng=139.6503&radius=25&limit=5', 'method': 'GET'},
            {'name': 'Core • Set User Location', 'endpoint': 'core/user-location/', 'method': 'POST'},

            # Destinations v1
            {'name': 'Destinations • List', 'endpoint': 'destinations/destinations/', 'method': 'GET'},
            {'name': 'Attractions • List', 'endpoint': 'destinations/attractions/', 'method': 'GET'},
            {'name': 'Regions • List', 'endpoint': 'destinations/regions/', 'method': 'GET'},
            {'name': 'Seasons • List', 'endpoint': 'destinations/seasons/', 'method': 'GET'},

            # Emergency v1
            {'name': 'Emergency • Services', 'endpoint': 'emergency/services/', 'method': 'GET'},
            {'name': 'Emergency • Contacts', 'endpoint': 'emergency/contacts/', 'method': 'GET'},
            {'name': 'Emergency • Safety', 'endpoint': 'emergency/safety/', 'method': 'GET'},

            # Transportation v1
            {'name': 'Transportation • Types', 'endpoint': 'transportation/types/', 'method': 'GET'},
            {'name': 'Transportation • Providers', 'endpoint': 'transportation/providers/', 'method': 'GET'},
            {'name': 'Transportation • Routes', 'endpoint': 'transportation/routes/', 'method': 'GET'},

            # Tours v1 (maintenance stubs)
            {'name': 'Tours • List', 'endpoint': 'tours/tours/', 'method': 'GET'},
            {'name': 'Tour Categories • List', 'endpoint': 'tours/categories/', 'method': 'GET'},
        ]
        return context
