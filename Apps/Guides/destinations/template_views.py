"""
Template views for the destinations app.

This module contains views that render HTML templates for the frontend.
"""
from django.shortcuts import render, redirect
from django.views import View
from django.urls import reverse

class HomeView(View):
    """View for the home page."""
    
    def get(self, request):
        """
        Handle GET request to the home page.
        
        Args:
            request: The HTTP request
            
        Returns:
            HttpResponse: Rendered home page
        """
        # Redirect to the core:home URL which is now handled by core.app_urls
        return redirect('core:home')
