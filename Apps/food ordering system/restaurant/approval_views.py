"""
Enhanced views for restaurant approval management.

Provides comprehensive dashboard and tools for managers/admins to review,
approve, or reject restaurant registrations with detailed analytics and
workflow management.
"""

from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Avg, F
from django.utils import timezone
from datetime import timedelta
from restaurant.models import Restaurant
from restaurant.workflow import RegistrationWorkflow, AutoApprovalEngine
import logging

logger = logging.getLogger(__name__)


class ManagerRequiredMixin(UserPassesTestMixin):
    """
    Mixin to restrict access to managers and staff only.
    
    Ensures that only users with staff privileges or manager role
    can access approval management views.
    """
    
    def test_func(self):
        """
        Check if user has manager/staff privileges.
        
        Returns:
            bool: True if user is staff or manager
        """
        return self.request.user.is_staff or self.request.user.is_superuser


class ApprovalDashboardView(LoginRequiredMixin, ManagerRequiredMixin, TemplateView):
    """
    Comprehensive dashboard for managing restaurant approvals.
    
    Displays overview statistics, pending applications queue,
    recent activity, and quick action tools for managers.
    """
    
    template_name = 'restaurant/approval_dashboard.html'
    
    def get_context_data(self, **kwargs):
        """
        Prepare dashboard context with statistics and application lists.
        
        Args:
            **kwargs: Additional keyword arguments
            
        Returns:
            dict: Template context data
        """
        context = super().get_context_data(**kwargs)
        
        # Overall statistics
        context['total_restaurants'] = Restaurant.objects.count()
        context['pending_count'] = Restaurant.objects.filter(
            approval_status__in=['pending', 'submitted']
        ).count()
        context['approved_count'] = Restaurant.objects.filter(
            approval_status='approved'
        ).count()
        context['rejected_count'] = Restaurant.objects.filter(
            approval_status='rejected'
        ).count()
        
        # Pending applications (prioritized)
        pending_restaurants = Restaurant.objects.filter(
            approval_status__in=['pending', 'submitted']
        ).select_related('owner').order_by('created_at')
        
        # Add trust scores and priority
        pending_with_scores = []
        for restaurant in pending_restaurants:
            eligible, reason, trust_score = AutoApprovalEngine.check_eligibility(restaurant)
            days_pending = (timezone.now() - restaurant.created_at).days
            
            # Calculate priority (higher = more urgent)
            priority = days_pending * 10 + (100 - trust_score)
            
            pending_with_scores.append({
                'restaurant': restaurant,
                'trust_score': trust_score,
                'days_pending': days_pending,
                'priority': priority,
                'auto_approve_eligible': eligible,
                'auto_approve_reason': reason,
            })
        
        # Sort by priority (highest first)
        pending_with_scores.sort(key=lambda x: x['priority'], reverse=True)
        context['pending_applications'] = pending_with_scores[:10]
        
        # Recent activity (last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        context['recent_approved'] = Restaurant.objects.filter(
            approval_status='approved',
            approved_at__gte=week_ago
        ).select_related('owner', 'approved_by').order_by('-approved_at')[:5]
        
        context['recent_rejected'] = Restaurant.objects.filter(
            approval_status='rejected',
            rejected_at__gte=week_ago
        ).select_related('owner', 'rejected_by').order_by('-rejected_at')[:5]
        
        # Approval metrics
        total_processed = context['approved_count'] + context['rejected_count']
        if total_processed > 0:
            context['approval_rate'] = (
                context['approved_count'] / total_processed
            ) * 100
        else:
            context['approval_rate'] = 0
        
        # Average processing time
        recently_approved = Restaurant.objects.filter(
            approval_status='approved',
            approved_at__isnull=False,
            created_at__gte=week_ago
        )
        
        if recently_approved.exists():
            total_time = sum([
                (r.approved_at - r.created_at).total_seconds() / 3600
                for r in recently_approved
                if r.approved_at
            ])
            context['avg_processing_hours'] = total_time / recently_approved.count()
        else:
            context['avg_processing_hours'] = 0
        
        # Quick stats cards
        context['urgent_applications'] = Restaurant.objects.filter(
            approval_status__in=['pending', 'submitted'],
            created_at__lte=timezone.now() - timedelta(days=3)
        ).count()
        
        context['auto_approve_eligible'] = sum(
            1 for app in pending_with_scores if app['auto_approve_eligible']
        )
        
        return context


class PendingRestaurantsListView(LoginRequiredMixin, ManagerRequiredMixin, ListView):
    """
    Detailed list view of all pending restaurant applications.
    
    Provides filtering, sorting, and bulk action capabilities
    for managing the approval queue.
    """
    
    model = Restaurant
    template_name = 'restaurant/pending_list.html'
    context_object_name = 'restaurants'
    paginate_by = 20
    
    def get_queryset(self):
        """
        Get filtered and sorted queryset of pending restaurants.
        
        Returns:
            QuerySet: Filtered restaurant queryset
        """
        queryset = Restaurant.objects.filter(
            approval_status__in=['pending', 'submitted']
        ).select_related('owner').order_by('created_at')
        
        # Apply filters
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(owner__username__icontains=search) |
                Q(cuisine_type__icontains=search)
            )
        
        cuisine_filter = self.request.GET.get('cuisine')
        if cuisine_filter:
            queryset = queryset.filter(cuisine_type=cuisine_filter)
        
        # Apply sorting
        sort_by = self.request.GET.get('sort', 'oldest')
        if sort_by == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort_by == 'name':
            queryset = queryset.order_by('name')
        elif sort_by == 'trust_score':
            # Calculate trust scores (more complex, handled in context)
            pass
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Add filtering and sorting context.
        
        Args:
            **kwargs: Additional keyword arguments
            
        Returns:
            dict: Template context data
        """
        context = super().get_context_data(**kwargs)
        
        # Add trust scores to each restaurant
        restaurants_with_scores = []
        for restaurant in context['restaurants']:
            eligible, reason, trust_score = AutoApprovalEngine.check_eligibility(restaurant)
            restaurants_with_scores.append({
                'restaurant': restaurant,
                'trust_score': trust_score,
                'auto_approve_eligible': eligible,
                'days_pending': (timezone.now() - restaurant.created_at).days,
            })
        
        context['restaurants_data'] = restaurants_with_scores
        context['cuisine_types'] = Restaurant.objects.filter(
            approval_status__in=['pending', 'submitted']
        ).values_list('cuisine_type', flat=True).distinct()
        
        return context


class RestaurantReviewView(LoginRequiredMixin, ManagerRequiredMixin, DetailView):
    """
    Detailed review page for a specific restaurant application.
    
    Displays complete restaurant information, owner details,
    trust score analysis, and approval/rejection actions.
    """
    
    model = Restaurant
    template_name = 'restaurant/review_detail.html'
    context_object_name = 'restaurant'
    
    def get_context_data(self, **kwargs):
        """
        Prepare detailed review context.
        
        Args:
            **kwargs: Additional keyword arguments
            
        Returns:
            dict: Template context data
        """
        context = super().get_context_data(**kwargs)
        restaurant = self.object
        
        # Trust score and eligibility
        eligible, reason, trust_score = AutoApprovalEngine.check_eligibility(restaurant)
        context['trust_score'] = trust_score
        context['auto_approve_eligible'] = eligible
        context['auto_approve_reason'] = reason
        
        # Owner information
        owner = restaurant.owner
        context['owner_stats'] = {
            'total_restaurants': Restaurant.objects.filter(owner=owner).count(),
            'approved_restaurants': Restaurant.objects.filter(
                owner=owner,
                approval_status='approved'
            ).count(),
            'rejected_restaurants': Restaurant.objects.filter(
                owner=owner,
                approval_status='rejected'
            ).count(),
            'account_age_days': (timezone.now() - owner.date_joined).days,
        }
        
        # Review history if owner has other restaurants
        context['other_restaurants'] = Restaurant.objects.filter(
            owner=owner
        ).exclude(id=restaurant.id).order_by('-created_at')[:5]
        
        # Application timeline
        context['days_pending'] = (timezone.now() - restaurant.created_at).days
        
        return context
    
    def post(self, request, *args, **kwargs):
        """
        Handle approval/rejection actions.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            HttpResponse: Redirect to dashboard or error display
        """
        restaurant = self.get_object()
        action = request.POST.get('action')
        
        workflow = RegistrationWorkflow(restaurant)
        
        if action == 'approve':
            notes = request.POST.get('notes', '')
            success, message = workflow.approve(
                approved_by=request.user,
                notes=notes,
                request=request
            )
            
            if success:
                messages.success(
                    request,
                    f'✅ Restaurant "{restaurant.name}" has been approved!'
                )
                logger.info(
                    f'Restaurant {restaurant.id} approved by {request.user.username}'
                )
            else:
                messages.error(request, f'Error approving restaurant: {message}')
            
            return redirect('restaurant:approval_dashboard')
        
        elif action == 'reject':
            reason = request.POST.get('reason', '')
            if not reason:
                messages.error(request, 'Please provide a reason for rejection')
                return redirect('restaurant:review_detail', pk=restaurant.pk)
            
            success, message = workflow.reject(
                rejected_by=request.user,
                reason=reason,
                request=request
            )
            
            if success:
                messages.warning(
                    request,
                    f'Restaurant "{restaurant.name}" has been rejected.'
                )
                logger.info(
                    f'Restaurant {restaurant.id} rejected by {request.user.username}'
                )
            else:
                messages.error(request, f'Error rejecting restaurant: {message}')
            
            return redirect('restaurant:approval_dashboard')
        
        return self.get(request, *args, **kwargs)


class BulkApprovalView(LoginRequiredMixin, ManagerRequiredMixin, TemplateView):
    """
    Bulk approval interface for processing multiple applications.
    
    Allows managers to quickly review and approve/reject multiple
    restaurants at once with batch operations.
    """
    
    template_name = 'restaurant/bulk_approval.html'
    
    def post(self, request, *args, **kwargs):
        """
        Handle bulk approval actions.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            JsonResponse: Result of bulk operation
        """
        action = request.POST.get('action')
        restaurant_ids = request.POST.getlist('restaurant_ids[]')
        
        if not restaurant_ids:
            return JsonResponse({
                'success': False,
                'message': 'No restaurants selected'
            })
        
        results = {
            'success': 0,
            'failed': 0,
            'total': len(restaurant_ids)
        }
        
        restaurants = Restaurant.objects.filter(
            id__in=restaurant_ids,
            approval_status__in=['pending', 'submitted']
        )
        
        if action == 'approve_all':
            for restaurant in restaurants:
                workflow = RegistrationWorkflow(restaurant)
                success, message = workflow.approve(
                    approved_by=request.user,
                    notes='Bulk approved',
                    request=request
                )
                
                if success:
                    results['success'] += 1
                else:
                    results['failed'] += 1
        
        elif action == 'auto_approve_eligible':
            for restaurant in restaurants:
                eligible, reason, _ = AutoApprovalEngine.check_eligibility(restaurant)
                
                if eligible:
                    workflow = RegistrationWorkflow(restaurant)
                    success, message = workflow.approve(
                        approved_by=request.user,
                        notes=f'Auto-approved: {reason}',
                        request=request
                    )
                    
                    if success:
                        results['success'] += 1
                    else:
                        results['failed'] += 1
                else:
                    results['failed'] += 1
        
        return JsonResponse({
            'success': True,
            'results': results,
            'message': f'Processed {results["success"]} successfully, {results["failed"]} failed'
        })


class ApprovalAnalyticsView(LoginRequiredMixin, ManagerRequiredMixin, TemplateView):
    """
    Analytics dashboard for approval metrics and trends.
    
    Provides visualizations and detailed statistics about the
    approval process, manager performance, and application trends.
    """
    
    template_name = 'restaurant/approval_analytics.html'
    
    def get_context_data(self, **kwargs):
        """
        Prepare analytics context with comprehensive metrics.
        
        Args:
            **kwargs: Additional keyword arguments
            
        Returns:
            dict: Template context data
        """
        context = super().get_context_data(**kwargs)
        
        # Time-based statistics (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # Submissions per day
        daily_submissions = []
        daily_approvals = []
        
        for i in range(30):
            day = timezone.now() - timedelta(days=29-i)
            day_start = day.replace(hour=0, minute=0, second=0)
            day_end = day.replace(hour=23, minute=59, second=59)
            
            submissions = Restaurant.objects.filter(
                created_at__range=(day_start, day_end)
            ).count()
            
            approvals = Restaurant.objects.filter(
                approved_at__range=(day_start, day_end)
            ).count()
            
            daily_submissions.append({
                'date': day.strftime('%Y-%m-%d'),
                'count': submissions
            })
            
            daily_approvals.append({
                'date': day.strftime('%Y-%m-%d'),
                'count': approvals
            })
        
        context['daily_submissions'] = daily_submissions
        context['daily_approvals'] = daily_approvals
        
        # Manager performance
        from django.contrib.auth.models import User
        managers = User.objects.filter(
            Q(is_staff=True) | Q(is_superuser=True)
        ).distinct()
        
        manager_stats = []
        for manager in managers:
            approved = Restaurant.objects.filter(
                approved_by=manager,
                approved_at__gte=thirty_days_ago
            ).count()
            
            rejected = Restaurant.objects.filter(
                rejected_by=manager,
                rejected_at__gte=thirty_days_ago
            ).count()
            
            manager_stats.append({
                'manager': manager,
                'approved': approved,
                'rejected': rejected,
                'total': approved + rejected
            })
        
        context['manager_stats'] = sorted(
            manager_stats,
            key=lambda x: x['total'],
            reverse=True
        )[:10]
        
        # Cuisine type distribution
        cuisine_stats = Restaurant.objects.filter(
            approval_status='approved'
        ).values('cuisine_type').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        context['cuisine_distribution'] = list(cuisine_stats)
        
        # Average processing time by cuisine
        context['avg_processing_by_cuisine'] = []
        
        return context
