"""
View for displaying safety information by category.
"""
from django.views.generic import ListView
from django.db.models import Q
from destinations.models import Destination, Region
from .models import SafetyInformation


class CategorySafetyInfoView(ListView):
    """
    Display safety information for a specific category.
    
    Shows all active safety information for a given category,
    with options for filtering by destination and region.
    """
    template_name = 'emergency/category_safety.html'
    context_object_name = 'safety_info_list'
    paginate_by = 10
    
    def get_queryset(self):
        """
        Get the list of safety information for the specified category.
        
        Returns:
            QuerySet: Filtered queryset of safety information
        """
        category = self.kwargs.get('category')
        queryset = SafetyInformation.objects.filter(
            category__iexact=category,
            is_active=True
        ).select_related('destination', 'region')
        
        # Filter by destination if provided
        destination_slug = self.request.GET.get('destination')
        if destination_slug:
            queryset = queryset.filter(destination__slug=destination_slug)
        
        # Filter by region if provided
        region_slug = self.request.GET.get('region')
        if region_slug:
            queryset = queryset.filter(region__slug=region_slug)
        
        # Filter by risk level if provided
        risk_level = self.request.GET.get('risk_level')
        if risk_level:
            queryset = queryset.filter(risk_level__iexact=risk_level)
        
        return queryset.order_by('-last_updated')
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        
        Adds category information and filter parameters to the context.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with added data
        """
        context = super().get_context_data(**kwargs)
        category = self.kwargs.get('category')
        
        # Add category to context
        context['category'] = category
        
        # Add filter parameters to context
        context['selected_destination'] = self.request.GET.get('destination', '')
        context['selected_region'] = self.request.GET.get('region', '')
        context['selected_risk_level'] = self.request.GET.get('risk_level', '')
        
        # Get unique destinations for this category
        context['destinations'] = Destination.objects.filter(
            safety_information__category__iexact=category,
            safety_information__is_active=True
        ).distinct().order_by('name')
        
        # Get unique regions for this category
        context['regions'] = Region.objects.filter(
            safety_information__category__iexact=category,
            safety_information__is_active=True
        ).distinct().order_by('name')
        
        # Get unique risk levels for this category
        context['risk_levels'] = SafetyInformation.objects.filter(
            category__iexact=category,
            is_active=True
        ).values_list('risk_level', flat=True).distinct().order_by('risk_level')
        
        return context
