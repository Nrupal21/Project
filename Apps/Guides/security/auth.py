"""
Custom authentication backend for two-factor authentication.

This module provides authentication backends and helpers for implementing
two-factor authentication in the TravelGuide application.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from .models import TwoFactorAuth, SecurityLog
from ipware import get_client_ip

User = get_user_model()


class TwoFactorAuthBackend(ModelBackend):
    """
    Custom authentication backend that supports two-factor authentication.
    
    This backend first authenticates with username/password, then redirects
    to a two-factor authentication verification page if 2FA is enabled
    for the user.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate a user and check if two-factor auth is required.
        
        Args:
            request: The HTTP request
            username: The username to authenticate
            password: The password to authenticate
            **kwargs: Additional arguments
            
        Returns:
            User: Authenticated user object or None
        """
        # First use the parent class to authenticate with username and password
        user = super().authenticate(request, username=username, password=password, **kwargs)
        
        if user and request and not kwargs.get('skip_twofa', False):
            # Check if user has 2FA enabled
            try:
                twofa = TwoFactorAuth.objects.get(user=user)
                
                if twofa.is_enabled:
                    if request:
                        # Store user ID in session for 2FA verification
                        request.session['twofa_user_id'] = str(user.id)
                        
                        # Store the next URL if available
                        if 'next' in request.GET:
                            request.session['twofa_next'] = request.GET.get('next')
                            
                        # Log the 2FA requirement
                        client_ip, _ = get_client_ip(request)
                        SecurityLog.objects.create(
                            level=SecurityLog.LEVEL_INFO,
                            event_type=SecurityLog.EVENT_2FA_REQUIRED,
                            user=user,
                            ip_address=client_ip,
                            user_agent=request.META.get('HTTP_USER_AGENT', ''),
                            description="Two-factor authentication required for login"
                        )
                        
                    # Return None to prevent automatic login
                    # The TwoFactorVerifyView will handle completion of authentication
                    return None
                    
            except TwoFactorAuth.DoesNotExist:
                # User doesn't have 2FA set up, proceed with normal authentication
                pass
                
        return user


def complete_login_after_2fa(request, user):
    """
    Helper function to complete login after successful 2FA verification.
    
    Args:
        request: The HTTP request
        user: The authenticated user
        
    Returns:
        bool: True if login was completed successfully
    """
    if 'twofa_user_id' in request.session:
        del request.session['twofa_user_id']
        
    # Log the successful 2FA verification
    client_ip, _ = get_client_ip(request)
    SecurityLog.objects.create(
        level=SecurityLog.LEVEL_SUCCESS,
        event_type=SecurityLog.EVENT_2FA_VERIFIED,
        user=user,
        ip_address=client_ip,
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        description="Two-factor authentication verified successfully"
    )
    
    return True
