"""
Utility functions for the reviews app.

This module contains helper functions for various review-related operations,
including email notifications and content processing.
"""

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse

def send_review_submission_email(user, review, content_object, request=None):
    """
    Send an email notification when a review is submitted.
    
    Args:
        user: The user who submitted the review
        review: The review instance that was submitted
        content_object: The object being reviewed
        request: Optional request object for building absolute URLs
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Get site URL for absolute links in email
        site_url = settings.SITE_URL if hasattr(settings, 'SITE_URL') else ''
        if request:
            site_url = request.build_absolute_uri('/')[:-1]
        
        # Dashboard URL for the user
        dashboard_url = f"{site_url}{reverse('reviews:my_reviews')}"
        
        # Context for email templates
        context = {
            'user': user,
            'review': review,
            'content_object': content_object,
            'site_url': site_url,
            'dashboard_url': dashboard_url,
        }
        
        # Render email content
        subject = f"Thank You for Your Review on {getattr(settings, 'SITE_NAME', 'TravelGuide')}"
        text_content = render_to_string('reviews/emails/review_submitted.txt', context)
        html_content = render_to_string('reviews/emails/review_submitted.html', context)
        
        # Create email message
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
            reply_to=[getattr(settings, 'SUPPORT_EMAIL', settings.DEFAULT_FROM_EMAIL)],
        )
        msg.attach_alternative(html_content, "text/html")
        
        # Send email
        msg.send()
        return True
        
    except Exception as e:
        # Log the error but don't crash the request
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send review submission email: {str(e)}")
        return False
