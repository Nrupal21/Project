"""
Email Verification Views for the accounts app.

This module contains views related to email verification functionality,
including token verification and resend verification email.
"""

from django.shortcuts import render, redirect
from django.http import JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from django.urls import reverse
from django.template.loader import render_to_string
from django.core.mail import send_mail
import logging

from .models import UserProfile, VerificationToken  # Importing directly from models.py

logger = logging.getLogger(__name__)

def verify_email(request, token):
    """
    Verify a user's email address using a verification token.
    
    This view handles the verification link sent to the user's email.
    It validates the token and marks the user's email as verified if valid.
    
    Args:
        request: The HTTP request object
        token: The verification token from the URL
        
    Returns:
        HttpResponse: Rendered template with verification status
        
    Notes:
        - Accessible to both authenticated and unauthenticated users
        - Handles both GET and POST requests for flexibility
        - Provides appropriate feedback for success/failure
    """
    try:
        # Get the verification token object
        verification = VerificationToken.objects.get(
            token=token,
            token_type=VerificationToken.TokenType.EMAIL_VERIFICATION,
            is_used=False
        )
        
        # Check if token is expired
        if verification.expires_at < timezone.now():
            messages.error(request, 'This verification link has expired. Please request a new one.')
            return redirect('accounts:resend_verification')
            
        # Mark the token as used
        verification.mark_as_used()
        
        # Get the user and mark email as verified
        user = verification.user
        user_profile = UserProfile.objects.get(user=user)
        user_profile.is_verified = True
        user_profile.save()
        
        # Log the user in if they're not already
        if not request.user.is_authenticated:
            from django.contrib.auth import login
            login(request, user)
        
        messages.success(request, 'Your email has been successfully verified!')
        return redirect('accounts:profile')
        
    except VerificationToken.DoesNotExist:
        logger.warning(f"Invalid verification token used: {token}")
        messages.error(request, 'Invalid verification link. Please request a new one.')
        return redirect('accounts:resend_verification')
    except Exception as e:
        logger.error(f"Error verifying email with token {token}: {str(e)}")
        messages.error(request, 'An error occurred while verifying your email. Please try again.')
        return redirect('home')

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
            reverse('accounts:verify_email', kwargs={'token': verification_token.token})
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
