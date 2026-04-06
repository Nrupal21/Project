"""
Custom template tags for working with content types in templates.

This module provides template tags that help with content type operations,
such as getting the content type ID for a model instance.
"""
from django import template
from django.contrib.contenttypes.models import ContentType

register = template.Library()

@register.simple_tag(takes_context=False)
def get_content_type_id(obj):
    """
    Get the content type ID for the given object.
    
    This template tag returns the content type ID for the given model instance.
    
    Args:
        obj: A model instance
        
    Returns:
        int: The content type ID for the object's model
    """
    if not obj:
        return ''
    content_type = ContentType.objects.get_for_model(obj)
    return content_type.id
