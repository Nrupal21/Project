"""
View for displaying safety information by risk level.
"""
from django.views.generic import ListView
from django.db.models import Q
from destinations.models import Destination, Region
from .models import SafetyInformation


class RiskLevelSafetyInfoView(ListView):
    """
    Display safety information for a specific risk level.
    
    Shows all active safety information for a given risk level,
    with options for filtering by destination, region, and category.
    """
    template_name = 'emergency/risk_level_safety.html'
    context_object_name = 'safety_info_list'
    paginate_by = 10
    
    def get_queryset(self):
        """
        Get the list of safety information for the specified risk level.
        
        Returns:
            QuerySet: Filtered queryset of safety information
        """
        risk_level = self.kwargs.get('risk_level')
        queryset = SafetyInformation.objects.filter(
            risk_level__iexact=risk_level,
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
        
        # Filter by category if provided
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__iexact=category)
        
        return queryset.order_by('-last_updated')
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        
        Adds risk level information and filter parameters to the context.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with added data
        """
        context = super().get_context_data(**kwargs)
        risk_level = self.kwargs.get('risk_level')
        
        # Add risk level to context
        context['risk_level'] = risk_level
        
        # Add filter parameters to context
        context['selected_destination'] = self.request.GET.get('destination', '')
        context['selected_region'] = self.request.GET.get('region', '')
        context['selected_category'] = self.request.GET.get('category', '')
        
        # Get unique categories for this risk level
        context['categories'] = SafetyInformation.objects.filter(
            risk_level__iexact=risk_level,
            is_active=True
        ).values_list('category', flat=True).distinct().order_by('category')
        
        # Get unique destinations for this risk level
        context['destinations'] = Destination.objects.filter(
            safety_information__risk_level__iexact=risk_level,
            safety_information__is_active=True
        ).distinct().order_by('name')
        
        # Get unique regions for this risk level
        context['regions'] = Region.objects.filter(
            safety_information__risk_level__iexact=risk_level,
            safety_information__is_active=True
        ).distinct().order_by('name')
        
        return context
