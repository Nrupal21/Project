"""
Custom template filters for the core app.

This module provides custom template filters that can be used in Django templates.
"""

from django import template
from django.utils.http import urlencode
from urllib.parse import urlparse, parse_qs, urlunparse

register = template.Library()


@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Custom template filter to retrieve a value from a dictionary using a variable key.
    
    Django templates don't support dictionary access with variable keys by default.
    This filter allows for variable key lookups in dictionaries within templates.
    
    Usage in templates:
        {{ my_dict|get_item:my_key }}
    
    Args:
        dictionary (dict): The dictionary to access
        key (str): The key to look up in the dictionary
        
    Returns:
        The value associated with the key in the dictionary,
        or None if the key doesn't exist or the object is not a dictionary
    """
    if not dictionary or not isinstance(dictionary, dict):
        return None
        
    return dictionary.get(key, None)


@register.filter(name='ad_format_class')
def ad_format_class(ad_format):
    """
    Convert ad format specification into appropriate CSS classes.
    
    This helps in styling different ad formats consistently across the site.
    
    Args:
        ad_format (str): The format specification for the ad
        
    Returns:
        str: CSS class string appropriate for the specified ad format
    """
    format_classes = {
        'auto': 'adsense-auto',
        'horizontal': 'adsense-horizontal',
        'vertical': 'adsense-vertical',
        'rectangle': 'adsense-rectangle',
        'responsive': 'adsense-responsive',
    }
    
    return format_classes.get(ad_format, 'adsense-auto')


@register.simple_tag(takes_context=True)
def update_query_params(context, **kwargs):
    """
    Updates the current URL's query parameters with the provided values.
    
    This tag allows modifying URL query parameters without affecting other parameters.
    If a parameter value is None, that parameter will be removed from the URL.
    
    Usage in template:
    <a href="?{% update_query_params page=1 %}">First page</a>
    <a href="?{% update_query_params filter_name=None %}">Remove filter</a>
    
    Args:
        context: The template context (automatically passed by Django)
        **kwargs: Key-value pairs of parameters to update
        
    Returns:
        str: The updated query string
    """
    request = context.get('request')
    if not request:
        return ''
        
    # Get the current GET parameters
    params = request.GET.copy()
    
    # Update with new parameters
    for key, value in kwargs.items():
        if value is None and key in params:
            del params[key]
        elif value is not None:
            params[key] = value
    
    # Return the updated query string
    return params.urlencode()
