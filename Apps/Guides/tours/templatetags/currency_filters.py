"""
Template filters for currency formatting.
"""
from django import template
from tours.utils import format_currency

register = template.Library()

@register.filter(name='currency')
def currency(value):
    """
    Format a number as Indian Rupees (INR) in templates.
    
    Usage in templates:
        {{ price|currency }}
    
    Args:
        value (Decimal, int, float): The amount to format
        
    Returns:
        str: Formatted currency string with Indian Rupee symbol
    """
    return format_currency(value)
