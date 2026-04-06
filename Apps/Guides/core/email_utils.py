"""
Core email utilities for the TravelGuide application.

This module provides reusable email functionality that can be used
across all apps in the project for consistent email sending.
"""
import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.template import TemplateDoesNotExist

# Set up logger
logger = logging.getLogger('travelguide.emails')

def send_templated_email(recipient_email, subject, template_name, context, from_email=None):
    """
    Send an email using a template with comprehensive error handling.
    
    This function handles the complete email sending process including:
    - HTML template rendering
    - Plain text fallback creation
    - Comprehensive error handling
    - Detailed logging
    
    Args:
        recipient_email (str or list): Email address(es) to send to
        subject (str): Email subject line
        template_name (str): Path to the email template (without .html extension)
        context (dict): Context data to render in the template
        from_email (str, optional): Sender email address, defaults to settings.DEFAULT_FROM_EMAIL
        
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    if not recipient_email:
        logger.warning(f"Cannot send email: No recipient provided for template {template_name}")
        return False
        
    # Convert single email to list if needed
    recipient_list = [recipient_email] if isinstance(recipient_email, str) else recipient_email
    
    # Remove any empty emails from the list
    recipient_list = [email for email in recipient_list if email]
    if not recipient_list:
        logger.warning(f"Cannot send email: Empty recipient list for template {template_name}")
        return False
    
    # Use default from email if not provided
    sender = from_email or settings.DEFAULT_FROM_EMAIL
    
    # Check if email settings are configured
    if not settings.EMAIL_HOST or not settings.EMAIL_HOST_USER:
        logger.error(f"Email settings not properly configured. Check EMAIL_HOST and EMAIL_HOST_USER in settings.")
        return False
    
    try:
        # Render the HTML message using the template and context
        template_path = f'emails/{template_name}.html'
        try:
            html_message = render_to_string(template_path, context)
            # Create a plain text version for email clients that don't support HTML
            plain_message = strip_tags(html_message)
        except TemplateDoesNotExist:
            logger.error(f"Email template '{template_path}' does not exist")
            # Fallback to a basic plain text message
            plain_message = f"Email from TravelGuide: {subject}"
            html_message = None
        
        # Send the email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=sender,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=True  # Prevent exceptions from breaking the application flow
        )
        
        logger.info(f"Email '{subject}' sent successfully to {', '.join(recipient_list)}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email '{subject}' to {', '.join(recipient_list)}: {str(e)}", exc_info=True)
        logger.debug(f"Email details - To: {recipient_list}, From: {sender}, Subject: {subject}, Template: {template_name}")
        return False

def send_admin_notification_email(subject, message, url=None):
    """
    Send a notification email to all admin users.
    
    Args:
        subject (str): Email subject line
        message (str): Email message body
        url (str, optional): URL to include in the email for admin action
        
    Returns:
        bool: True if at least one email was sent successfully, False otherwise
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        # Get all admin users with email addresses
        admins = User.objects.filter(is_staff=True).exclude(email='').values_list('email', flat=True)
        if not admins:
            logger.warning("No admin users with valid email addresses found for notification")
            return False
        
        # Create context for the email template
        context = {
            'subject': subject,
            'message': message,
            'action_url': url,
            'site_url': f"{settings.SITE_PROTOCOL}://{settings.SITE_DOMAIN}" if hasattr(settings, 'SITE_PROTOCOL') and hasattr(settings, 'SITE_DOMAIN') else '/'
        }
        
        # Send the email to all admins
        return send_templated_email(
            recipient_email=list(admins),
            subject=subject,
            template_name='admin_notification',
            context=context
        )
        
    except Exception as e:
        logger.error(f"Failed to send admin notification: {str(e)}", exc_info=True)
        return False
