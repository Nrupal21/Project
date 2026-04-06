"""
Views for handling review submission success pages.

This module contains views that handle the display of success messages
and related functionality after a review has been successfully submitted.
"""

from django.views.generic import TemplateView
from django.shortcuts import render


class ReviewSuccessView(TemplateView):
    """
    Display a success page after a review has been submitted.
    
    This view shows a confirmation message to the user after they have
    successfully submitted a review. It includes options to return to
    the destination or go to the home page.
    
    Attributes:
        template_name: The template to render for the success page
    """
    template_name = 'reviews/review_success.html'
    
    def get_context_data(self, **kwargs):
        """
        Add the destination URL to the template context.
        
        Retrieves the destination URL from the query parameters to provide
        a way back to the reviewed item.
        
        Args:
            **kwargs: Additional context data
            
        Returns:
            dict: Context dictionary with destination URL
        """
        context = super().get_context_data(**kwargs)
        context['destination_url'] = self.request.GET.get('destination', '/')
        return context
