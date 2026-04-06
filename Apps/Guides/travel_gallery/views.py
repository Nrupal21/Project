"""
Views for the travel_gallery app.

This module defines view functions and classes for displaying gallery images.
Each view includes comprehensive documentation and follows Django best practices.
"""

from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from .models import GalleryImage

class GalleryImageListView(ListView):
    """
    Display a list of gallery images.
    
    This view shows all gallery images, with options for filtering and sorting.
    Featured images are shown first, followed by other images in display_order.
    
    Attributes:
        model: The model that this view displays objects of
        paginate_by: Number of images to show per page
        context_object_name: Variable name to use in template context
        template_name: The template used to render this view
    """
    model = GalleryImage
    paginate_by = 12  # Show 12 images per page
    context_object_name = 'images'
    template_name = 'travel_gallery/gallery_list.html'
    
    def get_queryset(self):
        """
        Return the list of items for this view.
        
        Retrieves and orders gallery images based on request parameters.
        By default, only active images are shown. Use show_all=1 to include inactive.
        
        Returns:
            QuerySet: Filtered and ordered gallery images
        """
        # Use all_objects manager if show_all=1 is in the query params
        show_all = self.request.GET.get('show_all') == '1'
        manager = GalleryImage.all_objects if show_all else GalleryImage.objects
        
        queryset = manager.all()
        
        # Apply filters based on request parameters
        location_filter = self.request.GET.get('location')
        if location_filter:
            queryset = queryset.filter(location__icontains=location_filter)
        
        # Apply ordering based on request parameters
        sort_by = self.request.GET.get('sort', 'featured')
        if sort_by == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort_by == 'oldest':
            queryset = queryset.order_by('created_at')
        elif sort_by == 'featured':  # Default ordering
            queryset = queryset.order_by('-is_featured', 'display_order', '-created_at')
            
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Get the context data for the template.
        
        Adds additional context data to pass to the template, including
        featured images and available locations for filtering.
        
        Args:
            **kwargs: Keyword arguments
            
        Returns:
            dict: Context dictionary for template rendering
        """
        context = super().get_context_data(**kwargs)
        
        # Determine which manager to use based on show_all parameter
        show_all = self.request.GET.get('show_all') == '1'
        manager = GalleryImage.all_objects if show_all else GalleryImage.objects
        
        # Get featured images (respecting the show_all filter)
        featured_qs = manager.filter(is_featured=True).order_by('display_order')[:6]
        
        # Get distinct locations from active images only
        locations = GalleryImage.objects.values_list('location', flat=True).distinct()
        
        # Add data to context
        context.update({
            'featured_images': featured_qs,
            'locations': locations,
            'current_sort': self.request.GET.get('sort', 'featured'),
            'current_location': self.request.GET.get('location', ''),
            'show_all': show_all
        })
        
        return context


class GalleryImageDetailView(DetailView):
    """
    Display details of a specific gallery image.
    
    This view shows all details of a gallery image, including full-size image and location.
    
    Attributes:
        model: The model that this view displays objects of
        context_object_name: Variable name to use in template context
        template_name: The template used to render this view
    """
    model = GalleryImage
    context_object_name = 'image'
    template_name = 'travel_gallery/gallery_detail.html'
    
    def get_queryset(self):
        """
        Return the queryset for this view.
        
        Uses the all_objects manager to allow viewing inactive images in detail view
        when accessed directly by URL, but still respects the is_active filter in listings.
        
        Returns:
            QuerySet: The queryset for this view
        """
        return GalleryImage.all_objects.all()
        
    def get_context_data(self, **kwargs):
        """
        Get the context data for the template.
        
        Adds additional context data to pass to the template, including
        related images from the same location.
        
        Args:
            **kwargs: Keyword arguments
            
        Returns:
            dict: Context dictionary for template rendering
        """
        context = super().get_context_data(**kwargs)
        
        # Get related images from the same location (only active ones)
        related_images = GalleryImage.objects.filter(
            location=self.object.location
        ).exclude(
            pk=self.object.pk
        ).order_by('?')[:4]  # Random 4 related images
        
        context.update({
            'related_images': related_images,
            'is_active': self.object.is_active  # Pass the active status to the template
        })
        return context


def gallery_grid_view(request):
    """
    Display a grid of gallery images suitable for the homepage.
    
    This view is used to show a responsive grid of featured travel gallery images
    for inclusion on the homepage or other sections of the site. By default, only
    active images are shown. Use show_all=1 in the query parameters to include
    inactive images.
    
    Args:
        request: The HTTP request object
        
    Returns:
        HttpResponse: Rendered template with gallery images or JSON response for AJAX
    """
    # Check if we should show all images (including inactive ones)
    show_all = request.GET.get('show_all') == '1'
    manager = GalleryImage.all_objects if show_all else GalleryImage.objects
    
    # Get featured images (respecting the show_all filter)
    images = manager.filter(is_featured=True).order_by('display_order')[:8]
    
    # For AJAX requests, return JSON data
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        image_data = [{
            'id': img.id,
            'title': img.title,
            'location': img.location,
            'image_url': img.image_url,
            'url': img.get_absolute_url(),
            'is_active': img.is_active if hasattr(img, 'is_active') else True
        } for img in images]
        return JsonResponse({
            'images': image_data,
            'show_all': show_all
        })
        
    # For regular requests, render template
    return render(request, 'travel_gallery/gallery_grid.html', {
        'images': images,
        'show_all': show_all
    })
