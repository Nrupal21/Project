"""
Custom template filters for destination-related functionality.

This module provides custom template filters that can be used in Django templates
to perform destination-specific operations that aren't available in the default
template language.
"""

from django import template

register = template.Library()

@register.filter
def has_primary_image(images):
    """
    Check if any image in the given queryset is marked as primary.
    
    Args:
        images: A queryset of PendingDestinationImage objects
        
    Returns:
        bool: True if any image is marked as primary, False otherwise
    """
    return images.filter(is_primary=True).exists()
