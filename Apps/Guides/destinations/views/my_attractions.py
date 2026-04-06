"""
Views for displaying a guide's attractions.

This module contains views for displaying and managing attractions created by the currently
logged-in guide, with filtering and pagination support.
"""
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _

from destinations.models import Attraction


class MyAttractionsView(LoginRequiredMixin, ListView):
    """
    View for displaying attractions created by the current user.
    
    This view shows a paginated list of all attractions created by the currently
    logged-in guide, with options to filter by status and other criteria.
    
    Template used: 'destinations/my_attractions.html'
    Context data includes:
    - attractions: Paginated queryset of the user's attractions
    - status_filter: The current status filter being applied
    - status_choices: Available status choices for filtering
    """
    model = Attraction
    template_name = 'destinations/my_attractions.html'
    context_object_name = 'attractions'
    paginate_by = 12
    
    def get_queryset(self):
        """
        Get the queryset of attractions created by the current user.
        
        Applies filtering based on the 'status' query parameter if provided.
        
        Returns:
            QuerySet: Filtered queryset of the user's attractions
        """
        queryset = Attraction.objects.filter(
            created_by=self.request.user
        ).select_related('destination').order_by('-created_at')
        
        status_filter = self.request.GET.get('status', '').lower()
        if status_filter in ['pending', 'approved', 'rejected']:
            queryset = queryset.filter(approval_status=status_filter)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.
        
        Adds status filter information and available status choices to the context.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with added data
        """
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '').lower()
        context['status_choices'] = [
            ('', _('All')),
            ('pending', _('Pending')),
            ('approved', _('Approved')),
            ('rejected', _('Rejected'))
        ]
        return context
