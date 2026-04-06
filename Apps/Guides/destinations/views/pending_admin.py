"""
Admin views for managing pending destinations.

This module contains views for handling the pending destinations workflow:
- Listing pending destinations submitted by local guides
- Detailed review interface for each pending destination
- Approval process to transfer data to the main Destination table
- Rejection workflow with notification management

All views are protected by authentication and permission checks to ensure
only authorized staff can access these administrative functions.
"""

from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseRedirect
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required

# Import models
from destinations.models import PendingDestination, PendingDestinationImage


def send_destination_approval_notification(destination):
    """
    Send an email notification to the destination creator when their pending destination is approved.
    
    This function sends both email and in-app notifications to inform the local guide
    that their destination has been approved and is now live on the site.
    
    Args:
        destination: The approved Destination object
        
    Returns:
        bool: True if notification sent successfully, False otherwise
    """
    if not destination.created_by or not destination.created_by.email:
        return False
    
    # Get current reward points balance if available
    try:
        from rewards.models import RewardPoints
        reward_points = RewardPoints.get_user_point_balance(destination.created_by)
    except (ImportError, AttributeError):
        reward_points = 'updated'
    
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
    
    # Use the email template
    html_message = render_to_string('emails/destinations/destination_approved.html', context)
    
    # Create plain text message as fallback
    name = destination.created_by.get_full_name() or destination.created_by.username
    plain_message = f"""Hi {name},

Great news! Your destination '{destination.name}' has been approved and is now visible on the TravelGuides site.

You've been awarded 50 reward points for your contribution!

Thank you for helping us grow our community of travel destinations.

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
        
        # Create in-app notification if available
        try:
            from notifications.models import Notification
            Notification.objects.create(
                user=destination.created_by,
                title=f"Destination '{destination.name}' approved!",
                message=f"Your destination has been approved and is now live on the site.",
                notification_type='SUCCESS',
                reference_type='Destination',
                reference_id=str(destination.id)
            )
        except ImportError:
            pass
            
        return True
    except Exception:
        return False


def send_destination_rejection_notification(pending_destination):
    """
    Send an email notification when a pending destination is rejected.
    
    This function notifies the local guide about their rejected destination submission,
    including the specific reason for rejection provided by the reviewer.
    
    Args:
        pending_destination: The PendingDestination object that was rejected
        
    Returns:
        bool: True if notification sent successfully, False otherwise
    """
    if not pending_destination.created_by or not pending_destination.created_by.email:
        return False
        
    subject = f"Your destination '{pending_destination.name}' needs revisions"
    
    # Create HTML message content using a template
    context = {
        'destination': pending_destination,
        'rejection_reason': pending_destination.rejection_reason,
    }
    
    # Use the email template
    html_message = render_to_string('emails/destinations/destination_rejected.html', context)
    
    # Create plain text message as fallback
    name = pending_destination.created_by.get_full_name() or pending_destination.created_by.username
    plain_message = f"""Hi {name},

Your destination '{pending_destination.name}' needs some revisions before it can be approved.

Reason for revision request:
{pending_destination.rejection_reason}

Please update your submission addressing these points and resubmit for approval.

Thank you for your contribution to our travel community.

The TravelGuides Team"""
    
    try:
        # Send email notification
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[pending_destination.created_by.email],
            html_message=html_message,
            fail_silently=False
        )
        
        # Create in-app notification if available
        try:
            from notifications.models import Notification
            Notification.objects.create(
                user=pending_destination.created_by,
                title=f"Destination '{pending_destination.name}' needs revisions",
                message=f"Your destination submission needs revisions: {pending_destination.rejection_reason[:50]}...",
                notification_type='WARNING',
                reference_type='PendingDestination',
                reference_id=str(pending_destination.id)
            )
        except ImportError:
            pass
            
        return True
    except Exception:
        return False


class StaffRequiredMixin(UserPassesTestMixin):
    """
    Mixin that tests whether a user is a manager or admin.
    
    This mixin restricts access to administrative views to ensure only
    staff members can approve or reject destinations.
    """
    def test_func(self):
        """
        Check if the current user has staff permissions.
        
        Returns:
            bool: True if user is a manager or admin, False otherwise
        """
        # First make sure the user is authenticated
        if not self.request.user.is_authenticated:
            return False
            
        # Check if user has staff permissions
        if hasattr(self.request.user, 'is_manager') and self.request.user.is_manager:
            return True
            
        if hasattr(self.request.user, 'is_admin') and self.request.user.is_admin:
            return True
            
        # Fallback to Django's built-in staff status
        return self.request.user.is_staff or self.request.user.is_superuser


class PendingDestinationListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """
    Display pending destinations awaiting approval or rejection.
    
    This view shows all pending destinations submitted by local guides,
    allowing managers and admins to review them.
    """
    model = PendingDestination
    template_name = 'destinations/admin/pending_destinations.html'
    context_object_name = 'destinations'  # Keep same name for template compatibility
    paginate_by = 10
    
    def get_queryset(self):
        """
        Get pending destinations that need review.
        
        Returns:
            QuerySet: Filtered queryset of pending destinations
        """
        # Return pending destinations ordered by creation date (newest first)
        return PendingDestination.objects.filter(
            approval_status=PendingDestination.ApprovalStatus.PENDING
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with additional data
        """
        context = super().get_context_data(**kwargs)
        context['title'] = 'Pending Destinations'
        context['pending_count'] = self.get_queryset().count()
        
        # Add stats for approved and rejected destinations
        context['approved_count'] = PendingDestination.objects.filter(
            approval_status=PendingDestination.ApprovalStatus.APPROVED
        ).count()
        
        context['rejected_count'] = PendingDestination.objects.filter(
            approval_status=PendingDestination.ApprovalStatus.REJECTED
        ).count()
        
        return context


class PendingDestinationReviewView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    """
    Detailed view for reviewing a pending destination.
    
    This view displays all information about a pending destination
    and provides options to approve or reject it.
    """
    model = PendingDestination
    template_name = 'destinations/admin/review_destination.html'
    context_object_name = 'destination'  # Keep same name for template compatibility
    
    def get_queryset(self):
        """
        Get the queryset for this view.
        
        Returns:
            QuerySet: All pending destinations
        """
        return PendingDestination.objects.all()
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with additional data
        """
        context = super().get_context_data(**kwargs)
        
        # Get pending destination images
        destination = self.get_object()
        context['images'] = destination.images.all()
        
        # Add information about the creator
        context['created_by'] = destination.created_by
        context['created_at'] = destination.created_at
        
        # Add title for the page
        context['title'] = f'Review: {destination.name}'
        
        return context


@login_required
@require_http_methods(['POST'])
def approve_pending_destination(request, pk):
    """
    Approve a pending destination and transfer it to the main Destination table.
    
    This view handles the approval process, transfers data to the main table,
    sends notifications, and awards points to the creator.
    
    Args:
        request: The HTTP request
        pk: Primary key of the pending destination
        
    Returns:
        HttpResponseRedirect: Redirect to the pending destinations list
    """
    # Get the pending destination or return 404
    pending_destination = get_object_or_404(PendingDestination, pk=pk)
    
    # Check if user has permission to approve
    if not hasattr(request.user, 'is_manager') or not request.user.is_manager:
        if not hasattr(request.user, 'is_admin') or not request.user.is_admin:
            if not request.user.is_staff and not request.user.is_superuser:
                messages.error(request, "You don't have permission to approve destinations.")
                return redirect('destinations:admin_pending_destinations')
    
    # Transfer the pending destination to the approved Destination table
    new_destination = pending_destination.approve_and_transfer(request.user)
    
    if new_destination:
        # Send notification to destination creator
        send_destination_approval_notification(new_destination)
        
        # Show success message
        messages.success(
            request,
            f"Destination '{pending_destination.name}' has been approved and is now live on the site."
        )
    else:
        # Show error message
        messages.error(
            request,
            f"There was a problem approving destination '{pending_destination.name}'."
        )
    
    # Redirect to pending destinations list
    return HttpResponseRedirect(reverse_lazy('destinations:admin_pending_destinations'))


@login_required
@require_http_methods(['POST'])
def reject_pending_destination(request, pk):
    """
    Reject a pending destination.
    
    This view handles the rejection process, updates the status,
    and sends notifications to the creator.
    
    Args:
        request: The HTTP request
        pk: Primary key of the pending destination
        
    Returns:
        HttpResponseRedirect: Redirect to the pending destinations list
    """
    # Get the pending destination or return 404
    pending_destination = get_object_or_404(PendingDestination, pk=pk)
    
    # Check if user has permission to reject
    if not hasattr(request.user, 'is_manager') or not request.user.is_manager:
        if not hasattr(request.user, 'is_admin') or not request.user.is_admin:
            if not request.user.is_staff and not request.user.is_superuser:
                messages.error(request, "You don't have permission to reject destinations.")
                return redirect('destinations:admin_pending_destinations')
    
    # Get rejection reason from form
    rejection_reason = request.POST.get('rejection_reason', '')
    
    if not rejection_reason:
        messages.error(request, "Please provide a reason for rejection.")
        return redirect('destinations:admin_review_destination', pk=pk)
    
    # Reject the pending destination
    if pending_destination.reject(request.user, rejection_reason):
        # Send notification to destination creator
        send_destination_rejection_notification(pending_destination)
        
        # Show success message
        messages.success(
            request,
            f"Destination '{pending_destination.name}' has been rejected."
        )
    else:
        # Show error message
        messages.error(
            request,
            f"There was a problem rejecting destination '{pending_destination.name}'."
        )
    
    # Redirect to pending destinations list
    return HttpResponseRedirect(reverse_lazy('destinations:admin_pending_destinations'))
