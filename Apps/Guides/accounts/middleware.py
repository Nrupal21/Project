"""
Custom middleware for OTP verification.

This module contains middleware to enforce OTP verification for protected views.
"""
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

class OTPVerificationMiddleware:
    """
    Middleware to ensure OTP verification for protected views.
    
    This middleware checks if the user has completed OTP verification
    before accessing protected views.
    """
    
    def __init__(self, get_response):
        """
        Initialize the middleware.
        
        Args:
            get_response: The next middleware in the chain
        """
        self.get_response = get_response
        self.login_url = getattr(settings, 'LOGIN_URL', '/login/')
        self.otp_required_url_names = getattr(settings, 'OTP_REQUIRED_URL_NAMES', [])
        # Don't reverse URLs here to avoid import-time URL resolution
        self.otp_request_url = '/otp/request-otp/'
        self.otp_verify_url = '/otp/verify-otp/'
    
    def __call__(self, request):
        """
        Process the request.
        
        Args:
            request: The HTTP request object
            
        Returns:
            HttpResponse: The response from the next middleware or view
        """
        # Skip OTP check for unauthenticated users (they'll be caught by login_required)
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Skip OTP check for OTP-related URLs
        if request.path in [self.login_url, self.otp_request_url, self.otp_verify_url]:
            return self.get_response(request)
        
        # Check if the current URL requires OTP verification
        requires_otp = False
        for url_name in self.otp_required_url_names:
            try:
                if request.resolver_match and request.resolver_match.url_name == url_name:
                    requires_otp = True
                    break
            except AttributeError:
                continue
        
        # If OTP is required but not verified, redirect to OTP verification
        if requires_otp and not request.session.get('otp_verified', False):
            return redirect('otp:request_otp')
        
        return self.get_response(request)
