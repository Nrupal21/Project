"""
Custom template filters for restaurant app
Provides additional functionality for Django templates
"""

from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """
    Multiply two values together
    Usage: {{ value|mul:arg }}
    
    Args:
        value: First numeric value
        arg: Second numeric value to multiply by
    
    Returns:
        float: Result of multiplication, or empty string if conversion fails
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def div(value, arg):
    """
    Divide two values
    Usage: {{ value|div:arg }}
    
    Args:
        value: First numeric value (dividend)
        arg: Second numeric value (divisor)
    
    Returns:
        float: Result of division, or empty string if conversion fails or division by zero
    """
    try:
        if float(arg) == 0:
            return ''
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def add_class(value, css_class):
    """
    Add CSS class to form field
    Usage: {{ field|add_class:"form-control" }}
    
    Args:
        value: Django form field
        css_class: CSS class string to add
    
    Returns:
        Field with added CSS class
    """
    if hasattr(value, 'as_widget'):
        return value.as_widget(attrs={'class': css_class})
    return value

@register.filter
def truncate_chars(value, arg):
    """
    Truncate string after specified number of characters
    Usage: {{ text|truncate_chars:50 }}
    
    Args:
        value: String to truncate
        arg: Maximum number of characters
    
    Returns:
        str: Truncated string with ellipsis if needed
    """
    try:
        length = int(arg)
        if len(value) <= length:
            return value
        return value[:length] + '...'
    except (ValueError, TypeError):
        return value

@register.filter
def format_currency(value):
    """
    Format number as Indian currency
    Usage: {{ amount|format_currency }}
    
    Args:
        value: Numeric value to format
    
    Returns:
        str: Formatted currency string
    """
    try:
        return f"₹{float(value):.2f}"
    except (ValueError, TypeError):
        return "₹0.00"

@register.filter
def get_item(dictionary, key):
    """
    Get item from dictionary by key
    Usage: {{ my_dict|get_item:key }}
    
    Args:
        dictionary: Dictionary to get item from
        key: Key to look up
    
    Returns:
        Value from dictionary, or empty string if not found
    """
    try:
        return dictionary.get(key, '')
    except (AttributeError, TypeError):
        return ''

@register.filter
def percentage(value, total):
    """
    Calculate percentage of value relative to total
    Usage: {{ value|percentage:total }}
    
    Args:
        value: Part value
        total: Total value
    
    Returns:
        float: Percentage value, or 0 if total is 0
    """
    try:
        if float(total) == 0:
            return 0
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError):
        return 0

@register.simple_tag
def query_transform(request, **kwargs):
    """
    Transform query parameters for URL building
    Usage: {% query_transform request page=2 %}
    
    Args:
        request: Django request object
        **kwargs: Query parameters to update/add
    
    Returns:
        str: Updated query string
    """
    updated = request.GET.copy()
    for k, v in kwargs.items():
        if v is not None:
            updated[k] = v
        elif k in updated:
            del updated[k]
    return updated.urlencode()

@register.filter
def status_badge_class(status):
    """
    Return appropriate CSS class for order status badge
    Usage: {{ order.status|status_badge_class }}
    
    Args:
        status: Order status string
    
    Returns:
        str: CSS class for status badge
    """
    status_classes = {
        'pending': 'bg-yellow-100 text-yellow-800',
        'accepted': 'bg-blue-100 text-blue-800',
        'preparing': 'bg-purple-100 text-purple-800',
        'ready': 'bg-green-100 text-green-800',
        'delivered': 'bg-gray-100 text-gray-800',
        'cancelled': 'bg-red-100 text-red-800',
    }
    return status_classes.get(status.lower(), 'bg-gray-100 text-gray-800')

@register.filter
def order_type_badge_class(order_type):
    """
    Return appropriate CSS class for order type badge
    Usage: {{ order.order_type|order_type_badge_class }}
    
    Args:
        order_type: Order type string
    
    Returns:
        str: CSS class for order type badge
    """
    type_classes = {
        'qr_code': 'bg-purple-100 text-purple-800',
        'dine_in': 'bg-blue-100 text-blue-800',
        'delivery': 'bg-green-100 text-green-800',
        'takeaway': 'bg-yellow-100 text-yellow-800',
        'staff': 'bg-indigo-100 text-indigo-800',
    }
    return type_classes.get(order_type.lower(), 'bg-gray-100 text-gray-800')
