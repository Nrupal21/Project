"""
Updated views for the accounts app with VerificationToken integration.

This module contains the updated view functions that use the new
VerificationToken model for email verification.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
import logging

# Import models directly from models.py to avoid circular imports
from .models import UserProfile, VerificationToken

logger = logging.getLogger(__name__)

@login_required
def resend_verification_email(request):
    """
    Resend email verification link to the user's email.
    
    This view handles requests to resend the verification email when a user
    hasn't received the original email or the original link has expired.
    It creates a new verification token using the VerificationToken model
    and sends a fresh email with a styled HTML template.
    
    Args:
        request: The HTTP request object containing user data
        
    Returns:
        JsonResponse: JSON with success status and message
        
    Notes:
        - Only accessible to logged-in users
        - Uses POST method to prevent CSRF attacks
        - Rate-limited to 1 request per 5 minutes per user
        - Uses the VerificationToken model for secure token management
    """
    # Only allow POST requests to prevent CSRF attacks
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Only POST requests are allowed'
        }, status=405)
    
    # Get the current user - we know they're authenticated due to @login_required
    user = request.user
    
    # Check if user's email is already verified
    user_profile = UserProfile.objects.get(user=user)
    if user_profile.is_verified:
        return JsonResponse({
            'success': False,
            'message': 'Your email is already verified'
        })
    
    # Check for rate limiting - prevent abuse by limiting frequency of resends
    cache_key = f"email_verification_resend_{user.id}"
    resend_timestamp = cache.get(cache_key)
    
    if resend_timestamp and (timezone.now() - resend_timestamp).total_seconds() < 300:  # 5 minutes
        return JsonResponse({
            'success': False,
            'message': 'Please wait 5 minutes before requesting another verification email'
        })
    
    try:
        # Create a new verification token using our model
        verification_token = VerificationToken.create_token(
            user=user,
            token_type=VerificationToken.TokenType.EMAIL_VERIFICATION,
            expires_in_hours=24  # Token expires in 24 hours
        )
        
        # Construct verification URL
        verification_url = request.build_absolute_uri(
            reverse('accounts:verify_email', args=[verification_token.token])
        )
        
        # Send verification email with HTML template
        try:
            # Render the HTML email template
            email_html_message = render_to_string('emails/verify_email.html', {
                'user': user,
                'verification_url': verification_url,
                'expiry_hours': 24
            })
            
            # Send the email with both plain text and HTML versions
            send_mail(
                subject='Verify Your TravelGuide Account Email',
                message=f'Please click the link to verify your email: {verification_url}\n\nThis link will expire in 24 hours.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
                html_message=email_html_message
            )
            
            # Update cache to implement rate limiting (5 minutes)
            cache.set(cache_key, timezone.now(), 300)
            
            # Log successful email sending
            logger.info(f"Verification email sent to {user.email}")
            
            return JsonResponse({
                'success': True,
                'message': 'Verification email has been sent to your registered email address'
            })
            
        except Exception as e:
            # Log the error for server-side debugging
            logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
            
            return JsonResponse({
                'success': False,
                'message': 'Failed to send verification email. Please try again later.'
            }, status=500)
            
    except Exception as e:
        logger.error(f"Error creating verification token for user {user.id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while processing your request. Please try again.'
        }, status=500)
