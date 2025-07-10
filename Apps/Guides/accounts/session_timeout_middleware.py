"""
Session Timeout Middleware for Django.

This module provides middleware to handle automatic session expiration
and logout after a period of inactivity.
"""
from django.conf import settings
from django.shortcuts import redirect
from django.utils import timezone
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

class SessionTimeoutMiddleware:
    """
    Middleware to handle session timeout and automatic logout.
    
    This middleware checks if the user's session has expired due to inactivity
    and logs them out if necessary.
    """
    
    def __init__(self, get_response):
        """
        Initialize the middleware.
        
        Args:
            get_response: The next middleware in the chain
        """
        self.get_response = get_response
        self.session_timeout = getattr(settings, 'SESSION_COOKIE_AGE', 600)  # Default 10 minutes
        self.login_url = getattr(settings, 'LOGIN_URL', '/accounts/login/')
    
    def __call__(self, request):
        """
        Process the request.
        
        Args:
            request: The HTTP request object
            
        Returns:
            HttpResponse: The response from the next middleware or view
        """
        # Skip session timeout check for unauthenticated users
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Skip session timeout check for login/logout URLs
        if request.path in [self.login_url, '/accounts/logout/']:
            return self.get_response(request)
        
        # Initialize last_activity if it doesn't exist
        if 'last_activity' not in request.session:
            request.session['last_activity'] = timezone.now().isoformat()
            return self.get_response(request)
        
        # Calculate time since last activity
        try:
            last_activity = timezone.datetime.fromisoformat(request.session['last_activity'])
            time_since_activity = (timezone.now() - last_activity).total_seconds()
            
            # If session has expired, log the user out
            if time_since_activity > self.session_timeout:
                from django.contrib.auth import logout
                logout(request)
                messages.warning(request, _('Your session has expired due to inactivity. Please log in again.'))
                return redirect(f'{self.login_url}?next={request.path}')
            
        except (ValueError, TypeError):
            # If there's an error parsing the timestamp, reset it
            request.session['last_activity'] = timezone.now().isoformat()
        
        # Update last activity time for active session
        request.session['last_activity'] = timezone.now().isoformat()
        
        return self.get_response(request)
