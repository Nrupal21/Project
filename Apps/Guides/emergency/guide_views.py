"""
Views for emergency guides.
"""
from django.views.generic import ListView, DetailView
from django.db.models import Q
from django.shortcuts import get_object_or_404
from destinations.models import Destination, Region
from .models import EmergencyGuide, EmergencyService


class EmergencyGuideListView(ListView):
    """
    Display a list of emergency guides.
    
    Renders a template with all active emergency guides,
    with options for filtering by category and search query.
    """
    model = EmergencyGuide
    template_name = 'emergency/guide_list.html'
    context_object_name = 'guides'
    paginate_by = 10
    
    def get_queryset(self):
        """
        Get the list of emergency guides with filtering.
        
        Returns:
            QuerySet: Filtered queryset of emergency guides
        """
        queryset = EmergencyGuide.objects.filter(is_active=True)
        
        # Filter by category if provided
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__iexact=category)
            
        # Search functionality
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(category__icontains=search_query)
            )
            
        return queryset.order_by('category', 'title')
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with added data
        """
        context = super().get_context_data(**kwargs)
        
        # Add filter parameters to context
        context['selected_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('q', '')
        
        # Get unique categories for filter dropdown
        context['categories'] = EmergencyGuide.objects.filter(
            is_active=True
        ).values_list('category', flat=True).distinct().order_by('category')
        
        return context


class EmergencyGuideDetailView(DetailView):
    """
    Display detailed information about a specific emergency guide.
    
    Shows the full content of an emergency guide along with related services.
    """
    model = EmergencyGuide
    template_name = 'emergency/guide_detail.html'
    context_object_name = 'guide'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        """
        Get the emergency guide with related data.
        
        Returns:
            QuerySet: Filtered queryset of emergency guides
        """
        return EmergencyGuide.objects.filter(is_active=True).prefetch_related('related_services')
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with added data
        """
        context = super().get_context_data(**kwargs)
        guide = self.object
        
        # Get related services
        context['related_services'] = guide.related_services.filter(is_active=True)
        
        # Get related guides in the same category
        context['related_guides'] = EmergencyGuide.objects.filter(
            category=guide.category,
            is_active=True
        ).exclude(pk=guide.pk).order_by('title')
        
        return context
