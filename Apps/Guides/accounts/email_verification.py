"""
Email Verification Module.

This module handles email verification functionality for the TravelGuide application,
including token generation, validation, sending verification emails, and handling
the verification process flow.

The module implements security best practices for token generation and validation
to ensure secure email verification.
"""

import secrets
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import get_user_model

# Configure logger
logger = logging.getLogger(__name__)

# Get the User model
User = get_user_model()


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """
    Token generator for email verification.
    
    Extends Django's PasswordResetTokenGenerator to create secure,
    time-limited tokens for email verification. Each token is unique
    to a user and becomes invalid once the user's email is verified.
    """
    
    def _make_hash_value(self, user, timestamp):
        """
        Create a unique hash value for the verification token.
        
        This method ensures the token becomes invalid when the user's email
        is verified by including the is_verified status in the hash.
        
        Args:
            user: User object for whom to generate token
            timestamp: Current timestamp for token generation
            
        Returns:
            str: Hash value incorporating user data and timestamp
        """
        # Get verification status from user profile if it exists
        is_verified = False
        if hasattr(user, 'profile'):
            is_verified = user.profile.is_verified
            
        # Create a unique hash combining user data, timestamp, and verification status
        # This ensures token invalidation when verification status changes
        login_timestamp = '' if user.last_login is None else user.last_login.replace(microsecond=0, tzinfo=None)
        return f"{user.pk}{user.email}{login_timestamp}{timestamp}{is_verified}"


# Create an instance of the token generator
email_verification_token_generator = EmailVerificationTokenGenerator()


def generate_verification_token(user):
    """
    Generate a secure verification token for a user.
    
    Creates a URL-safe token tied to the user's account that can be
    included in verification emails.
    
    Args:
        user: User object for whom to generate token
        
    Returns:
        str: Verification token
    """
    # Generate token using the token generator
    return email_verification_token_generator.make_token(user)


def encode_user_id(user):
    """
    Encode a user ID in a URL-safe format.
    
    Converts the user ID to a URL-safe base64 encoded string
    for inclusion in verification URLs.
    
    Args:
        user: User object whose ID will be encoded
        
    Returns:
        str: URL-safe base64 encoded user ID
    """
    # Convert user ID to bytes and encode as URL-safe base64
    return urlsafe_base64_encode(force_bytes(user.pk))


def decode_user_id(uidb64):
    """
    Decode a user ID from URL-safe base64 format.
    
    Converts the encoded ID back to the original user ID.
    
    Args:
        uidb64: URL-safe base64 encoded user ID
        
    Returns:
        int: Original user ID
        
    Raises:
        ValueError: If decoding fails
    """
    try:
        # Decode the URL-safe base64 string to get the user ID
        uid = force_str(urlsafe_base64_decode(uidb64))
        return int(uid)
    except (TypeError, ValueError, OverflowError):
        raise ValueError("Invalid user ID encoding")


def validate_verification_token(user, token):
    """
    Validate a verification token for a user.
    
    Checks if the provided token is valid for the specified user.
    
    Args:
        user: User object to check the token against
        token: Verification token to validate
        
    Returns:
        bool: True if token is valid, False otherwise
    """
    # Check if the token is valid for this user
    return email_verification_token_generator.check_token(user, token)


def get_verification_url(request, user):
    """
    Generate a complete verification URL for a user.
    
    Creates a full URL including the verification token that the user
    can click on to verify their email address.
    
    Args:
        request: HttpRequest object for determining site domain
        user: User object for whom to generate verification URL
        
    Returns:
        str: Complete verification URL
    """
    # Get current site domain
    current_site = get_current_site(request)
    
    # Encode user ID
    uidb64 = encode_user_id(user)
    
    # Generate verification token
    token = generate_verification_token(user)
    
    # Build verification URL path
    verification_path = reverse('accounts:verify_email', kwargs={'uidb64': uidb64, 'token': token})
    
    # Create full URL with site domain and protocol (http/https)
    protocol = 'https' if request.is_secure() else 'http'
    verification_url = f"{protocol}://{current_site.domain}{verification_path}"
    
    return verification_url


def send_verification_email(request, user):
    """
    Send a verification email to a user.
    
    Creates and sends an email with a verification link to the user's
    registered email address.
    
    Args:
        request: HttpRequest object for determining site domain
        user: User object to whom to send the verification email
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Get verification URL
        verification_url = get_verification_url(request, user)
        
        # Get current site domain
        current_site = get_current_site(request)
        
        # Prepare email context
        context = {
            'user': user,
            'verification_url': verification_url,
            'site_url': f"{'https' if request.is_secure() else 'http'}://{current_site.domain}",
            'site_name': current_site.name,
            'valid_days': settings.EMAIL_VERIFICATION_DAYS if hasattr(settings, 'EMAIL_VERIFICATION_DAYS') else 7
        }
        
        # Render email templates
        html_content = render_to_string('accounts/email/email_verification.html', context)
        text_content = strip_tags(html_content)  # Create plain text version
        
        # Create email message
        subject = f"Verify your email address for {current_site.name}"
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = user.email
        
        # Create the email message object
        email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        email.attach_alternative(html_content, "text/html")
        
        # Send the email
        email.send()
        
        logger.info(f"Verification email sent to {user.email}")
        return True
        
    except Exception as e:
        # Log any errors
        logger.error(f"Error sending verification email to {user.email}: {str(e)}")
        return False


def verify_user_email(uidb64, token):
    """
    Verify a user's email using the verification token.
    
    Checks the token validity and marks the user's email as verified
    if the token is valid.
    
    Args:
        uidb64: URL-safe base64 encoded user ID
        token: Verification token to validate
        
    Returns:
        tuple: (bool, User) - (Success status, User object or None)
    """
    try:
        # Decode user ID
        uid = decode_user_id(uidb64)
        user = User.objects.get(pk=uid)
        
        # Validate token
        if validate_verification_token(user, token):
            # Mark user as verified
            if hasattr(user, 'profile'):
                user.profile.is_verified = True
                user.profile.save()
                
                # Log successful verification
                logger.info(f"Email verified for user {user.email}")
                return True, user
                
        # If token validation failed
        logger.warning(f"Invalid verification attempt for user ID {uid}")
        return False, None
        
    except (User.DoesNotExist, ValueError) as e:
        # Log error
        logger.error(f"Email verification error: {str(e)}")
        return False, None


def check_verification_status(user):
    """
    Check if a user's email has been verified.
    
    Args:
        user: User object to check
        
    Returns:
        bool: True if email is verified, False otherwise
    """
    # Check if user has a profile with verification status
    if hasattr(user, 'profile'):
        return user.profile.is_verified
    
    # Default to unverified if no profile exists
    return False


def verification_required(view_func):
    """
    Decorator to require email verification for a view.
    
    Redirects to a verification required page if the user's email
    is not verified.
    
    Args:
        view_func: The view function to wrap
        
    Returns:
        function: Wrapped view function
    """
    from django.contrib.auth.decorators import login_required
    from django.shortcuts import redirect
    from functools import wraps
    
    @login_required
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check if user's email is verified
        if check_verification_status(request.user):
            # If verified, proceed to the view
            return view_func(request, *args, **kwargs)
        else:
            # If not verified, redirect to verification required page
            return redirect('accounts:verification_required')
            
    return _wrapped_view
