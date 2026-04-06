"""
Utility functions for the accounts app.

This module contains helper functions used across the accounts application,
including IP address handling and authentication utilities.
"""
import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator

# Set up logger for this module
logger = logging.getLogger('travelguide.accounts')

User = get_user_model()

def get_client_ip(request):
    """
    Get the client's IP address from the request object with robust error handling.
    
    This function extracts the client IP from various request headers with fallbacks:
    1. First checks the X-Forwarded-For header (common for proxied requests)
    2. If not available, uses the REMOTE_ADDR from request.META
    3. If request or META is None or any other error occurs, returns a safe default
    
    Args:
        request: The Django HTTP request object containing client information
        
    Returns:
        str: The client's IP address or '0.0.0.0' if not found/error occurs
    """
    try:
        # Check if request and META exist
        if request is None or not hasattr(request, 'META') or request.META is None:
            return '0.0.0.0'
            
        # Try to get the X-Forwarded-For header
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        
        if x_forwarded_for:
            # X-Forwarded-For can contain multiple IPs (client, proxy1, proxy2, ...)
            # The leftmost IP is the original client IP
            try:
                ip = x_forwarded_for.split(',')[0].strip()
                if ip:  # Make sure we got a non-empty string
                    return ip
            except (AttributeError, IndexError):
                # If splitting fails or x_forwarded_for isn't a string with commas
                pass
                
        # Fallback to REMOTE_ADDR or the default
        return request.META.get('REMOTE_ADDR', '0.0.0.0')
        
    except Exception:
        # Catch any unexpected errors and return a safe default
        # This ensures the function never raises exceptions
        return '0.0.0.0'

def complete_login_after_twofa(request, user, redirect_to=None):
    """
    Complete the login process after two-factor authentication.
    
    Args:
        request: The HTTP request object
        user: The user object to log in
        redirect_to: Optional URL to redirect to after login
        
    Returns:
        HttpResponseRedirect: Redirect response to the appropriate page
    """
    from django.contrib.auth import login
    from django.shortcuts import redirect
    from django.urls import reverse
    from django.conf import settings
    
    # Log the user in
    login(request, user)
    
    # Log the successful login
    from .models import SecurityLog
    SecurityLog.objects.create(
        user=user,
        event_type=SecurityLog.EVENT_LOGIN_SUCCESS,
        description="Successful login with 2FA",
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    # Redirect to the specified URL or the default success URL
    redirect_url = redirect_to or getattr(settings, 'LOGIN_REDIRECT_URL', '/')
    return redirect(redirect_url)

def send_password_reset_email(user, site_domain, use_https=False, token_generator=default_token_generator):    
    """
    Send a password reset email using the reusable email utility.
    
    Args:
        user: The user object requesting the password reset
        site_domain: The domain name of the site for the reset link
        use_https: Whether to use HTTPS in the reset link
        token_generator: Token generator for creating reset tokens
        
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    if not user.email:
        logger.warning(f"Cannot send password reset email: No email address for user {user.username}")
        return False
    
    # Generate the password reset token
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = token_generator.make_token(user)
    
    # Create the password reset URL
    protocol = 'https' if use_https else 'http'
    reset_url = f"{protocol}://{site_domain}/accounts/reset/{uid}/{token}/"
    
    # Expiry time for the token (usually 1-3 days depending on Django settings)
    # Default is PASSWORD_RESET_TIMEOUT which is typically 3 days (259200 seconds)
    expiry_hours = getattr(settings, 'PASSWORD_RESET_TIMEOUT', 259200) // 3600
    
    # Create context for the email template
    context = {
        'user': user,
        'reset_url': reset_url,
        'expiry_hours': expiry_hours,
        'site_url': f"{protocol}://{site_domain}"
    }
    
    # Send the password reset email
    return send_templated_email(
        recipient_email=user.email,
        subject="Reset Your TravelGuide Password",
        template_name='password_reset',
        context=context
    )

# Add any additional utility functions below

def send_welcome_email(user):
    """
    Send a welcome email to a newly registered user.
    
    Args:
        user: The user object to send the welcome email to
    """
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
    from django.conf import settings
    
    subject = 'Welcome to TravelGuide!'
    html_message = render_to_string('emails/welcome.html', {'user': user})
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=True
    )


def send_guide_application_confirmation(user, application):
    """
    Send a confirmation email to a user after they submit a guide application.
    
    Uses the centralized email utility to send a templated email with consistent
    styling and error handling. Includes personalized details about their application
    and explains the next steps in the approval process.
    
    Args:
        user: The user object who submitted the application
        application: The GuideApplication object that was submitted
        
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    from django.conf import settings
    from django.template.exceptions import TemplateDoesNotExist
    from core.email_utils import send_templated_email
    
    if not user.email:
        logger.warning(f"Cannot send guide application confirmation: User {user.id} has no email address")
        return False
    
    # Create context for the email template
    context = {
        'user': user,
        'application_id': application.id,
        'application_date': application.application_date,
        'site_url': f"{settings.SITE_PROTOCOL}://{settings.SITE_DOMAIN}" if hasattr(settings, 'SITE_PROTOCOL') and hasattr(settings, 'SITE_DOMAIN') else '/'
    }
    
    try:
        # Use the centralized email utility
        return send_templated_email(
            recipient_email=user.email,
            subject='Your Local Guide Application Submitted Successfully!',
            template_name='emails/guide_application_confirmation.html',
            context=context
        )
    except Exception as e:
        logger.error(f"Failed to send guide application confirmation email: {str(e)}", exc_info=True)
        return False
        logger.debug(f"Email details - To: {user.email}, From: {settings.DEFAULT_FROM_EMAIL}, Subject: {subject}")
        return False


def send_admin_notification(subject, message, url=None):
    """
    Send a notification email to all admin users.
    
    This function sends an email to all users with admin privileges in the system.
    It's used for important system notifications like new guide applications.
    
    Args:
        subject (str): Email subject line
        message (str): Email message body (plain text)
        url (str, optional): URL to include in the email for admin action
        
    Returns:
        bool: True if at least one email was sent successfully, False otherwise
    """
    try:
        # Get all admin users with email addresses
        admins = User.objects.filter(is_staff=True).exclude(email='').values_list('email', flat=True)
        if not admins:
            logger.warning("No admin users with valid email addresses found for notification")
            return False
        
        # Check if email settings are configured properly
        if not settings.EMAIL_HOST or not settings.EMAIL_HOST_USER:
            logger.error("Email settings not properly configured. Check EMAIL_HOST and EMAIL_HOST_USER in settings.")
            return False
        
        # Format the message with the URL if provided
        full_message = message
        if url:
            full_message += f"\n\nAction required: {url}"
            
        # Format HTML version with better styling if this is a high-priority notification
        html_message = None
        if 'application' in subject.lower() or 'urgent' in subject.lower():
            html_message = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #5b21b6; border-bottom: 2px solid #8b5cf6; padding-bottom: 10px;">{subject}</h2>
                <p style="line-height: 1.5;">{message}</p>
                {f'<p><a href="{url}" style="background-color: #6d28d9; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; display: inline-block; margin-top: 15px;">Take Action</a></p>' if url else ''}
                <p style="color: #6b7280; font-size: 0.9em; margin-top: 30px;">This is an automated notification from the TravelGuide system.</p>
            </div>
            """
        
        # Send the email with fail_silently=True to prevent breaking the application flow
        from django.core.mail import send_mail
        send_mail(
            subject=subject,
            message=full_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=list(admins),
            html_message=html_message,
            fail_silently=True
        )
        
        # Log success message with recipient count
        logger.info(f"Admin notification '{subject}' sent to {len(admins)} admins")
        return True
        
    except Exception as e:
        # Comprehensive error logging with exception details
        logger.error(f"Failed to send admin notification: {str(e)}", exc_info=True)
        logger.debug(f"Email details - Subject: {subject}, To: admin users, From: {settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'Not configured'}")
        return False
