"""
Custom template tags for URL manipulation in customer app.
Provides functionality to remove specific query parameters from URLs.
"""
from django import template
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

register = template.Library()


@register.filter
def remove_param(url, param):
    """
    Remove a specific query parameter from a URL.
    
    Args:
        url (str): The URL to modify
        param (str): The parameter name to remove
        
    Returns:
        str: URL with the specified parameter removed
        
    Example:
        {{ request.GET.urlencode|remove_param:'cuisine' }}
    """
    if not url or not param:
        return url
    
    # Parse the URL and query string
    parsed = urlparse('?' + url)
    query_dict = parse_qs(parsed.query)
    
    # Remove the specified parameter
    query_dict.pop(param, None)
    
    # Rebuild the query string
    new_query = urlencode(query_dict, doseq=True)
    
    return new_query


@register.filter
def build_url_with_params(base_url, **kwargs):
    """
    Build a URL with specific query parameters.
    
    Args:
        base_url (str): The base URL
        **kwargs: Query parameters to add
        
    Returns:
        str: Complete URL with query parameters
    """
    if not base_url:
        return ''
    
    # Parse existing URL
    parsed = urlparse(base_url)
    query_dict = parse_qs(parsed.query)
    
    # Update with new parameters
    for key, value in kwargs.items():
        if value is not None and value != '':
            query_dict[key] = [value]
        else:
            query_dict.pop(key, None)
    
    # Rebuild URL
    new_query = urlencode(query_dict, doseq=True)
    new_parsed = parsed._replace(query=new_query)
    
    return urlunparse(new_parsed)


@register.simple_tag
def current_url_without_param(request, param_to_remove):
    """
    Get the current URL without a specific parameter.
    
    Args:
        request: Django request object
        param_to_remove (str): Parameter to remove from URL
        
    Returns:
        str: Current URL without the specified parameter
    """
    query_dict = request.GET.copy()
    query_dict.pop(param_to_remove, None)
    
    if query_dict:
        return f"{request.path}?{query_dict.urlencode()}"
    else:
        return request.path


@register.simple_tag
def filter_badge_url(request, filter_type, filter_value):
    """
    Generate URL for removing a specific filter badge.
    
    Args:
        request: Django request object
        filter_type (str): Type of filter (cuisine, price_range, etc.)
        filter_value (str): Current filter value
        
    Returns:
        str: URL for removing the specific filter
    """
    query_dict = request.GET.copy()
    
    # Remove the specific filter
    if filter_type in query_dict and query_dict[filter_type] == filter_value:
        query_dict.pop(filter_type, None)
    
    # Build the URL
    if query_dict:
        return f"{request.path}?{query_dict.urlencode()}"
    else:
        return request.path


@register.filter
def has_filters(request):
    """
    Check if the current request has any active filters.
    
    Args:
        request: Django request object
        
    Returns:
        bool: True if any filters are active
    """
    filter_params = ['search', 'cuisine', 'price_range', 'delivery_fee', 'rating', 'sort']
    return any(param in request.GET for param in filter_params if request.GET.get(param))


@register.filter
def active_filter_count(request):
    """
    Count the number of active filters (excluding sort).
    
    Args:
        request: Django request object
        
    Returns:
        int: Number of active filters
    """
    filter_params = ['search', 'cuisine', 'price_range', 'delivery_fee', 'rating']
    return sum(1 for param in filter_params if request.GET.get(param))
