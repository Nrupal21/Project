"""
Core utilities package.

This package contains utility modules for the food ordering system including:
- user_roles: Restaurant owner identification and role management
- EmailUtils: Centralized email sending functionality
- ValidationUtils: Data validation and sanitization helpers  
- LocationUtils: Location-based operations and address handling
- Additional utility functions for common tasks
"""

# Import all utility classes and functions to make them available at package level
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class EmailUtils:
    """
    Utility class for handling email operations throughout the application.
    
    Provides centralized email sending functionality with template rendering,
    error handling, and logging for consistent email communication.
    """
    
    @staticmethod
    def send_templated_email(subject, template_name, context, recipient_list, 
                           from_email=None, html_template=None, fail_silently=False):
        """
        Send a templated email using Django templates.
        
        Creates and sends an email with both plain text and HTML versions
        using Django's template system for dynamic content generation.
        
        Args:
            subject (str): Email subject line
            template_name (str): Path to plain text email template
            context (dict): Context variables for template rendering
            recipient_list (list): List of recipient email addresses
            from_email (str, optional): Sender email address. Uses default if None
            html_template (str, optional): Path to HTML email template
            fail_silently (bool): Whether to suppress exceptions
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Set default from email if not provided
            from_email = from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@foodordering.com')
            
            # Render plain text content
            plain_message = render_to_string(template_name, context)
            
            # Create email with plain text
            if html_template:
                # Create multipart email with both HTML and text
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=plain_message,
                    from_email=from_email,
                    to=recipient_list,
                )
                
                # Render and attach HTML content
                html_content = render_to_string(html_template, context)
                email.attach_alternative(html_content, "text/html")
                
                result = email.send()
            else:
                # Send plain text email only
                result = send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=from_email,
                    recipient_list=recipient_list,
                    fail_silently=fail_silently,
                )
            
            logger.info(f"Email sent successfully to {recipient_list}: {subject}")
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_list}: {str(e)}")
            if not fail_silently:
                raise
            return False
    
    @staticmethod
    def send_welcome_email(user, request):
        """
        Send welcome email to newly registered user.
        
        Creates and sends a personalized welcome email with account details
        and information about getting started with the food ordering system.
        
        Args:
            user: User object that was just created
            request: Django HTTP request object for building absolute URLs
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Build context for email template
            site_url = request.build_absolute_uri('/')
            site_name = getattr(settings, 'SITE_NAME', 'Food Ordering System')
            
            context = {
                'user': user,
                'site_url': site_url,
                'site_name': site_name,
                'login_url': site_url + reverse('core:login'),
                'current_year': timezone.now().year,
            }
            
            # Send welcome email
            return EmailUtils.send_templated_email(
                subject=f'Welcome to {site_name}! 🍽️',
                template_name='emails/welcome_email.txt',
                html_template='emails/welcome_email.html',
                context=context,
                recipient_list=[user.email],
            )
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_password_reset_email(user, request, token_generator=default_token_generator):
        """
        Send password reset email to user.
        
        Creates and sends a secure password reset email with unique token
        and encoded user ID for password reset functionality.
        
        Args:
            user: User object requesting password reset
            request: Django HTTP request object for building absolute URLs
            token_generator: Token generator for creating secure reset tokens
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Generate password reset token and UID
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)
            
            # Build reset URL
            current_site = get_current_site(request)
            reset_url = request.build_absolute_uri(
                reverse('core:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )
            
            # Build context for email template
            context = {
                'user': user,
                'reset_url': reset_url,
                'site_name': getattr(settings, 'SITE_NAME', 'Food Ordering System'),
                'username': user.username,
                'current_year': timezone.now().year,
            }
            
            # Send password reset email
            return EmailUtils.send_templated_email(
                subject='Reset Your Password - Food Ordering System',
                template_name='emails/password_reset.txt',
                html_template='emails/password_reset.html',
                context=context,
                recipient_list=[user.email],
            )
            
        except Exception as e:
            logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_order_confirmation_email(order, request):
        """
        Send order confirmation email to customer.
        
        Creates and sends a detailed order confirmation with order details,
        restaurant information, and estimated delivery time.
        
        Args:
            order: Order object that was just created
            request: Django HTTP request object for building absolute URLs
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Build context for email template
            site_url = request.build_absolute_uri('/')
            context = {
                'order': order,
                'user': order.user,
                'restaurant': order.restaurant,
                'order_items': order.items.all(),
                'site_url': site_url,
                'track_order_url': site_url + reverse('orders:track_order', kwargs={'order_id': order.id}),
                'site_name': getattr(settings, 'SITE_NAME', 'Food Ordering System'),
                'current_year': timezone.now().year,
            }
            
            # Send order confirmation email
            return EmailUtils.send_templated_email(
                subject=f'Order Confirmation #{order.id} - {order.restaurant.name}',
                template_name='emails/order_confirmation.txt',
                html_template='emails/order_confirmation.html',
                context=context,
                recipient_list=[order.user.email],
            )
            
        except Exception as e:
            logger.error(f"Failed to send order confirmation email for order {order.id}: {str(e)}")
            return False
    
    @staticmethod
    def send_order_status_update_email(order, request):
        """
        Send order status update email to customer.
        
        Creates and sends an email notification when order status changes
        (e.g., confirmed, preparing, out for delivery, delivered).
        
        Args:
            order: Order object with updated status
            request: Django HTTP request object for building absolute URLs
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Build context for email template
            site_url = request.build_absolute_uri('/')
            context = {
                'order': order,
                'user': order.user,
                'restaurant': order.restaurant,
                'site_url': site_url,
                'track_order_url': site_url + reverse('orders:track_order', kwargs={'order_id': order.id}),
                'site_name': getattr(settings, 'SITE_NAME', 'Food Ordering System'),
                'current_year': timezone.now().year,
            }
            
            # Send status update email
            return EmailUtils.send_templated_email(
                subject=f'Order Status Update #{order.id} - {order.get_status_display()}',
                template_name='emails/order_status_update.txt',
                html_template='emails/order_status_update.html',
                context=context,
                recipient_list=[order.user.email],
            )
            
        except Exception as e:
            logger.error(f"Failed to send order status update email for order {order.id}: {str(e)}")
            return False
    
    @staticmethod
    def send_promotional_email(subject, template_name, context, user_list, 
                             from_email=None, fail_silently=False):
        """
        Send promotional email to multiple users.
        
        Creates and sends promotional emails to a list of users who have
        opted in to receive marketing communications.
        
        Args:
            subject (str): Email subject line
            template_name (str): Path to HTML email template
            context (dict): Context variables for template rendering
            user_list (list): List of User objects to send email to
            from_email (str, optional): Sender email address
            fail_silently (bool): Whether to suppress exceptions
            
        Returns:
            dict: Dictionary with success count and failed users
        """
        results = {'success': 0, 'failed': []}
        
        try:
            # Set default from email if not provided
            from_email = from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@foodordering.com')
            
            for user in user_list:
                try:
                    # Check if user has opted in for promotional emails
                    if hasattr(user, 'email_preferences'):
                        if not user.email_preferences.promotional_emails:
                            continue
                    
                    # Add user-specific context
                    user_context = context.copy()
                    user_context['user'] = user
                    user_context['username'] = user.username
                    user_context['first_name'] = user.first_name or user.username
                    
                    # Send email to individual user
                    success = EmailUtils.send_templated_email(
                        subject=subject,
                        template_name='emails/promotional_base.txt',
                        html_template=template_name,
                        context=user_context,
                        recipient_list=[user.email],
                        from_email=from_email,
                        fail_silently=True,
                    )
                    
                    if success:
                        results['success'] += 1
                    else:
                        results['failed'].append(user.email)
                        
                except Exception as e:
                    logger.error(f"Failed to send promotional email to {user.email}: {str(e)}")
                    results['failed'].append(user.email)
            
            logger.info(f"Promotional email campaign completed: {results['success']} successful, {len(results['failed'])} failed")
            
        except Exception as e:
            logger.error(f"Promotional email campaign failed: {str(e)}")
            if not fail_silently:
                raise
        
        return results


class ValidationUtils:
    """
    Utility class for data validation and sanitization.
    
    Provides common validation functions used throughout the application
    for ensuring data integrity and security.
    """
    
    @staticmethod
    def validate_phone_number(phone_number):
        """
        Validate phone number format.
        
        Args:
            phone_number (str): Phone number to validate
            
        Returns:
            bool: True if phone number is valid, False otherwise
        """
        import re
        pattern = r'^\+?1?\d{9,15}$'
        return bool(re.match(pattern, phone_number))
    
    @staticmethod
    def sanitize_email(email):
        """
        Sanitize and validate email address.
        
        Args:
            email (str): Email address to sanitize
            
        Returns:
            str: Sanitized email address or None if invalid
        """
        import re
        email = email.strip().lower()
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return email if re.match(pattern, email) else None
    
    @staticmethod
    def validate_postal_code(postal_code):
        """
        Validate postal/ZIP code format.
        
        Args:
            postal_code (str): Postal code to validate
            
        Returns:
            bool: True if postal code is valid, False otherwise
        """
        import re
        # Basic pattern for postal codes (alphanumeric, 3-10 characters)
        pattern = r'^[a-zA-Z0-9\s]{3,10}$'
        return bool(re.match(pattern, postal_code.strip()))


class LocationUtils:
    """
    Utility class for location-based operations.
    
    Provides helper functions for handling addresses, distances,
    and location-related calculations.
    """
    
    @staticmethod
    def format_address(address, city, postal_code):
        """
        Format complete address from components.
        
        Args:
            address (str): Street address
            city (str): City name
            postal_code (str): Postal/ZIP code
            
        Returns:
            str: Formatted complete address
        """
        address_parts = []
        if address and address.strip():
            address_parts.append(address.strip())
        if city and city.strip():
            address_parts.append(city.strip())
        if postal_code and postal_code.strip():
            address_parts.append(postal_code.strip())
        
        return ', '.join(address_parts) if address_parts else 'No address provided'
    
    @staticmethod
    def validate_delivery_address(address, city, postal_code):
        """
        Validate if address is complete enough for delivery.
        
        Args:
            address (str): Street address
            city (str): City name
            postal_code (str): Postal/ZIP code
            
        Returns:
            tuple: (bool is_valid, str error_message)
        """
        if not address or not address.strip():
            return False, "Street address is required for delivery"
        
        if not city or not city.strip():
            return False, "City is required for delivery"
        
        if not ValidationUtils.validate_postal_code(postal_code):
            return False, "Please enter a valid postal code"
        
        return True, ""

    @staticmethod
    def send_restaurant_submission_email(user, restaurant, request):
        """
        Send email to restaurant owner confirming submission and pending approval.
        
        Args:
            user: User object (restaurant owner)
            restaurant: Restaurant object that was submitted
            request: Django HTTP request object
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            site_url = request.build_absolute_uri('/')
            site_name = getattr(settings, 'SITE_NAME', 'Food Ordering System')
            
            context = {
                'user': user,
                'restaurant': restaurant,
                'site_url': site_url,
                'site_name': site_name,
                'login_url': site_url + reverse('core:login'),
                'current_year': timezone.now().year,
            }
            
            return EmailUtils.send_templated_email(
                subject=f'Restaurant "{restaurant.name}" Submitted for Approval - {site_name}',
                template_name='emails/restaurant_submission.txt',
                html_template='emails/restaurant_submission.html',
                context=context,
                recipient_list=[user.email],
            )
            
        except Exception as e:
            logger.error(f"Failed to send restaurant submission email to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_restaurant_approval_email(user, restaurant, request):
        """
        Send email to restaurant owner when restaurant is approved.
        
        Args:
            user: User object (restaurant owner)
            restaurant: Restaurant object that was approved
            request: Django HTTP request object
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            site_url = request.build_absolute_uri('/')
            site_name = getattr(settings, 'SITE_NAME', 'Food Ordering System')
            
            context = {
                'user': user,
                'restaurant': restaurant,
                'site_url': site_url,
                'site_name': site_name,
                'restaurant_url': site_url + reverse('restaurant:detail', kwargs={'pk': restaurant.pk}),
                'dashboard_url': site_url + reverse('restaurant:dashboard'),
                'current_year': timezone.now().year,
            }
            
            return EmailUtils.send_templated_email(
                subject=f'🎉 Restaurant "{restaurant.name}" Approved! - {site_name}',
                template_name='emails/restaurant_approval.txt',
                html_template='emails/restaurant_approval.html',
                context=context,
                recipient_list=[user.email],
            )
            
        except Exception as e:
            logger.error(f"Failed to send restaurant approval email to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_restaurant_rejection_email(user, restaurant, reason=None, request=None):
        """
        Send email to restaurant owner when restaurant is rejected.
        
        Args:
            user: User object (restaurant owner)
            restaurant: Restaurant object that was rejected
            reason: Optional reason for rejection
            request: Django HTTP request object
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            site_url = request.build_absolute_uri('/') if request else getattr(settings, 'SITE_URL', '')
            site_name = getattr(settings, 'SITE_NAME', 'Food Ordering System')
            
            context = {
                'user': user,
                'restaurant': restaurant,
                'reason': reason,
                'site_url': site_url,
                'site_name': site_name,
                'contact_email': getattr(settings, 'CONTACT_EMAIL', 'support@foodordering.com'),
                'current_year': timezone.now().year,
            }
            
            return EmailUtils.send_templated_email(
                subject=f'Restaurant "{restaurant.name}" Update - {site_name}',
                template_name='emails/restaurant_rejection.txt',
                html_template='emails/restaurant_rejection.html',
                context=context,
                recipient_list=[user.email],
            )
            
        except Exception as e:
            logger.error(f"Failed to send restaurant rejection email to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_manager_notification_emails(restaurant, request):
        """
        Send notification emails to all managers/admins about new restaurant submission.
        
        Args:
            restaurant: Restaurant object that was submitted
            request: Django HTTP request object
            
        Returns:
            tuple: (success_count, total_count, error_message)
        """
        try:
            from django.contrib.auth.models import User, Group
            from django.db import models
            
            # Get all managers and admins
            managers = User.objects.filter(
                models.Q(is_superuser=True) | 
                models.Q(is_staff=True) |
                models.Q(groups__name__in=['Manager', 'Admin'])
            ).distinct()
            
            if not managers:
                return 0, 0, "No managers found to notify"
            
            site_url = request.build_absolute_uri('/')
            site_name = getattr(settings, 'SITE_NAME', 'Food Ordering System')
            
            context = {
                'restaurant': restaurant,
                'site_url': site_url,
                'site_name': site_name,
                'admin_url': site_url + '/admin/',
                'current_year': timezone.now().year,
            }
            
            success_count = 0
            for manager in managers:
                try:
                    EmailUtils.send_templated_email(
                        subject=f'New Restaurant Submission: "{restaurant.name}" - {site_name}',
                        template_name='emails/manager_notification.txt',
                        html_template='emails/manager_notification.html',
                        context=context,
                        recipient_list=[manager.email],
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to send manager notification to {manager.email}: {str(e)}")
            
            return success_count, len(managers), ""
            
        except Exception as e:
            logger.error(f"Failed to send manager notifications: {str(e)}")
            return 0, 0, str(e)


def get_client_ip(request):
    """
    Get the client's IP address from the request.
    
    Extracts the real IP address considering proxies and load balancers.
    
    Args:
        request: Django HTTP request object
        
    Returns:
        str: Client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def generate_unique_filename(filename, prefix=''):
    """
    Generate a unique filename to prevent collisions.
    
    Creates a unique filename using timestamp and random UUID
    while preserving the original file extension.
    
    Args:
        filename (str): Original filename
        prefix (str): Optional prefix for the filename
        
    Returns:
        str: Unique filename
    """
    import uuid
    import os
    from datetime import datetime
    
    # Get file extension
    ext = os.path.splitext(filename)[1]
    
    # Generate unique identifier
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    
    # Build unique filename
    if prefix:
        return f"{prefix}_{timestamp}_{unique_id}{ext}"
    else:
        return f"{timestamp}_{unique_id}{ext}"
