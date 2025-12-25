"""
Notification service for sending SMS and email notifications.
Handles order status updates and customer communications.
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)

# Twilio import (will be used for SMS notifications)
try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logger.warning("Twilio not installed. SMS notifications will be disabled.")


def send_order_notification(order, old_status, new_status):
    """
    Send email and SMS notifications for order status updates.
    
    Args:
        order: Order object that was updated
        old_status: Previous status of the order
        new_status: New status of the order
    
    Returns:
        dict: Results of email and SMS sending attempts
    """
    results = {
        'email_sent': False,
        'sms_sent': False,
        'email_error': None,
        'sms_error': None
    }
    
    try:
        # Send email notification
        results['email_sent'] = send_order_email_notification(order, old_status, new_status)
    except Exception as e:
        logger.error(f"Failed to send email notification for order {order.order_id}: {str(e)}")
        results['email_error'] = str(e)
    
    try:
        # Send SMS notification for critical status changes
        if should_send_sms(new_status):
            results['sms_sent'] = send_order_sms_notification(order, new_status)
    except Exception as e:
        logger.error(f"Failed to send SMS notification for order {order.order_id}: {str(e)}")
        results['sms_error'] = str(e)
    
    return results


def send_order_email_notification(order, old_status, new_status):
    """
    Send email notification for order status update.
    
    Args:
        order: Order object
        old_status: Previous status
        new_status: New status
    
    Returns:
        bool: True if email was sent successfully
    """
    if not order.user or not order.user.email:
        logger.warning(f"No email address found for order {order.order_id}")
        return False
    
    # Prepare email context
    context = {
        'order': order,
        'old_status': old_status,
        'new_status': new_status,
        'customer_name': order.customer_name,
        'restaurant_name': order.items.first().menu_item.restaurant.name if order.items.exists() else 'Restaurant',
        'status_display': order.get_status_display(),
    }
    
    # Render email templates
    try:
        html_content = render_to_string('emails/order_status_update.html', context)
        text_content = strip_tags(html_content)
        
        # Send email
        send_mail(
            subject=f'Order #{str(order.order_id)[:8]} Status Update - {context["status_display"]}',
            message=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@foodordering.com'),
            recipient_list=[order.user.email],
            html_message=html_content,
            fail_silently=False,
        )
        
        logger.info(f"Email notification sent for order {order.order_id} - status: {new_status}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email for order {order.order_id}: {str(e)}")
        raise


def send_order_sms_notification(order, new_status):
    """
    Send SMS notification for critical order status updates.
    
    Args:
        order: Order object
        new_status: New status
    
    Returns:
        bool: True if SMS was sent successfully
    """
    if not TWILIO_AVAILABLE:
        logger.warning("Twilio not available. SMS notification skipped.")
        return False
    
    if not order.customer_phone:
        logger.warning(f"No phone number found for order {order.order_id}")
        return False
    
    # Get Twilio credentials from settings
    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
    from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', None)
    
    if not all([account_sid, auth_token, from_number]):
        logger.warning("Twilio credentials not configured. SMS notification skipped.")
        return False
    
    try:
        client = Client(account_sid, auth_token)
        
        # Prepare SMS message
        message_body = get_sms_message(order, new_status)
        
        # Send SMS
        message = client.messages.create(
            body=message_body,
            from_=from_number,
            to=order.customer_phone
        )
        
        logger.info(f"SMS notification sent for order {order.order_id} - SID: {message.sid}")
        return True
        
    except TwilioRestException as e:
        logger.error(f"Twilio error for order {order.order_id}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to send SMS for order {order.order_id}: {str(e)}")
        raise


def should_send_sms(status):
    """
    Determine if SMS should be sent for the given status.
    
    Args:
        status (str): Order status
    
    Returns:
        bool: True if SMS should be sent
    """
    # Send SMS for critical status changes only
    sms_statuses = ['accepted', 'out_for_delivery', 'delivered', 'cancelled']
    return status in sms_statuses


def get_sms_message(order, status):
    """
    Generate SMS message for order status update.
    
    Args:
        order: Order object
        status: New status
    
    Returns:
        str: SMS message
    """
    order_id_short = str(order.order_id)[:8]
    
    messages = {
        'accepted': f'Your order #{order_id_short} has been accepted! Restaurant is preparing your food.',
        'preparing': f'Your order #{order_id_short} is being prepared. It will be ready soon!',
        'out_for_delivery': f'Your order #{order_id_short} is out for delivery! Track your order on our website.',
        'delivered': f'Your order #{order_id_short} has been delivered. Enjoy your meal! Thank you for ordering.',
        'cancelled': f'Your order #{order_id_short} has been cancelled. Please contact the restaurant for details.',
    }
    
    return messages.get(status, f'Your order #{order_id_short} status has been updated to {status}.')


def send_welcome_email(user):
    """
    Send welcome email to new users.
    
    Args:
        user: User object
    
    Returns:
        bool: True if email was sent successfully
    """
    if not user.email:
        return False
    
    try:
        context = {
            'user': user,
            'site_name': getattr(settings, 'SITE_NAME', 'Food Ordering System'),
        }
        
        html_content = render_to_string('emails/welcome_email.html', context)
        text_content = strip_tags(html_content)
        
        send_mail(
            subject=f'Welcome to {context["site_name"]}!',
            message=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@foodordering.com'),
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=False,
        )
        
        logger.info(f"Welcome email sent to user {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        return False


def send_restaurant_approval_email(restaurant):
    """
    Send approval email to restaurant owners.
    
    Args:
        restaurant: Restaurant object
    
    Returns:
        bool: True if email was sent successfully
    """
    if not restaurant.owner or not restaurant.owner.email:
        return False
    
    try:
        context = {
            'restaurant': restaurant,
            'owner': restaurant.owner,
            'site_name': getattr(settings, 'SITE_NAME', 'Food Ordering System'),
        }
        
        html_content = render_to_string('emails/restaurant_approval.html', context)
        text_content = strip_tags(html_content)
        
        send_mail(
            subject=f'🎉 Your Restaurant "{restaurant.name}" has been Approved!',
            message=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@foodordering.com'),
            recipient_list=[restaurant.owner.email],
            html_message=html_content,
            fail_silently=False,
        )
        
        logger.info(f"Restaurant approval email sent to {restaurant.owner.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send restaurant approval email: {str(e)}")
        return False
