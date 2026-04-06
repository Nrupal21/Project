"""
Custom template filters for the reviews app.

This module contains custom template filters that can be used in Django templates.
To use these filters in a template, add {% load review_filters %} at the top of the template.
"""

from django import template

# Create a template library instance
register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Custom template filter to safely access dictionary items by key.
    
    This filter allows template access to dictionary values using a variable as the key.
    It handles cases where the key might not exist in the dictionary.
    
    Args:
        dictionary (dict): The dictionary to access
        key (str): The key to look up in the dictionary
        
    Returns:
        The value associated with the key if it exists, otherwise 0
        
    Usage in template:
        {% load review_filters %}
        {{ rating_breakdown|get_item:'5' }}
    """
    if not isinstance(dictionary, dict):
        return 0
    # Return 0 as default for rating counts if key doesn't exist
    return dictionary.get(key, 0)


@register.filter(name='multiply')
def multiply(value, arg):
    """
    Custom template filter to multiply a value by an argument.
    
    Args:
        value (int/float): The value to multiply
        arg (int/float): The multiplier
        
    Returns:
        The result of value * arg, or 0 if either value is not a number
        
    Usage in template:
        {{ value|multiply:arg }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter(name='divide')
def divide(value, arg):
    """
    Custom template filter to divide a value by an argument.
    Returns 0 if dividing by zero or if values are not numbers.
    
    Args:
        value (int/float): The numerator
        arg (int/float): The denominator
        
    Returns:
        The result of value / arg, or 0 if invalid operation
        
    Usage in template:
        {{ value|divide:arg }}
    """
    try:
        return float(value) / float(arg) if float(arg) != 0 else 0
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
