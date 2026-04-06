from django import template
from django.utils.http import urlencode
from urllib.parse import urlparse, parse_qs, urlunparse

register = template.Library()

@register.simple_tag(takes_context=True)
def remove_param(context, param_name, *args, **kwargs):
    """
    Removes a parameter from the current URL's query string.
    
    Usage in template:
    <a href="?{% remove_param 'param_name' %}">Remove filter</a>
    
    Args:
        context: The template context
        param_name: The name of the parameter to remove
        
    Returns:
        str: The modified query string with the parameter removed
    """
    request = context.get('request')
    if not request:
        return ''
        
    # Get the current GET parameters
    params = request.GET.copy()
    
    # Remove the specified parameter
    if param_name in params:
        del params[param_name]
    
    # Return the updated query string
    query_string = params.urlencode()
    return query_string if query_string else ''

@register.simple_tag(takes_context=True)
def update_query_params(context, **kwargs):
    """
    Updates the current URL's query parameters with the provided values.
    
    Usage in template:
    <a href="?{% update_query_params page=1 %}">First page</a>
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
