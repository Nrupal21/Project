"""
Email notification utilities for destination-related events.

This module provides functions to send email notifications for various
destination-related events such as new submissions, approvals, and rejections.
All email templates use Tailwind CSS for consistent styling.
"""

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from core.email_utils import send_templated_email

import logging

logger = logging.getLogger(__name__)

def send_destination_submission_notification(destination, submitter):
    """
    Send notification to managers/admins about a new destination submission.
    
    Args:
        destination: The PendingDestination instance that was submitted
        submitter: User who submitted the destination
        
    Returns:
        bool: True if notification was sent successfully, False otherwise
    """
    try:
        # Get the review URL for the admin interface
        review_url = settings.SITE_URL + reverse(
            'destinations:admin_review_destination', 
            kwargs={'pk': destination.pk}
        )
        
        # Get recipient emails (managers and admins)
        from accounts.models import User
        recipients = User.objects.filter(
            is_active=True,
            is_staff=True
        ).values_list('email', flat=True)
        
        if not recipients:
            logger.warning("No staff members found to send notification to")
            return False
        
        # Prepare context for the email template
        context = {
            'destination': destination,
            'submitter': submitter,
            'review_url': review_url,
            'site_name': getattr(settings, 'SITE_NAME', 'TravelGuide'),
            'current_date': timezone.now().strftime('%B %d, %Y'),
            'site_url': settings.SITE_URL
        }
        
        # Send using the reusable email utility
        subject = f"New Destination Submitted: {destination.name}"
        result = send_templated_email(
            recipient_email=list(recipients),
            subject=subject,
            template_name='emails/destinations/destination_submitted',
            context=context
        )
        
        if result:
            logger.info(f"Destination submission notification sent for {destination.name}")
        else:
            logger.warning(f"Failed to send destination submission notification for {destination.name}")
            
        return result
        
    except Exception as e:
        logger.error(
            f"Error sending destination submission notification: {str(e)}",
            exc_info=True
        )
        return False

def send_destination_approved_notification(destination, reviewer):
    """
    Send notification to the guide when their destination is approved.
    
    Args:
        destination: The approved Destination instance
        reviewer: User who approved the destination
        
    Returns:
        bool: True if notification was sent successfully, False otherwise
    """
    try:
        if not destination.created_by or not destination.created_by.email:
            logger.warning("No creator email found for approved destination")
            return False
            
        # Get reward points information if available
        reward_points = None
        try:
            from rewards.models import RewardPoints
            reward_points = RewardPoints.get_user_point_balance(destination.created_by)
        except Exception as e:
            logger.warning(f"Could not get reward points: {str(e)}")
        
        # Prepare context for the email template
        context = {
            'destination': destination,
            'reviewer': reviewer,
            'reward_points': reward_points,
            'destination_url': f"{settings.SITE_URL}{destination.get_absolute_url()}",
            'site_name': getattr(settings, 'SITE_NAME', 'TravelGuide'),
            'current_date': timezone.now().strftime('%B %d, %Y'),
            'site_url': settings.SITE_URL
        }
        
        # Send using the reusable email utility
        subject = f"Your Destination Has Been Approved: {destination.name}"
        result = send_templated_email(
            recipient_email=destination.created_by.email,
            subject=subject,
            template_name='emails/destinations/destination_approved',
            context=context
        )
        
        if result:
            logger.info(f"Destination approval notification sent for {destination.name}")
        else:
            logger.warning(f"Failed to send destination approval notification for {destination.name}")
            
        return result
        
    except Exception as e:
        logger.error(
            f"Error sending destination approval notification: {str(e)}",
            exc_info=True
        )
        return False

def send_destination_rejected_notification(pending_destination, reviewer, rejection_reason):
    """
    Send notification to the guide when their destination is rejected.
    
    Args:
        pending_destination: The rejected PendingDestination instance
        reviewer: User who rejected the destination
        rejection_reason: Reason for rejection
        
    Returns:
        bool: True if notification was sent successfully, False otherwise
    """
    try:
        if not pending_destination.created_by or not pending_destination.created_by.email:
            logger.warning("No creator email found for rejected destination")
            return False
            
        # Prepare context for the email template
        context = {
            'destination': pending_destination,
            'reviewer': reviewer,
            'rejection_reason': rejection_reason,
            'resubmit_url': (
                f"{settings.SITE_URL}" 
                f"{reverse('destinations:pending_destination_update', kwargs={'pk': pending_destination.pk})}"
            ),
            'site_name': getattr(settings, 'SITE_NAME', 'TravelGuide'),
            'current_date': timezone.now().strftime('%B %d, %Y'),
            'site_url': settings.SITE_URL
        }
        
        # Send using the reusable email utility
        subject = f"Update on Your Destination Submission: {pending_destination.name}"
        result = send_templated_email(
            recipient_email=pending_destination.created_by.email,
            subject=subject,
            template_name='emails/destinations/destination_rejected',
            context=context
        )
        
        if result:
            logger.info(f"Destination rejection notification sent for {pending_destination.name}")
        else:
            logger.warning(f"Failed to send destination rejection notification for {pending_destination.name}")
            
        return result
        
    except Exception as e:
        logger.error(
            f"Error sending destination rejection notification: {str(e)}",
            exc_info=True
        )
        return False


def send_guide_submission_confirmation(pending_destination, submitter):
    """
    Send confirmation to the local guide after successfully submitting a destination.
    
    Args:
        pending_destination: The PendingDestination instance that was submitted
        submitter: User who submitted the destination
        
    Returns:
        bool: True if confirmation was sent successfully, False otherwise
    """
    try:
        if not submitter or not submitter.email:
            logger.warning("No submitter email found for destination submission confirmation")
            return False
            
        # Get the profile URL
        profile_url = settings.SITE_URL + reverse('accounts:profile')
        
        # Prepare context for the email template
        context = {
            'destination': pending_destination,
            'submitter': submitter,
            'profile_url': profile_url,
            'site_name': getattr(settings, 'SITE_NAME', 'TravelGuide'),
            'current_date': timezone.now().strftime('%B %d, %Y'),
            'current_year': timezone.now().year,
            'site_url': settings.SITE_URL
        }
        
        # Send using the reusable email utility
        subject = f"Destination Submission Confirmation: {pending_destination.name}"
        result = send_templated_email(
            recipient_email=submitter.email,
            subject=subject,
            template_name='emails/destinations/guide_submission_confirmation',
            context=context
        )
        
        if result:
            logger.info(f"Submission confirmation sent to guide for {pending_destination.name}")
        else:
            logger.warning(f"Failed to send guide submission confirmation for {pending_destination.name}")
            
        return result
        
    except Exception as e:
        logger.error(
            f"Error sending guide submission confirmation: {str(e)}",
            exc_info=True
        )
        return False
