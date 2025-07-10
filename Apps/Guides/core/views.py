"""
Views for the core app.

This module contains the views for the core functionality of the application,
including the home page, about page, and contact page.
"""
from django.views.generic import TemplateView
from django.shortcuts import render
from destinations.models import Destination, DestinationImage
from tours.models import Tour, TourCategory


class HomeView(TemplateView):
    """
    View for the home page.
    
    This class renders the home template and populates it with featured destinations,
    tours, and tour categories from the database.
    """
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        """
        Add featured and popular destinations and tours to the context.
        
        This method retrieves featured and popular destinations, tours, and active tour categories
        from the database. It ensures that only active and valid items are included.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: The context dictionary with added featured and popular items
        """
        context = super().get_context_data(**kwargs)
        
        try:
            # Debug: Print all destinations for testing
            all_destinations = Destination.objects.all()
            print(f"Total destinations in DB: {all_destinations.count()}")
            for dest in all_destinations:
                print(f"- {dest.name} (Active: {dest.is_active}, Featured: {dest.is_featured})")
            
            # Get featured destinations (limit to 6)
            featured_destinations = list(Destination.objects.filter(
                is_featured=True,
                is_active=True
            ).prefetch_related('images')[:6])
            
            # Get popular destinations with their primary images
            # First try to get featured destinations
            popular_destinations = list(Destination.objects.filter(
                is_active=True,
                is_featured=True
            ).prefetch_related(
                models.Prefetch(
                    'images',
                    queryset=DestinationImage.objects.filter(is_primary=True),
                    to_attr='primary_image'
                )
            ).order_by('-views', '-created_at')[:6])
            
            print(f"Found {len(popular_destinations)} featured destinations")
            
            # If no featured destinations, get any active destinations
            if not popular_destinations:
                popular_destinations = list(Destination.objects.filter(
                    is_active=True
                ).prefetch_related(
                    models.Prefetch(
                        'images',
                        queryset=DestinationImage.objects.filter(is_primary=True),
                        to_attr='primary_image'
                    )
                ).order_by('?')[:6])  # Random order if no views
                print(f"Found {len(popular_destinations)} active destinations (fallback)")
            
            # Get featured tours (limit to 6) with at least one image
            featured_tours = []
            tours = Tour.objects.filter(
                is_featured=True,
                is_active=True
            ).prefetch_related('images', 'category')
            
            for tour in tours[:12]:  # Get up to 12 to ensure we have enough with images
                if hasattr(tour, 'images') and tour.images.exists():
                    featured_tours.append(tour)
                    if len(featured_tours) >= 6:  # Limit to 6 tours with images
                        break
            
            # Get all active tour categories for filtering
            tour_categories = list(TourCategory.objects.filter(is_active=True))
            
            context['featured_destinations'] = featured_destinations
            context['popular_destinations'] = popular_destinations
            context['featured_tours'] = featured_tours
            context['tour_categories'] = tour_categories
            
        except Exception as e:
            # Log the error but don't crash the page
            print(f"Error fetching featured content: {e}")
            # Provide empty lists as fallback
            context.update({
                'featured_destinations': [],
                'featured_tours': [],
                'tour_categories': [],
            })
        
        return context


class AboutView(TemplateView):
    """View for the about page."""
    template_name = 'about.html'


class ContactView(TemplateView):
    """View for the contact page."""
    template_name = 'contact.html'


class TermsView(TemplateView):
    """View for the Terms of Service page.
    
    This view renders the terms of service page which is required for OAuth providers.
    """
    template_name = 'core/terms.html'
