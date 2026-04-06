"""
Notification signals module for the TravelGuide application.

This module defines signal handlers and connections for the notifications system,
allowing other apps to trigger notifications using Django's signals mechanism.

The notification system uses the indigo/violet color palette for all UI elements
to maintain visual consistency across the application.

Signals defined here connect various app events (like destination approval,
booking confirmations, etc.) to notification creation actions.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver, Signal
from django.contrib.auth import get_user_model
from django.conf import settings

from .models import Notification

# Custom signals for notification events
destination_approved_signal = Signal()
destination_rejected_signal = Signal()
booking_confirmed_signal = Signal()
tour_reminder_signal = Signal()
emergency_alert_signal = Signal()

User = get_user_model()

@receiver(destination_approved_signal)
def create_destination_approval_notification(sender, **kwargs):
    """
    Create a notification when a destination is approved.
    
    Parameters:
    -----------
    sender: The sender of the signal
    kwargs: Additional keyword arguments containing:
        - user_id: ID of the user who submitted the destination
        - destination_id: ID of the destination that was approved
        - destination_name: Name of the approved destination
    
    Returns:
    --------
    None
    """
    user_id = kwargs.get('user_id')
    destination_id = kwargs.get('destination_id')
    destination_name = kwargs.get('destination_name', 'your destination')
    
    if user_id:
        Notification.objects.create(
            user_id=user_id,
            title="Destination Approved",
            content=f"Your destination '{destination_name}' has been approved and is now live.",
            notification_type='APPROVAL',
            object_id=destination_id,
            content_type_name='destination'
        )

@receiver(destination_rejected_signal)
def create_destination_rejection_notification(sender, **kwargs):
    """
    Create a notification when a destination is rejected.
    
    Parameters:
    -----------
    sender: The sender of the signal
    kwargs: Additional keyword arguments containing:
        - user_id: ID of the user who submitted the destination
        - destination_id: ID of the destination that was rejected
        - destination_name: Name of the rejected destination
        - reason: Reason for rejection
    
    Returns:
    --------
    None
    """
    user_id = kwargs.get('user_id')
    destination_id = kwargs.get('destination_id')
    destination_name = kwargs.get('destination_name', 'your destination')
    reason = kwargs.get('reason', 'It did not meet our guidelines.')
    
    if user_id:
        Notification.objects.create(
            user_id=user_id,
            title="Destination Not Approved",
            content=f"Your destination '{destination_name}' was not approved. Reason: {reason}",
            notification_type='REJECTION',
            object_id=destination_id,
            content_type_name='destination'
        )

@receiver(booking_confirmed_signal)
def create_booking_confirmation_notification(sender, **kwargs):
    """
    Create a notification when a booking is confirmed.
    
    Parameters:
    -----------
    sender: The sender of the signal
    kwargs: Additional keyword arguments containing:
        - user_id: ID of the user who made the booking
        - booking_id: ID of the confirmed booking
        - tour_name: Name of the tour that was booked
    
    Returns:
    --------
    None
    """
    user_id = kwargs.get('user_id')
    booking_id = kwargs.get('booking_id')
    tour_name = kwargs.get('tour_name', 'your tour')
    
    if user_id:
        Notification.objects.create(
            user_id=user_id,
            title="Booking Confirmed",
            content=f"Your booking for '{tour_name}' has been confirmed.",
            notification_type='BOOKING',
            object_id=booking_id,
            content_type_name='booking'
        )

@receiver(tour_reminder_signal)
def create_tour_reminder_notification(sender, **kwargs):
    """
    Create a reminder notification for an upcoming tour.
    
    Parameters:
    -----------
    sender: The sender of the signal
    kwargs: Additional keyword arguments containing:
        - user_id: ID of the user who has the upcoming tour
        - tour_id: ID of the tour
        - tour_name: Name of the tour
        - days_left: Number of days until the tour
    
    Returns:
    --------
    None
    """
    user_id = kwargs.get('user_id')
    tour_id = kwargs.get('tour_id')
    tour_name = kwargs.get('tour_name', 'your tour')
    days_left = kwargs.get('days_left', 'soon')
    
    if user_id:
        Notification.objects.create(
            user_id=user_id,
            title="Tour Reminder",
            content=f"Your tour '{tour_name}' is starting in {days_left} days.",
            notification_type='REMINDER',
            object_id=tour_id,
            content_type_name='tour'
        )

@receiver(emergency_alert_signal)
def create_emergency_alert_notification(sender, **kwargs):
    """
    Create an emergency alert notification.
    
    Parameters:
    -----------
    sender: The sender of the signal
    kwargs: Additional keyword arguments containing:
        - user_id: ID of the user who should receive the alert
        - emergency_id: ID of the emergency record
        - alert_type: Type of emergency (weather, safety, etc.)
        - message: Emergency message content
    
    Returns:
    --------
    None
    """
    user_id = kwargs.get('user_id')
    emergency_id = kwargs.get('emergency_id')
    alert_type = kwargs.get('alert_type', 'General')
    message = kwargs.get('message', 'Please check the emergency section for details.')
    
    if user_id:
        Notification.objects.create(
            user_id=user_id,
            title=f"{alert_type} Emergency Alert",
            content=message,
            notification_type='EMERGENCY',
            object_id=emergency_id,
            content_type_name='emergency',
            is_read=False,
            is_urgent=True
        )
