"""
Manager dashboard view for destination approval workflow.

This file contains the Manager Dashboard view class which provides managers and administrators
with an overview of the destination approval workflow, including pending destinations,
approval statistics, and quick access to management functions.

The view aggregates data about pending, approved, and rejected destinations to
provide a centralized interface for destination moderation.
"""

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, F, Prefetch
from django.utils import timezone
from datetime import timedelta

# Local imports
from destinations.views.admin import StaffRequiredMixin
from destinations.models import Destination, PendingDestination, PendingDestinationImage
from accounts.models import User, GuideApplication

class ManagerDashboardView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    """
    Manager dashboard view displaying an overview of destination approval data.
    
    This view provides a centralized dashboard for managers and admins to monitor
    the destination approval workflow, showing counts of pending, approved, and
    rejected destinations, along with a list of recent pending submissions.
    
    Only staff members and managers can access this view, enforced by the
    StaffRequiredMixin which checks for appropriate permissions.
    """
    template_name = 'destinations/admin/manager_dashboard.html'
    
    def get_context_data(self, **kwargs):
        """
        Prepare context data for the manager dashboard template.
        
        Aggregates statistics about destinations in different approval states,
        provides a list of recent pending submissions, and adds additional
        analytics data for the dashboard cards.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with dashboard data
        """
        context = super().get_context_data(**kwargs)
        
        # Count destinations in each approval status
        pending_destinations_count = Destination.objects.filter(
            approval_status=Destination.ApprovalStatus.PENDING
        ).count()
        
        approved_destinations_count = Destination.objects.filter(
            approval_status=Destination.ApprovalStatus.APPROVED
        ).count()
        
        rejected_destinations_count = Destination.objects.filter(
            approval_status=Destination.ApprovalStatus.REJECTED
        ).count()
        
        total_destinations_count = Destination.objects.count()
        
        featured_destinations_count = Destination.objects.filter(
            is_featured=True
        ).count()
        
        # Get recent pending destinations with related data
        recent_pending_destinations = PendingDestination.objects.select_related(
            'created_by', 'region'
        ).prefetch_related(
            Prefetch('images', queryset=PendingDestinationImage.objects.filter(is_primary=True))
        ).filter(
            approval_status=PendingDestination.ApprovalStatus.PENDING
        ).order_by('-created_at')[:5]  # Limit to 5 most recent
        
        # Get pending guide applications
        pending_guide_applications = GuideApplication.objects.select_related(
            'user', 'reviewed_by'
        ).filter(
            status__in=['PENDING', 'UNDER_REVIEW']
        ).order_by('application_date')[:5]
        
        # Add to context
        context['recent_pending_destinations'] = recent_pending_destinations
        context['pending_guide_applications'] = pending_guide_applications
        context['pending_guide_applications_count'] = GuideApplication.objects.filter(
            status__in=['PENDING', 'UNDER_REVIEW']
        ).count()
        
        # Count recent submissions (last 7 days)
        one_week_ago = timezone.now() - timedelta(days=7)
        recent_submissions_count = PendingDestination.objects.filter(
            created_at__gte=one_week_ago
        ).count()
        
        # Get pending destinations by status
        pending_by_status = PendingDestination.objects.filter(
            approval_status=PendingDestination.ApprovalStatus.PENDING
        ).values('approval_status').annotate(count=Count('id'))
        
        # Get pending destinations by creator (top 5)
        top_submitters = User.objects.filter(
            pending_destinations__isnull=False
        ).annotate(
            submission_count=Count('pending_destinations')
        ).order_by('-submission_count')[:5]
        
        # Get pending destinations by region
        pending_by_region = PendingDestination.objects.filter(
            approval_status=PendingDestination.ApprovalStatus.PENDING
        ).values('region__name').annotate(
            count=Count('id'),
            region_name=F('region__name')
        ).exclude(region__isnull=True).order_by('-count')
        
        # Add all data to context with detailed pending destinations info
        context.update({
            'pending_destinations_count': pending_destinations_count,
            'approved_destinations_count': approved_destinations_count,
            'rejected_destinations_count': rejected_destinations_count,
            'total_destinations_count': total_destinations_count,
            'featured_destinations_count': featured_destinations_count,
            'recent_pending_destinations': recent_pending_destinations,
            'recent_submissions_count': recent_submissions_count,
            'pending_by_status': pending_by_status,
            'top_submitters': top_submitters,
            'pending_by_region': pending_by_region,
            'now': timezone.now(),
        })
        
        return context
