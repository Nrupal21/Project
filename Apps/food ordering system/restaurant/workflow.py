"""
Enhanced restaurant registration workflow management.

This module provides comprehensive workflow management for restaurant registrations,
including approval status tracking, auto-approval logic, and notification handling.
"""

from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import transaction
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class RegistrationWorkflow:
    """
    Core workflow manager for restaurant registrations.
    
    Handles the complete lifecycle of restaurant registration from submission
    through approval/rejection to activation. Provides hooks for notifications
    and analytics tracking.
    """
    
    # Workflow status constants
    STATUS_DRAFT = 'draft'
    STATUS_SUBMITTED = 'submitted'
    STATUS_PENDING = 'pending'
    STATUS_UNDER_REVIEW = 'under_review'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_ACTIVE = 'active'
    STATUS_SUSPENDED = 'suspended'
    
    # Auto-approval criteria thresholds
    AUTO_APPROVAL_MIN_RATING = Decimal('4.5')
    AUTO_APPROVAL_MIN_ORDERS = 100
    AUTO_APPROVAL_MIN_TENURE_DAYS = 30
    
    def __init__(self, restaurant):
        """
        Initialize workflow manager with restaurant instance.
        
        Args:
            restaurant: Restaurant model instance
        """
        self.restaurant = restaurant
        self.user = restaurant.owner if hasattr(restaurant, 'owner') else None
    
    def submit_for_review(self, request=None):
        """
        Submit restaurant for manager review.
        
        Changes status from draft to submitted and triggers notification emails
        to managers and the restaurant owner.
        
        Args:
            request: Django HTTP request object for building URLs
            
        Returns:
            tuple: (success: bool, message: str, notifications_sent: int)
        """
        try:
            with transaction.atomic():
                # Update status
                self.restaurant.approval_status = self.STATUS_SUBMITTED
                self.restaurant.submitted_at = timezone.now()
                self.restaurant.save()
                
                # Send notifications
                notifications_sent = 0
                
                if request and self.user:
                    # Import here to avoid circular imports
                    from core.utils import EmailUtils
                    
                    # Send confirmation to restaurant owner
                    try:
                        # Simple email notification bypassing EmailUtils issue
                        from django.core.mail import send_mail
                        from django.conf import settings
                        
                        site_name = getattr(settings, 'SITE_NAME', 'Food Ordering System')
                        subject = f'Restaurant "{self.restaurant.name}" Submitted for Approval - {site_name}'
                        message = f'''
Dear {self.user.username},

Your restaurant "{self.restaurant.name}" has been successfully submitted for approval.

Our team will review your application within 24-48 hours. You will receive an email notification once a decision has been made.

Thank you for choosing {site_name}!

Best regards,
The {site_name} Team
                        '''
                        
                        send_mail(
                            subject=subject,
                            message=message,
                            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@foodordering.com'),
                            recipient_list=[self.user.email],
                            fail_silently=False,
                        )
                        notifications_sent += 1
                    except Exception as e:
                        logger.error(f"Failed to send submission email: {e}")
                    
                    # Send notifications to managers
                    try:
                        from django.core.mail import send_mail
                        from django.contrib.auth.models import User
                        
                        # Get all staff/manager users
                        managers = User.objects.filter(is_staff=True, is_active=True)
                        
                        site_name = getattr(settings, 'SITE_NAME', 'Food Ordering System')
                        subject = f'New Restaurant Submission: "{self.restaurant.name}"'
                        message = f'''
Hello,

A new restaurant has been submitted for approval:

Restaurant Name: {self.restaurant.name}
Owner: {self.user.username} ({self.user.email})
Submitted: {self.restaurant.created_at}

Please review this submission in the manager dashboard.

Dashboard URL: {request.build_absolute_uri('/restaurant/manager/dashboard/')}

Best regards,
{site_name} System
                        '''
                        
                        manager_emails = [m.email for m in managers if m.email]
                        if manager_emails:
                            send_mail(
                                subject=subject,
                                message=message,
                                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@foodordering.com'),
                                recipient_list=manager_emails,
                                fail_silently=False,
                            )
                            notifications_sent += len(manager_emails)
                    except Exception as e:
                        logger.error(f"Failed to send manager notification emails: {e}")
                
                logger.info(
                    f"Restaurant {self.restaurant.name} submitted for review. "
                    f"{notifications_sent} notifications sent."
                )
                
                return True, "Restaurant submitted successfully", notifications_sent
                
        except Exception as e:
            logger.error(f"Error submitting restaurant for review: {str(e)}")
            return False, str(e), 0
    
    def can_auto_approve(self):
        """
        Check if restaurant qualifies for automatic approval.
        
        Evaluates various criteria including owner reputation, restaurant metrics,
        and compliance requirements to determine auto-approval eligibility.
        
        Returns:
            tuple: (eligible: bool, reason: str)
        """
        # Check if auto-approval is enabled
        if not getattr(settings, 'ENABLE_AUTO_APPROVAL', False):
            return False, "Auto-approval is disabled"
        
        # Check owner is authenticated and active
        if not self.user or not self.user.is_active:
            return False, "Owner account is not active"
        
        # Check if owner is verified
        if hasattr(self.user, 'profile') and not self.user.profile.is_verified:
            return False, "Owner identity not verified"
        
        # Check owner reputation (if they have previous restaurants)
        owner_restaurants = self.restaurant.__class__.objects.filter(
            owner=self.user,
            approval_status=self.STATUS_APPROVED
        ).exclude(id=self.restaurant.id)
        
        if owner_restaurants.exists():
            # Check average rating
            avg_rating = owner_restaurants.aggregate(
                models.Avg('rating')
            )['rating__avg']
            
            if avg_rating and avg_rating >= self.AUTO_APPROVAL_MIN_RATING:
                return True, "Trusted owner with high-rated existing restaurants"
        
        # Check if restaurant has required information completeness
        if not self._is_complete():
            return False, "Restaurant information incomplete"
        
        # Check for staff vouching
        if hasattr(self.restaurant, 'vouched_by') and self.restaurant.vouched_by:
            if self.restaurant.vouched_by.is_staff or self.restaurant.vouched_by.is_superuser:
                return True, "Vouched by staff member"
        
        # Default: requires manual review
        return False, "Requires manual review"
    
    def approve(self, approved_by, notes=None, request=None):
        """
        Approve restaurant registration and activate it.
        
        Sets approval status, activates restaurant, updates timestamps,
        and sends notification emails to the owner.
        
        Args:
            approved_by: User who approved the restaurant (staff/manager)
            notes: Optional approval notes
            request: Django HTTP request object for building URLs
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            with transaction.atomic():
                # Update restaurant status
                self.restaurant.is_approved = True
                self.restaurant.is_active = True
                self.restaurant.approval_status = self.STATUS_APPROVED
                self.restaurant.approved_at = timezone.now()
                self.restaurant.approved_by = approved_by
                self.restaurant.rejection_reason = None
                
                if notes:
                    self.restaurant.approval_notes = notes
                
                self.restaurant.save()
                
                # Add owner to Restaurant Owner group if not already
                from django.contrib.auth.models import Group
                restaurant_owner_group, _ = Group.objects.get_or_create(
                    name='Restaurant Owner'
                )
                self.user.groups.add(restaurant_owner_group)
                
                # Send approval notification
                if request and self.user:
                    try:
                        from django.core.mail import send_mail
                        
                        site_name = getattr(settings, 'SITE_NAME', 'Food Ordering System')
                        subject = f'Restaurant "{self.restaurant.name}" Approved! - {site_name}'
                        message = f'''
Dear {self.user.username},

Congratulations! Your restaurant "{self.restaurant.name}" has been approved!

You can now start accepting orders through our platform. Please log in to your dashboard to:
- Update your menu
- Set your availability
- Manage incoming orders

Dashboard URL: {request.build_absolute_uri('/restaurant/dashboard/')}

Thank you for joining {site_name}!

Best regards,
The {site_name} Team
                        '''
                        
                        send_mail(
                            subject=subject,
                            message=message,
                            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@foodordering.com'),
                            recipient_list=[self.user.email],
                            fail_silently=False,
                        )
                    except Exception as e:
                        logger.error(f"Failed to send approval email: {e}")
                
                # Log approval
                logger.info(
                    f"Restaurant {self.restaurant.name} approved by {approved_by.username}"
                )
                
                # Track analytics
                self._track_approval_event(approved_by)
                
                return True, "Restaurant approved successfully"
                
        except Exception as e:
            logger.error(f"Error approving restaurant: {str(e)}")
            return False, str(e)
    
    def reject(self, rejected_by, reason, request=None):
        """
        Reject restaurant registration.
        
        Sets rejection status, records reason, and sends notification
        email to the owner explaining the rejection.
        
        Args:
            rejected_by: User who rejected the restaurant (staff/manager)
            reason: Detailed reason for rejection
            request: Django HTTP request object for building URLs
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            with transaction.atomic():
                # Update restaurant status
                self.restaurant.is_approved = False
                self.restaurant.is_active = False
                self.restaurant.approval_status = self.STATUS_REJECTED
                self.restaurant.rejected_at = timezone.now()
                self.restaurant.rejected_by = rejected_by
                self.restaurant.rejection_reason = reason
                
                self.restaurant.save()
                
                # Send rejection notification
                if request and self.user:
                    try:
                        from django.core.mail import send_mail
                        
                        site_name = getattr(settings, 'SITE_NAME', 'Food Ordering System')
                        subject = f'Restaurant Application Update - {site_name}'
                        message = f'''
Dear {self.user.username},

Thank you for your interest in joining {site_name}.

Unfortunately, your restaurant application for "{self.restaurant.name}" has not been approved at this time.

Reason: {reason if reason else "Please contact support for more details"}

If you have any questions or would like to resubmit your application with additional information, please contact our support team.

Best regards,
The {site_name} Team
                        '''
                        
                        send_mail(
                            subject=subject,
                            message=message,
                            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@foodordering.com'),
                            recipient_list=[self.user.email],
                            fail_silently=False,
                        )
                    except Exception as e:
                        logger.error(f"Failed to send rejection email: {e}")
                
                # Log rejection
                logger.info(
                    f"Restaurant {self.restaurant.name} rejected by {rejected_by.username}. "
                    f"Reason: {reason}"
                )
                
                # Track analytics
                self._track_rejection_event(rejected_by, reason)
                
                return True, "Restaurant rejected"
                
        except Exception as e:
            logger.error(f"Error rejecting restaurant: {str(e)}")
            return False, str(e)
    
    def suspend(self, suspended_by, reason):
        """
        Suspend an active restaurant.
        
        Temporarily deactivates restaurant while keeping approval status.
        Can be reversed by reactivating.
        
        Args:
            suspended_by: User who suspended the restaurant
            reason: Reason for suspension
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            with transaction.atomic():
                self.restaurant.is_active = False
                self.restaurant.approval_status = self.STATUS_SUSPENDED
                self.restaurant.suspended_at = timezone.now()
                self.restaurant.suspended_by = suspended_by
                self.restaurant.suspension_reason = reason
                
                self.restaurant.save()
                
                logger.info(
                    f"Restaurant {self.restaurant.name} suspended by {suspended_by.username}"
                )
                
                return True, "Restaurant suspended"
                
        except Exception as e:
            logger.error(f"Error suspending restaurant: {str(e)}")
            return False, str(e)
    
    def reactivate(self, reactivated_by, notes=None):
        """
        Reactivate a suspended restaurant.
        
        Args:
            reactivated_by: User who reactivated the restaurant
            notes: Optional reactivation notes
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            with transaction.atomic():
                self.restaurant.is_active = True
                self.restaurant.approval_status = self.STATUS_ACTIVE
                self.restaurant.reactivated_at = timezone.now()
                self.restaurant.reactivated_by = reactivated_by
                
                if notes:
                    self.restaurant.reactivation_notes = notes
                
                self.restaurant.save()
                
                logger.info(
                    f"Restaurant {self.restaurant.name} reactivated by {reactivated_by.username}"
                )
                
                return True, "Restaurant reactivated"
                
        except Exception as e:
            logger.error(f"Error reactivating restaurant: {str(e)}")
            return False, str(e)
    
    def _is_complete(self):
        """
        Check if restaurant has all required information.
        
        Returns:
            bool: True if all required fields are filled
        """
        required_fields = [
            'name', 'description', 'phone', 'address', 
            'cuisine_type', 'opening_time', 'closing_time',
            'minimum_order', 'delivery_fee'
        ]
        
        for field in required_fields:
            if not getattr(self.restaurant, field, None):
                return False
        
        return True
    
    def _track_approval_event(self, approved_by):
        """
        Track restaurant approval event for analytics.
        
        Args:
            approved_by: User who approved the restaurant
        """
        try:
            from core.system_analytics import SystemAnalytics
            analytics = SystemAnalytics()
            analytics.track_event(
                'restaurant_approved',
                {
                    'restaurant_id': self.restaurant.id,
                    'restaurant_name': self.restaurant.name,
                    'approved_by': approved_by.username,
                    'owner': self.user.username if self.user else None,
                }
            )
        except Exception as e:
            logger.warning(f"Failed to track approval event: {str(e)}")
    
    def _track_rejection_event(self, rejected_by, reason):
        """
        Track restaurant rejection event for analytics.
        
        Args:
            rejected_by: User who rejected the restaurant
            reason: Rejection reason
        """
        try:
            from core.system_analytics import SystemAnalytics
            analytics = SystemAnalytics()
            analytics.track_event(
                'restaurant_rejected',
                {
                    'restaurant_id': self.restaurant.id,
                    'restaurant_name': self.restaurant.name,
                    'rejected_by': rejected_by.username,
                    'owner': self.user.username if self.user else None,
                    'reason': reason,
                }
            )
        except Exception as e:
            logger.warning(f"Failed to track rejection event: {str(e)}")


class AutoApprovalEngine:
    """
    Engine for evaluating and executing auto-approval logic.
    
    Implements sophisticated rules for automatically approving restaurant
    registrations based on owner reputation, compliance, and trust scores.
    """
    
    @staticmethod
    def evaluate_all_pending():
        """
        Evaluate all pending restaurants for auto-approval.
        
        Scans all pending restaurant registrations and automatically approves
        those that meet the auto-approval criteria.
        
        Returns:
            dict: Statistics about auto-approval results
        """
        from restaurant.models import Restaurant
        
        pending_restaurants = Restaurant.objects.filter(
            approval_status='pending',
            is_approved=False
        )
        
        stats = {
            'total_evaluated': 0,
            'auto_approved': 0,
            'requires_review': 0,
            'errors': 0
        }
        
        for restaurant in pending_restaurants:
            stats['total_evaluated'] += 1
            workflow = RegistrationWorkflow(restaurant)
            
            eligible, reason = workflow.can_auto_approve()
            
            if eligible:
                # Create a system user for auto-approval
                system_user = User.objects.filter(
                    username='system',
                    is_staff=True
                ).first()
                
                if not system_user:
                    logger.warning("System user not found for auto-approval")
                    stats['requires_review'] += 1
                    continue
                
                success, message = workflow.approve(
                    approved_by=system_user,
                    notes=f"Auto-approved: {reason}"
                )
                
                if success:
                    stats['auto_approved'] += 1
                    logger.info(f"Auto-approved restaurant: {restaurant.name}")
                else:
                    stats['errors'] += 1
                    logger.error(f"Failed to auto-approve {restaurant.name}: {message}")
            else:
                stats['requires_review'] += 1
        
        return stats
    
    @staticmethod
    def check_eligibility(restaurant):
        """
        Check if a specific restaurant is eligible for auto-approval.
        
        Args:
            restaurant: Restaurant instance to check
            
        Returns:
            tuple: (eligible: bool, reason: str, trust_score: float)
        """
        workflow = RegistrationWorkflow(restaurant)
        eligible, reason = workflow.can_auto_approve()
        
        # Calculate trust score (0-100)
        trust_score = AutoApprovalEngine._calculate_trust_score(restaurant)
        
        return eligible, reason, trust_score
    
    @staticmethod
    def _calculate_trust_score(restaurant):
        """
        Calculate trust score for restaurant/owner.
        
        Args:
            restaurant: Restaurant instance
            
        Returns:
            float: Trust score from 0 to 100
        """
        score = 50.0  # Base score
        
        owner = restaurant.owner if hasattr(restaurant, 'owner') else None
        
        if owner:
            # Owner has verified email
            if owner.is_active:
                score += 10
            
            # Owner has other approved restaurants
            approved_count = restaurant.__class__.objects.filter(
                owner=owner,
                approval_status='approved',
                is_active=True
            ).count()
            
            score += min(approved_count * 10, 30)  # Max 30 points
        
        # Restaurant information completeness
        required_fields = ['name', 'description', 'phone', 'address', 'image']
        complete_fields = sum(1 for field in required_fields 
                            if getattr(restaurant, field, None))
        score += (complete_fields / len(required_fields)) * 10
        
        return min(score, 100.0)
