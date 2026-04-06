"""
Admin configuration for the travel_gallery app.

This module registers models with the Django admin site and configures
their appearance and functionality in the admin interface.
"""

from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import GalleryImage

@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    """
    Admin configuration for GalleryImage model.
    
    Provides a rich interface for managing gallery images with preview functionality,
    filtering, sorting options, and organized fieldsets.
    """
    list_display = ('title', 'location', 'image_preview', 'is_featured', 'display_order', 'created_at')
    list_filter = ('is_featured', 'created_at')
    search_fields = ('title', 'description', 'location')
    readonly_fields = ('created_at', 'updated_at', 'image_preview')
    list_editable = ('is_featured', 'display_order')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Image Information', {
            'fields': ('title', 'description', 'image_url', 'image_preview')
        }),
        ('Location Details', {
            'fields': ('location', 'coordinates')
        }),
        ('Display Options', {
            'fields': ('is_featured', 'display_order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def image_preview(self, obj):
        """
        Generates an HTML image preview for the admin interface.
        
        Args:
            obj: The GalleryImage instance
            
        Returns:
            str: HTML for displaying a thumbnail preview of the image
        """
        if obj.image_url:
            return mark_safe(f'<img src="{obj.image_url}" width="100" height="75" style="object-fit: cover;" />')
        return 'No Image'
    
    image_preview.short_description = 'Preview'
