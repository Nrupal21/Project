"""
Email utility functions for the accounts app.

This module provides helper functions to send various types of emails
to users, including verification emails, password reset emails, and
guide application status notifications.
"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth import get_user_model
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Get the User model
User = get_user_model()

def send_templated_email(template_name, context, subject, to_email, from_email=None, attachments=None):
    """
    Send an HTML email using a template with fallback to plain text.
    
    This function renders an HTML template and sends it as an email with both
    HTML and plain text versions. It handles all the complexity of creating
    multipart emails and provides error logging.
    
    Args:
        template_name (str): The name of the template to render (without .html extension)
        context (dict): Context variables to pass to the template
        subject (str): Email subject line
        to_email (str or list): Recipient email address(es)
        from_email (str, optional): Sender email address. Defaults to DEFAULT_FROM_EMAIL setting.
        attachments (list, optional): List of (filename, content, mimetype) tuples
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    
    Example:
        >>> context = {'user': user, 'verification_url': url, 'expiry_hours': 48}
        >>> send_templated_email(
        ...     'emails/verification_email',
        ...     context,
        ...     'Verify Your TravelGuide Account',
        ...     user.email
        ... )
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL
    
    try:
        # Convert to list if it's a single email
        if isinstance(to_email, str):
            to_email = [to_email]
        
        # Render the HTML template
        html_content = render_to_string(f"{template_name}.html", context)
        
        # Create plain text version by stripping HTML
        text_content = strip_tags(html_content)
        
        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=to_email
        )
        
        # Attach HTML content
        email.attach_alternative(html_content, "text/html")
        
        # Add any attachments
        if attachments:
            for attachment in attachments:
                email.attach(*attachment)
        
        # Send the email
        email.send(fail_silently=False)
        
        logger.info(f"Email '{subject}' sent successfully to {', '.join(to_email)}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email '{subject}' to {to_email}: {str(e)}")
        return False


def send_verification_email(user, verification_url, expiry_hours=48):
    """
    Send an account verification email to a user.
    
    This function sends an email to a newly registered user with a link
    to verify their email address and activate their account.
    
    Args:
        user (User): The user object to send the verification email to
        verification_url (str): The URL for email verification
        expiry_hours (int, optional): Hours until verification link expires. Defaults to 48.
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    context = {
        'user': user,
        'verification_url': verification_url,
        'expiry_hours': expiry_hours,
    }
    
    subject = f"{settings.EMAIL_SUBJECT_PREFIX}Verify Your Email Address"
    
    return send_templated_email(
        'emails/verification_email',
        context,
        subject,
        user.email
    )


def send_password_reset_email(user, reset_url, expiry_hours=24):
    """
    Send a password reset email to a user.
    
    This function sends an email with a link to reset the user's password.
    
    Args:
        user (User): The user requesting password reset
        reset_url (str): The URL for password reset
        expiry_hours (int, optional): Hours until reset link expires. Defaults to 24.
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    context = {
        'user': user,
        'reset_url': reset_url,
        'expiry_hours': expiry_hours,
    }
    
    subject = f"{settings.EMAIL_SUBJECT_PREFIX}Reset Your Password"
    
    return send_templated_email(
        'emails/password_reset_email',
        context,
        subject,
        user.email
    )


def send_guide_application_status_email(user, status, review_comments=None):
    """
    Send a notification email about guide application status.
    
    This function notifies users about updates to their guide application status.
    
    Args:
        user (User): The user who applied to be a guide
        status (str): The new status of the application (e.g., 'APPROVED', 'REJECTED', 'UNDER_REVIEW')
        review_comments (str, optional): Comments from the reviewer. Defaults to None.
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    context = {
        'user': user,
        'application_status': status,
        'review_comments': review_comments,
    }
    
    if status == 'APPROVED':
        subject = f"{settings.EMAIL_SUBJECT_PREFIX}Congratulations! Your Guide Application Has Been Approved"
        template = 'emails/guide_approved_email'
    elif status == 'REJECTED':
        subject = f"{settings.EMAIL_SUBJECT_PREFIX}Update on Your Guide Application"
        template = 'emails/guide_rejected_email'
    else:
        subject = f"{settings.EMAIL_SUBJECT_PREFIX}Update on Your Guide Application Status"
        template = 'emails/guide_status_update_email'
    
    return send_templated_email(
        template,
        context,
        subject,
        user.email
    )


def send_destination_submission_notification(destination, submitter):
    """
    Send a notification email to managers and admins about a new destination submission.
    
    This function notifies all managers and admins when a local guide submits
    a new destination for review. The email includes details about the destination
    and a link to review it.
    
    Args:
        destination: The PendingDestination object that was submitted
        submitter: The User object who submitted the destination
    
    Returns:
        bool: True if emails were sent successfully, False otherwise
    
    Example:
        >>> send_destination_submission_notification(pending_destination, request.user)
    """
    # Get all managers and admins
    managers_and_admins = User.objects.filter(
        role__in=[User.Role.MANAGER, User.Role.ADMIN],
        is_active=True
    )
    
    if not managers_and_admins.exists():
        logger.warning("No managers or admins found to notify about destination submission")
        return False
    
    # Prepare email context
    context = {
        'destination': destination,
        'submitter': submitter,
        'review_url': f"{settings.BASE_URL}/admin/destinations/pendingdestination/{destination.id}/change/",
        'dashboard_url': f"{settings.BASE_URL}/admin/destinations/pendingdestination/",
    }
    
    subject = f"{settings.EMAIL_SUBJECT_PREFIX}New Destination Submission: {destination.name}"
    
    # Get all manager and admin emails
    recipient_emails = list(managers_and_admins.values_list('email', flat=True))
    
    # Send the email
    return send_templated_email(
        'emails/destination_submission_notification',
        context,
        subject,
        recipient_emails
    )
