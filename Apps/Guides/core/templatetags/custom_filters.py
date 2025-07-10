"""
Custom template filters for the core app.
"""
from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument."""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def get_discount_percentage(price, discount_price):
    """Calculate the discount percentage."""
    if not discount_price or not price:
        return 0
    try:
        percentage = ((float(price) - float(discount_price)) / float(price)) * 100
        return round(percentage)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
