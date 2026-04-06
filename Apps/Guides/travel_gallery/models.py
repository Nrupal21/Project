"""
Models for the travel_gallery app.

This module defines database models for managing travel gallery images.
Each model includes comprehensive documentation and follows Django best practices.
"""

from django.db import models
from django.urls import reverse
from django.utils import timezone


class GalleryImageManager(models.Manager):
    """
    Custom manager for GalleryImage model that filters active images by default.
    
    This ensures that only active images are returned in queries unless explicitly overridden.
    """
    def get_queryset(self):
        """
        Return a QuerySet of all active gallery images.
        
        Returns:
            QuerySet: A queryset containing only active gallery images
        """
        return super().get_queryset().filter(is_active=True)

class GalleryImage(models.Model):
    """
    Represents an image in the travel gallery.
    
    This model stores images for the travel gallery section, allowing for a
    dynamic display of beautiful travel destinations and experiences.
    Each image can be associated with location data and categorized for better organization.
    """
    # Custom manager that filters active images by default
    objects = GalleryImageManager()
    
    # Manager that includes all images, including inactive ones
    all_objects = models.Manager()
    title = models.CharField(
        max_length=200,
        help_text="Title of the gallery image"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of what the image shows or the location depicted"
    )
    image_url = models.URLField(
        help_text="URL to the image (external hosting or CDN)"
    )
    location = models.CharField(
        max_length=200,
        help_text="Location shown in the image (e.g., 'Bali, Indonesia')"
    )
    coordinates = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional GPS coordinates for the location (e.g., '8.3405, 115.0920')"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Whether this image should be featured prominently in the gallery"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this image is active and should be displayed on the site"
    )
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Order in which this image should appear in the gallery (lower numbers first)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when this image was added to the gallery"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when this image was last updated"
    )
    
    class Meta:
        """
        Model metadata options.
        
        This class defines metadata for the GalleryImage model, including the app_label
        which explicitly tells Django which app this model belongs to, verbose names for
        admin interface, ordering for querysets, and database indexes for performance.
        """
        app_label = 'travel_gallery'  # Explicitly set app_label to ensure Django recognizes this model
        verbose_name = 'Gallery Image'
        verbose_name_plural = 'Gallery Images'
        ordering = ['display_order', '-created_at']  # Order by display_order first, then by creation date
        indexes = [
            models.Index(fields=['is_featured']),  # Index for faster filtering of featured images
            models.Index(fields=['display_order']),  # Index for faster ordering by display_order
        ]
    
    def __str__(self):
        """
        Returns a string representation of this gallery image.
        
        Returns:
            str: The title and location of the image
        """
        return f"{self.title} - {self.location}"
        
    def get_absolute_url(self):
        """
        Return the URL for this gallery image's detail view.
        
        Returns:
            str: URL for the detail view of this image
        """
        return reverse('travel_gallery:detail', kwargs={'pk': self.pk})
