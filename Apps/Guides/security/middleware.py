"""
Security middleware for the website.

This module implements middleware components that intercept requests
to handle security features such as tracking failed login attempts,
logging security events, and enforcing security policies.
"""

import re
from ipware import get_client_ip
from django.utils import timezone
from django.urls import resolve, reverse
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseRedirect

from .models import FailedLoginAttempt, SecurityLog


class SecurityMiddleware:
    """
    Middleware for handling various security-related tasks.
    
    This middleware intercepts requests to implement security features
    such as failed login tracking, security logging, and more.
    """
    
    def __init__(self, get_response):
        """
        Initialize the middleware with the get_response callable.
        
        Args:
            get_response: Callable that processes the request into a response
        """
        self.get_response = get_response
        # Login URL pattern to detect login attempts
        self.login_url_pattern = re.compile(r'^/accounts/login/$')
        
    def __call__(self, request):
        """
        Process each request through the middleware.
        
        This method performs several security checks:
        1. Checks for account lockout on login attempts
        2. Enforces two-factor authentication for users who have completed first auth step
        3. Allows certain paths to be accessed without 2FA (static files, the 2FA verification page itself)
        
        Args:
            request: The HTTP request object
            
        Returns:
            HttpResponse: The processed response or a redirect if security checks fail
        """
        # Check for account lockout if this is a login request
        if request.method == 'POST' and self.login_url_pattern.match(request.path):
            username = request.POST.get('username', '')
            
            if username:
                # Get client IP address
                client_ip, _ = get_client_ip(request)
                
                # Check if the account is locked
                is_locked, minutes = FailedLoginAttempt.is_account_locked(username, client_ip)
                
                if is_locked:
                    # Log the blocked attempt
                    SecurityLog.objects.create(
                        level=SecurityLog.LEVEL_WARNING,
                        event_type=SecurityLog.EVENT_LOGIN_BLOCKED,
                        ip_address=client_ip,
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        description=f"Login blocked due to account lockout: {username}",
                        additional_data={
                            'username': username,
                            'minutes_remaining': minutes
                        }
                    )
                    
                    # Add a message and redirect back to login page
                    messages.error(
                        request, 
                        f"This account has been temporarily locked due to too many failed login attempts. "
                        f"Please try again in {minutes} minute{'s' if minutes != 1 else ''}."
                    )
                    return HttpResponseRedirect(reverse('accounts:login'))
        
        # Check if user needs 2FA verification
        if 'twofa_user_id' in request.session:
            # Get the current path and check if it's exempt from 2FA enforcement
            current_path = request.path.lstrip('/')
            
            # Allow static files, media files, and the 2FA verification page itself
            twofa_exempt_paths = [
                'static/',
                'media/',
                'security/twofa/verify/',
                'security/twofa/backup/',
                'accounts/logout/',  # Always allow logout
            ]
            
            # Check if current path is exempt
            is_exempt = any(current_path.startswith(exempt_path) for exempt_path in twofa_exempt_paths)
            
            # If path is not exempt and user needs 2FA, redirect to verification page
            if not is_exempt:
                # Log the redirect for security audit
                SecurityLog.objects.create(
                    level=SecurityLog.LEVEL_INFO,
                    event_type=SecurityLog.EVENT_2FA_REQUIRED,
                    user_id=request.session.get('twofa_user_id'),  # User not fully authenticated yet
                    ip_address=get_client_ip(request)[0],
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    description=f"User redirected to 2FA verification from: {request.path}"
                )
                
                # Redirect to 2FA verification
                return HttpResponseRedirect(reverse('security:twofa_verify'))
        
        # Process the request
        response = self.get_response(request)
        
        # Return the response
        return response


class LoginAttemptMiddleware:
    """
    Middleware specifically for tracking failed login attempts.
    
    This middleware works with Django's authentication system to
    track failed login attempts and implement account lockouts.
    """
    
    def __init__(self, get_response):
        """
        Initialize the middleware with the get_response callable.
        
        Args:
            get_response: Callable that processes the request into a response
        """
        self.get_response = get_response
        
    def __call__(self, request):
        """
        Process each request through the middleware.
        
        Args:
            request: The HTTP request object
            
        Returns:
            HttpResponse: The processed response
        """
        # Process the request and get the response
        response = self.get_response(request)
        return response
    
    def process_template_response(self, request, response):
        """
        Process the template response to detect failed login attempts.
        
        This hook runs after the view is called and the template response
        is generated, allowing us to check for authentication errors.
        
        Args:
            request: The HTTP request object
            response: The template response object
            
        Returns:
            TemplateResponse: The processed template response
        """
        # Check if this is a failed login attempt
        if (request.method == 'POST' and 
            resolve(request.path_info).url_name == 'login' and
            not request.user.is_authenticated and
            hasattr(response, 'context_data') and
            response.context_data.get('form') and
            response.context_data['form'].errors):
            
            # Extract username from POST data
            username = request.POST.get('username', '')
            
            # Get client IP address
            client_ip, _ = get_client_ip(request)
            
            if username and client_ip:
                # Record the failed attempt
                is_locked, minutes = FailedLoginAttempt.record_failure(
                    username=username,
                    ip_address=client_ip,
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                # Log the failed attempt
                SecurityLog.objects.create(
                    level=SecurityLog.LEVEL_WARNING,
                    event_type=SecurityLog.EVENT_LOGIN_FAIL,
                    ip_address=client_ip,
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    description=f"Failed login attempt for username: {username}",
                    additional_data={
                        'username': username,
                        'is_locked': is_locked,
                        'minutes_until_unlock': minutes
                    }
                )
                
                # If account is now locked, add a message
                if is_locked:
                    messages.error(
                        request, 
                        f"Too many failed login attempts. This account has been locked for {minutes} minutes."
                    )
        
        return response


class SecurityAuditMiddleware:
    """
    Middleware for auditing security-related events.
    
    Records important security events like user logins, logouts,
    admin actions, and other security-relevant activities.
    """
    
    def __init__(self, get_response):
        """
        Initialize the middleware with the get_response callable.
        
        Args:
            get_response: Callable that processes the request into a response
        """
        self.get_response = get_response
        
    def __call__(self, request):
        """
        Process each request through the middleware.
        
        Args:
            request: The HTTP request object
            
        Returns:
            HttpResponse: The processed response
        """
        # Save current auth state to detect changes
        was_authenticated = request.user.is_authenticated
        username = request.user.username if was_authenticated else None
        
        # Process the request
        response = self.get_response(request)
        
        # Log successful login (detected by auth state change)
        if not was_authenticated and request.user.is_authenticated:
            client_ip, _ = get_client_ip(request)
            
            SecurityLog.objects.create(
                level=SecurityLog.LEVEL_INFO,
                event_type=SecurityLog.EVENT_LOGIN,
                user=request.user,
                ip_address=client_ip,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                description=f"User successfully logged in: {request.user.username}"
            )
        
        # Log logout (detected by session key change in logout view)
        path = request.path.lstrip('/')
        if was_authenticated and path.startswith('accounts/logout'):
            client_ip, _ = get_client_ip(request)
            
            SecurityLog.objects.create(
                level=SecurityLog.LEVEL_INFO,
                event_type=SecurityLog.EVENT_LOGOUT,
                user_id=request.session.get('_auth_user_id'),  # Store ID directly as user is being logged out
                ip_address=client_ip,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                description=f"User logged out: {username}"
            )
        
        # Return the response
        return response
