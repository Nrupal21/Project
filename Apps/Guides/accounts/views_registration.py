"""
Registration-related views for the accounts app.

This module contains view functions and classes for user registration
including success pages and registration confirmation.
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from .models import User
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)


class RegistrationSuccessView(TemplateView):
    """
    Display a success page after user registration.
    
    This view shows a confirmation page after successful registration,
    including personalized welcome message and next steps information.
    It retrieves the user from the session if available.
    """
    template_name = 'accounts/registration_success.html'
    
    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to handle both direct access and post-registration access.
        
        If the user is authenticated but no registered_user_id is in session,
        use the current user for the success page.
        
        Args:
            request: The HTTP request object
            
        Returns:
            HttpResponse: Rendered success page or redirect
        """
        # If user is authenticated but no registered_user_id in session, use current user
        if request.user.is_authenticated and not request.session.get('registered_user_id'):
            request.session['registered_user_id'] = request.user.id
            
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """
        Add user data to the template context.
        
        Retrieves the newly registered user from the session if available
        and adds it to the template context for personalization.
        
        Returns:
            dict: Context dictionary with user data
        """
        context = super().get_context_data(**kwargs)
        
        # Try to get user from session
        user_id = self.request.session.get('registered_user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                context['user'] = user
                
                # Clear the session variable after use
                del self.request.session['registered_user_id']
                logger.info(f"Showing registration success page for user {user.email}")
            except User.DoesNotExist:
                logger.warning(f"User with ID {user_id} not found for registration success page")
        elif self.request.user.is_authenticated:
            # Fallback to current user if authenticated
            context['user'] = self.request.user
            logger.info(f"Using current user for registration success page: {self.request.user.email}")
        
        return context
