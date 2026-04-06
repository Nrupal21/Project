"""
Utility functions for the bookings app.

This module provides reusable functions for the bookings app,
including email sending, validation, and data processing.
"""
import logging
from django.conf import settings
from core.email_utils import send_templated_email

# Set up logger
logger = logging.getLogger('travelguide.bookings')

def send_booking_confirmation_email(booking):
    """
    Send a booking confirmation email to the user.
    
    This function sends an email to the user confirming their booking
    with all relevant details about the tour, dates, and payment status.
    
    Args:
        booking: The Booking object for which to send confirmation
        
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    if not booking or not booking.user or not booking.user.email:
        logger.warning("Cannot send booking confirmation: Invalid booking or missing user email")
        return False
        
    # Create context for the email template
    context = {
        'user': booking.user,
        'booking': booking,
        'site_url': f"{settings.SITE_PROTOCOL}://{settings.SITE_DOMAIN}" if hasattr(settings, 'SITE_PROTOCOL') and hasattr(settings, 'SITE_DOMAIN') else '/'
    }
    
    # Build the subject line
    if booking.is_paid:
        subject = f"Booking Confirmed: {booking.tour.name}"
    else:
        subject = f"Booking Received: {booking.tour.name} - Payment Pending"
    
    # Send the email
    return send_templated_email(
        recipient_email=booking.user.email,
        subject=subject,
        template_name='booking_confirmation',
        context=context
    )

def send_booking_update_email(booking, update_type):
    """
    Send an email notification about booking status updates.
    
    This function sends an email to the user when their booking status
    changes, such as when it's canceled, rescheduled, or completed.
    
    Args:
        booking: The Booking object that was updated
        update_type: The type of update (canceled, rescheduled, completed)
        
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    if not booking or not booking.user or not booking.user.email:
        logger.warning("Cannot send booking update: Invalid booking or missing user email")
        return False
    
    # Set subject and template based on update type
    if update_type == 'canceled':
        subject = f"Booking Canceled: {booking.tour.name}"
        template_name = 'booking_canceled'
    elif update_type == 'rescheduled':
        subject = f"Booking Rescheduled: {booking.tour.name}"
        template_name = 'booking_rescheduled'
    elif update_type == 'completed':
        subject = f"Tour Completed: {booking.tour.name} - Leave a Review"
        template_name = 'booking_completed'
    else:
        subject = f"Booking Update: {booking.tour.name}"
        template_name = 'booking_update'
    
    # Create context for the email template
    context = {
        'user': booking.user,
        'booking': booking,
        'update_type': update_type,
        'site_url': f"{settings.SITE_PROTOCOL}://{settings.SITE_DOMAIN}" if hasattr(settings, 'SITE_PROTOCOL') and hasattr(settings, 'SITE_DOMAIN') else '/'
    }
    
    # Send the email
    return send_templated_email(
        recipient_email=booking.user.email,
        subject=subject,
        template_name=template_name,
        context=context
    )

def notify_guides_about_booking(booking):
    """
    Send notification emails to tour guides about new bookings.
    
    This function notifies the relevant tour guides when a new booking
    is made for one of their tours.
    
    Args:
        booking: The new Booking object
        
    Returns:
        bool: True if at least one email was sent successfully, False otherwise
    """
    if not booking or not booking.tour:
        logger.warning("Cannot notify guides: Invalid booking or tour")
        return False
    
    # Get guide emails - in a real app, would fetch from tour.guides or similar
    # For now, just send to admin email as a placeholder
    guide_emails = [settings.DEFAULT_FROM_EMAIL]
    
    if not guide_emails:
        logger.warning(f"No guides found for tour {booking.tour.id}")
        return False
    
    # Create context for the email template
    context = {
        'booking': booking,
        'tour': booking.tour,
        'site_url': f"{settings.SITE_PROTOCOL}://{settings.SITE_DOMAIN}" if hasattr(settings, 'SITE_PROTOCOL') and hasattr(settings, 'SITE_DOMAIN') else '/'
    }
    
    # Send the notification email
    return send_templated_email(
        recipient_email=guide_emails,
        subject=f"New Booking: {booking.tour.name}",
        template_name='guide_booking_notification',
        context=context
    )
