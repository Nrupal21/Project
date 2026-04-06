"""
Admin-specific views for the destinations app.

This module contains views that are accessible only to users with manager or admin roles,
including the destination approval workflow, review process, and management functions.

The views in this file implement the complete destination moderation system:
- Listing pending destinations awaiting approval
- Detailed review interface for each destination
- Approval/rejection workflows with notifications
- Email and in-app notification integration

All views are protected by authentication and permission checks to ensure
only authorized staff can access these administrative functions.
"""

from django.views.generic import ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponseRedirect
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

# Use absolute import instead of relative import for better compatibility
from destinations.models import Destination, Region


def send_destination_approval_notification(destination):
    """
    Send an email notification to the destination creator when their destination is approved.
    
    This function composes and sends an email to the local guide who created the
    destination, informing them that their submission has been approved and is now
    visible on the site. It also mentions the reward points they've received.
    
    The function handles both email notifications and in-app notifications using the
    notifications app if available. It creates a visually appealing HTML email using
    the templates/emails/destinations/destination_approved.html template as well as
    a plain text fallback version.
    
    Args:
        destination: The Destination object that was approved
        
    Returns:
        bool: True if the notification was sent successfully, False otherwise
    """
    if not destination.created_by or not destination.created_by.email:
        return False
    
    # Get current reward points balance if available
    from rewards.models import RewardPoints
    reward_points = RewardPoints.get_user_point_balance(destination.created_by) \
        if hasattr(RewardPoints, 'get_user_point_balance') else 'updated'
    
    # Generate destination URL
    destination_url = f"{settings.SITE_URL}{destination.get_absolute_url()}" \
        if hasattr(settings, 'SITE_URL') else '#'
    
    subject = f"Your destination '{destination.name}' has been approved!"
    
    # Create HTML message content using a template
    context = {
        'destination': destination,
        'destination_url': destination_url,
        'reward_points': reward_points
    }
    
    # Use the new email template path
    html_message = render_to_string('emails/destinations/destination_approved.html', context)
    
    # Create plain text message as fallback
    name = destination.created_by.get_full_name() or destination.created_by.username
    plain_message = f"""Hi {name},

Great news! Your destination '{destination.name}' has been approved and is now visible on the TravelGuides site.

You've been awarded 50 reward points for your contribution!

Thank you for helping us grow our community of travel destinations.

The TravelGuides Team"""
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[destination.created_by.email],
            html_message=html_message,
            fail_silently=False
        )
        
        # Also create an in-app notification if the notifications app is available
        try:
            from notifications.models import Notification
            
            # Create in-app notification
            Notification.create_notification(
                recipient=destination.created_by,
                title=f"Destination '{destination.name}' Approved!",
                message=f"Your destination submission '{destination.name}' has been approved and is now visible on the site. You've earned 50 reward points!",
                level=Notification.LEVEL_SUCCESS,
                related_object=destination,
                link_url=destination.get_absolute_url(),
                link_text="View Your Destination"
            )
        except ImportError:
            # Notifications app not available, continue without in-app notification
            pass
            
        return True
    except Exception:
        return False


def send_destination_rejection_notification(destination):
    """
    Send an email notification to the destination creator when their destination is rejected.
    
    This function composes and sends an email to the local guide who created the
    destination, informing them that their submission has been rejected and
    providing the reason for rejection. Also creates an in-app notification.
    
    The function creates both an HTML email using the templates/emails/destinations/destination_rejected.html
    template and a plain text fallback. The email includes the specific reason for rejection
    and provides guidance on how to improve and resubmit the destination.
    
    If the notifications app is available, it also creates an in-app notification
    with appropriate warning level styling to ensure the user is aware of the rejection.
    
    Args:
        destination: The Destination object that was rejected
        
    Returns:
        bool: True if the notification was sent successfully, False otherwise
    """
    if not destination.created_by or not destination.created_by.email:
        return False
    
    # Generate submission guidelines URL
    submission_guidelines_url = f"{settings.SITE_URL}/destinations/submit/guidelines/" \
        if hasattr(settings, 'SITE_URL') else '#'
    
    subject = f"Important information about your destination '{destination.name}'"
    
    # Create HTML message content using a template
    context = {
        'destination': destination,
        'rejection_reason': destination.rejection_reason,
        'submission_guidelines_url': submission_guidelines_url
    }
    
    # Use the new email template path
    html_message = render_to_string('emails/destinations/destination_rejected.html', context)
    
    # Create plain text message as fallback
    name = destination.created_by.get_full_name() or destination.created_by.username
    plain_message = f"""Hi {name},

We've reviewed your destination '{destination.name}' and we're unable to approve it at this time.

Reason for rejection: {destination.rejection_reason}

You're welcome to make the necessary changes and submit a new destination.

Thank you for your understanding.

The TravelGuides Team"""
    
    try:
        # Send email notification
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[destination.created_by.email],
            html_message=html_message,
            fail_silently=False
        )
        
        # Also create an in-app notification if the notifications app is available
        try:
            from notifications.models import Notification
            
            # Create in-app notification
            Notification.create_notification(
                recipient=destination.created_by,
                title=f"Destination '{destination.name}' Needs Updates",
                message=f"Your destination submission '{destination.name}' requires some changes before it can be approved. Reason: {destination.rejection_reason}",
                level=Notification.LEVEL_WARNING,
                related_object=destination,
                link_url=submission_guidelines_url,
                link_text="View Submission Guidelines"
            )
        except ImportError:
            # Notifications app not available, continue without in-app notification
            pass
        
        return True
    except Exception:
        return False

class StaffRequiredMixin(UserPassesTestMixin):
    """
    Mixin that tests whether a user is a manager or admin.
    
    This mixin is used to restrict access to views that should only be
    accessible to users with management permissions. It extends Django's
    UserPassesTestMixin to provide a consistent permission check across
    all administrative views in the destinations app.
    
    The mixin checks both is_staff and is_superuser flags to determine
    if the user has appropriate permissions to access protected views.
    """
    def test_func(self):
        """
        Check if the user is a manager or admin.
        
        Returns:
            bool: True if the user is a manager or admin, False otherwise
        """
        return self.request.user.is_authenticated and (
            self.request.user.is_manager or 
            self.request.user.is_admin
        )


class PendingDestinationListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """
    Display destinations pending approval for managers and admins.
    
    This view shows all destinations with PENDING approval status,
    allowing managers and admins to review and approve or reject them.
    """
    model = Destination
    template_name = 'destinations/admin/pending_destinations.html'
    context_object_name = 'destinations'
    paginate_by = 10
    
    def get_queryset(self):
        """
        Get the queryset of destinations pending approval.
        
        Returns:
            QuerySet: Filtered queryset of pending destinations
        """
        return Destination.objects.filter(
            approval_status=Destination.ApprovalStatus.PENDING
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with additional data
        """
        context = super().get_context_data(**kwargs)
        context['title'] = 'Destinations Pending Approval'
        context['pending_count'] = Destination.objects.filter(
            approval_status=Destination.ApprovalStatus.PENDING
        ).count()
        return context


class DestinationReviewView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    """
    Display a detailed view of a destination for review.
    
    This view allows managers and admins to see all details of a pending
    destination and make a decision to approve or reject it.
    """
    model = Destination
    template_name = 'destinations/admin/review_destination.html'
    context_object_name = 'destination'
    
    def get_queryset(self):
        """
        Get the queryset for this view.
        
        Returns:
            QuerySet: All destinations regardless of approval status
        """
        # Allow viewing destinations regardless of status for review purposes
        return Destination.objects.all()
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with additional data
        """
        context = super().get_context_data(**kwargs)
        destination = self.get_object()
        
        context['title'] = f'Review Destination: {destination.name}'
        context['images'] = destination.images.all()
        context['created_by_user'] = destination.created_by
        
        # If the destination has been rejected before, pre-fill the rejection reason
        if destination.approval_status == Destination.ApprovalStatus.REJECTED:
            context['rejection_reason'] = destination.rejection_reason
        
        return context


@require_http_methods(["POST"])
def approve_destination(request, pk):
    """

    Approve a destination.
    
    This view processes the approval action for a destination.
    It calls the destination's approve() method, sends notifications to the creator,
    and redirects to the pending destinations list with a success message.
    
    Args:
        request: The HTTP request
        pk: Primary key of the destination to approve
        
    Returns:
        HttpResponseRedirect: Redirect to the pending destinations list
    """
    if not request.user.is_authenticated or not (request.user.is_manager or request.user.is_admin):
        messages.error(request, "You don't have permission to approve destinations.")
        return redirect('destinations:destination_list')
    
    destination = get_object_or_404(Destination, pk=pk)
    
    if destination.approve(request.user):
        # Send approval notification to destination creator
        notification_sent = send_destination_approval_notification(destination)
        
        success_message = f'Destination "{destination.name}" has been approved and is now visible on the site.'
        if notification_sent and destination.created_by:
            success_message += f' Notification sent to {destination.created_by.username}.'
            
        messages.success(request, success_message)
    else:
        messages.error(
            request, 
            f'Could not approve destination "{destination.name}". It may already be approved.'
        )
    
    return redirect('destinations:admin_pending_destinations')


@require_http_methods(["POST"])
def reject_destination(request, pk):
    """
    Reject a destination.
    
    This view processes the rejection action for a destination.
    It calls the destination's reject() method with a reason, sends notifications
    to the creator, and redirects to the pending destinations list with a success message.
    
    Args:
        request: The HTTP request
        pk: Primary key of the destination to reject
        
    Returns:
        HttpResponseRedirect: Redirect to the pending destinations list
    """
    if not request.user.is_authenticated or not (request.user.is_manager or request.user.is_admin):
        messages.error(request, "You don't have permission to reject destinations.")
        return redirect('destinations:destination_list')
    
    destination = get_object_or_404(Destination, pk=pk)
    rejection_reason = request.POST.get('rejection_reason')
    
    if not rejection_reason:
        messages.error(request, "Please provide a reason for rejecting the destination.")
        return redirect('destinations:review_destination', pk=pk)
    
    if destination.reject(request.user, rejection_reason):
        # Send rejection notification to destination creator
        notification_sent = send_destination_rejection_notification(destination)
        
        success_message = f'Destination "{destination.name}" has been rejected.'
        if notification_sent and destination.created_by:
            success_message += f' Notification sent to {destination.created_by.username}.'
            
        messages.success(request, success_message)
    else:
        messages.error(
            request, 
            f'Could not reject destination "{destination.name}". It may have already been processed.'
        )
    
    return redirect('destinations:admin_pending_destinations')
