"""
Core middleware for the food ordering system.

Includes:
- Session timeout and management
- Date-based access restrictions
"""
import os
import time
import datetime
import platform
import subprocess
from django.utils import timezone
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.http import JsonResponse, HttpResponseForbidden


class DateRestrictionMiddleware:
    """
    Middleware to restrict access on specific dates and perform system actions.
    
    This middleware prevents the application from running on specified dates
    and can perform system actions like shutting down the PC if someone tries
    to access the application on restricted dates.
    
    Features:
    - Restrict access on specific dates
    - System shutdown on unauthorized access attempts
    - Configurable restricted dates
    - Graceful error handling
    """
    
    def __init__(self, get_response):
        """Initialize the middleware with restricted dates."""
        self.get_response = get_response
        # List of restricted dates in YYYY-MM-DD format
        self.restricted_dates = [
            '2026-12-22',  # New Year's Eve
            # Add more dates as needed
        ]
    
    def is_restricted_date(self, date_to_check):
        """Check if the given date is in the restricted dates list."""
        return date_to_check.strftime('%Y-%m-%d') in self.restricted_dates
    
    def system_shutdown(self):
        """Shut down the system (Windows only)."""
        try:
            if platform.system() == 'Windows':
                os.system('shutdown /s /t 1')
            elif platform.system() == 'Linux' or platform.system() == 'Darwin':
                os.system('shutdown -h now')
            return True
        except Exception as e:
            print(f"Failed to shut down system: {e}")
            return False
    
    def __call__(self, request):
        """Process each request through the middleware."""
        current_date = timezone.now().date()
        
        # Check if current date is restricted
        if self.is_restricted_date(current_date):
            # Log the unauthorized access attempt
            print(f"Unauthorized access attempt on restricted date: {current_date}")
            
            # Shutdown the system
            self.system_shutdown()
            
            # Return 403 Forbidden response
            return HttpResponseForbidden(
                "<h1>Access Denied</h1>"
                "<p>This application is not available on this date.</p>"
                "<p>Your system will be shut down for security reasons.</p>",
                content_type="text/html"
            )
        
        return self.get_response(request)


class SessionTimeoutMiddleware:
    """
    Middleware to handle session timeout based on inactivity.
    
    This middleware tracks user activity and automatically logs out users
    after a period of inactivity. It provides JSON responses for AJAX requests
    and regular redirects for standard requests.
    
    Features:
    - Inactivity timeout tracking
    - AJAX request handling
    - Session last activity tracking
    - Automatic logout on timeout
    """
    
    def __init__(self, get_response):
        """
        Initialize the middleware.
        
        Args:
            get_response: Django's get_response callable
        """
        self.get_response = get_response
    
    def __call__(self, request):
        """
        Process each request through the middleware.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            HttpResponse: Processed response or redirect to login
        """
        # Skip timeout check for unauthenticated users and static files
        if not request.user.is_authenticated or self._is_static_file(request):
            return self.get_response(request)
        
        # Skip timeout for exempt URLs (checkout, payment, etc.)
        if self._is_exempt_url(request):
            return self.get_response(request)
        
        # Get session timeout settings
        customer_timeout = getattr(settings, 'SESSION_INACTIVITY_TIMEOUT', 1800)
        staff_timeout = getattr(settings, 'SESSION_STAFF_INACTIVITY_TIMEOUT', 3600)
        warning_time = getattr(settings, 'SESSION_WARNING_TIME', 120)
        absolute_timeout = getattr(settings, 'SESSION_COOKIE_AGE', 3600)
        
        # Determine timeout based on user role
        if self._is_restaurant_staff(request.user):
            inactivity_timeout = staff_timeout
        else:
            inactivity_timeout = customer_timeout
        
        # Get session timestamps
        current_time = time.time()
        login_time = request.session.get('login_time', current_time)
        last_activity = request.session.get('last_activity', current_time)
        
        # Check absolute timeout (from login)
        absolute_time_elapsed = current_time - login_time
        if absolute_time_elapsed > absolute_timeout:
            self._logout_user(request)
            return self._handle_timeout_response(request, 'Your session has expired due to time limit.')
        
        # Check inactivity timeout
        if last_activity:
            inactivity_time_elapsed = current_time - last_activity
            if inactivity_time_elapsed > inactivity_timeout:
                self._logout_user(request)
                return self._handle_timeout_response(request, 'Your session has expired due to inactivity.')
        
        # Initialize login_time if not set (first request after login)
        if 'login_time' not in request.session:
            request.session['login_time'] = current_time
        
        # Update last activity timestamp
        request.session['last_activity'] = current_time
        request.session['session_timeout'] = inactivity_timeout
        request.session['warning_time'] = warning_time
        request.session.modified = True
        
        # Add timeout info to response headers for JavaScript
        response = self.get_response(request)
        response['X-Session-Timeout'] = inactivity_timeout
        response['X-Warning-Time'] = warning_time
        response['X-Current-Time'] = current_time
        response['X-Login-Time'] = login_time
        
        return response
    
    def _is_static_file(self, request):
        """
        Check if the request is for a static file.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            bool: True if request is for static file, False otherwise
        """
        static_paths = ['/static/', '/media/', '/admin/static/']
        return any(request.path.startswith(path) for path in static_paths)
    
    def _is_exempt_url(self, request):
        """
        Check if the request URL is exempt from session timeout.
        
        Critical pages like checkout and payment should not timeout
        to prevent data loss during transactions.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            bool: True if URL is exempt, False otherwise
        """
        exempt_urls = getattr(settings, 'SESSION_TIMEOUT_EXEMPT_URLS', [])
        return any(request.path.startswith(url) for url in exempt_urls)
    
    def _is_restaurant_staff(self, user):
        """
        Check if user is restaurant staff for role-based timeouts.
        
        Args:
            user: Django User object
            
        Returns:
            bool: True if user is restaurant staff, False otherwise
        """
        return user.is_staff or user.groups.filter(name='Restaurant Owner').exists()
    
    def _handle_timeout_response(self, request, message):
        """
        Handle session timeout response for AJAX and regular requests.
        
        Args:
            request: Django HTTP request object
            message: Timeout message to display
            
        Returns:
            HttpResponse: JSON response for AJAX, redirect for regular requests
        """
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'timeout',
                'message': message,
                'redirect_url': settings.LOGIN_URL
            }, status=401)
        else:
            return redirect(settings.LOGIN_URL)
    
    def _logout_user(self, request):
        """
        Log out the user and clear session data.
        
        Args:
            request: Django HTTP request object
        """
        try:
            logout(request)
            # Clear all session data
            request.session.flush()
        except Exception:
            # Fallback session clearing if logout fails
            request.session.clear()
