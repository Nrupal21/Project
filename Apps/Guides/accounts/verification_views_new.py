"""
Updated Email Verification Views Module.

This module contains view functions for email verification flows in the TravelGuide application,
using the new VerificationToken model for secure token management.

All views include appropriate security measures, error handling, and user feedback mechanisms.
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_http_methods
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, Http404
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.contrib.auth import get_user_model, login
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.urls import reverse

from .models import UserProfile, VerificationToken

# Configure logger
logger = logging.getLogger(__name__)

# Get the User model
User = get_user_model()

def verify_email_view(request, token):
    """
    Handle the email verification link clicked by users.
    
    This view is accessed when a user clicks on the verification link in their email.
    It validates the token, updates the user's verification status, and provides
    appropriate feedback.
    
    Args:
        request: HttpRequest object
        token: Verification token to validate
        
    Returns:
        HttpResponse: Rendered verification confirmation page or error page
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
            return redirect('accounts:resend_verification_email')
            
        # Mark the token as used
        verification.mark_as_used()
        
        # Get the user and mark email as verified
        user = verification.user
        user_profile = UserProfile.objects.get(user=user)
        user_profile.is_verified = True
        user_profile.save()
        
        # Log the user in if they're not already
        if not request.user.is_authenticated:
            login(request, user)
        
        messages.success(request, 'Your email has been successfully verified!')
        return redirect('accounts:profile')
        
    except VerificationToken.DoesNotExist:
        logger.warning(f"Invalid verification token used: {token}")
        messages.error(request, 'Invalid verification link. Please request a new one.')
        return redirect('accounts:resend_verification_email')
    except Exception as e:
        logger.error(f"Error verifying email with token {token}: {str(e)}")
        messages.error(request, 'An error occurred while verifying your email. Please try again.')
        return redirect('home')

def verification_required_view(request):
    """
    Show a page informing users that email verification is required.
    
    This view is shown when a user attempts to access a feature that requires
    email verification, but their email hasn't been verified yet.
    
    Args:
        request: HttpRequest object
        
    Returns:
        HttpResponse: Rendered verification required page
    """
    if not request.user.is_authenticated:
        return redirect('accounts:login')
        
    # Check if user is already verified (in case they got here by direct URL)
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        if user_profile.is_verified:
            return redirect('accounts:profile')
    except UserProfile.DoesNotExist:
        pass
        
    return render(request, 'accounts/verification_required.html', {
        'title': 'Email Verification Required',
        'user': request.user,
    })

@login_required
@require_http_methods(["POST"])
def resend_verification_email_view(request):
    """
    Resend the verification email to the user.
    
    This endpoint is called via AJAX when a user requests a new verification email.
    It includes rate limiting to prevent abuse.
    
    Args:
        request: HttpRequest object
        
    Returns:
        JsonResponse: JSON response with success/error message
    """
    # Check for rate limiting - prevent abuse by limiting frequency of resends
    cache_key = f"email_verification_resend_{request.user.id}"
    resend_timestamp = cache.get(cache_key)
    
    if resend_timestamp and (timezone.now() - resend_timestamp).total_seconds() < 300:  # 5 minutes
        return JsonResponse({
            'success': False,
            'message': 'Please wait 5 minutes before requesting another verification email.'
        }, status=429)
    
    try:
        # Get the user's profile
        user_profile = UserProfile.objects.get(user=request.user)
        
        # Check if already verified
        if user_profile.is_verified:
            return JsonResponse({
                'success': False,
                'message': 'Your email is already verified.'
            }, status=400)
        
        # Create a new verification token
        verification_token = VerificationToken.create_token(
            user=request.user,
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
                'user': request.user,
                'verification_url': verification_url,
                'expiry_hours': 24
            })
            
            # Send the email with both plain text and HTML versions
            send_mail(
                subject='Verify Your TravelGuide Account Email',
                message=f'Please click the link to verify your email: {verification_url}\n\nThis link will expire in 24 hours.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[request.user.email],
                fail_silently=False,
                html_message=email_html_message
            )
            
            # Update cache to implement rate limiting (5 minutes)
            cache.set(cache_key, timezone.now(), 300)
            
            # Log successful email sending
            logger.info(f"Verification email sent to {request.user.email}")
            
            return JsonResponse({
                'success': True,
                'message': 'A new verification email has been sent to your email address.'
            })
            
        except Exception as e:
            # Log the error for server-side debugging
            logger.error(f"Failed to send verification email to {request.user.email}: {str(e)}")
            
            return JsonResponse({
                'success': False,
                'message': 'Failed to send verification email. Please try again later.'
            }, status=500)
            
    except Exception as e:
        logger.error(f"Error in resend_verification_email_view: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while processing your request.'
        }, status=500)
