"""
Custom template filters for the tours app.

This module provides template filters that extend Django's built-in template
filtering capabilities, specifically for formatting and manipulating strings
in tour templates.
"""
from django import template
from django.utils.safestring import mark_safe
import re

# Register the template library
register = template.Library()

@register.filter
def split(value, delimiter=','):
    """
    Split a string into a list using the specified delimiter.
    
    This filter enables splitting a string in templates, which is useful
    for converting comma-separated lists into iterable items.
    
    Args:
        value (str): The input string to split
        delimiter (str, optional): The delimiter to split on. Defaults to ','.
        
    Returns:
        list: The split string as a list of items
        
    Example usage in templates:
        {% for item in tour.included_activities|split:"," %}
            <li>{{ item }}</li>
        {% endfor %}
    """
    if value is None:
        return []
    return [item for item in value.split(delimiter)]

@register.filter
def trim(value):
    """
    Remove leading and trailing whitespace from a string.
    
    This filter is useful for cleaning up individual items after splitting
    a comma-separated string where items might have extra whitespace.
    
    Args:
        value (str): The input string to trim
        
    Returns:
        str: The input string with leading and trailing whitespace removed
        
    Example usage in templates:
        {% for item in tour.included_activities|split:"," %}
            <li>{{ item|trim }}</li>
        {% endfor %}
    """
    if value is None:
        return ''
    return value.strip()

@register.filter(is_safe=True)
def stars(value):
    """
    Convert a numeric rating to a star display HTML.
    
    This filter generates HTML for displaying ratings as stars, supporting
    half stars for decimal values.
    
    Args:
        value (float): The rating value (typically between 0 and 5)
        
    Returns:
        str: HTML markup for displaying the star rating
        
    Example usage in templates:
        {{ tour.rating|stars }}
    """
    try:
        # Convert to float and ensure it's within 0-5 range
        value = float(value)
        value = max(0, min(5, value))
        
        # Calculate full, half and empty stars
        full_stars = int(value)
        half_star = False
        if value - full_stars >= 0.5:
            half_star = True
            
        empty_stars = 5 - full_stars - (1 if half_star else 0)
        
        # Generate HTML
        html = ''
        # Full stars
        html += '<i class="fas fa-star text-yellow-500"></i>' * full_stars
        # Half star if applicable
        if half_star:
            html += '<i class="fas fa-star-half-alt text-yellow-500"></i>'
        # Empty stars
        html += '<i class="far fa-star text-yellow-500"></i>' * empty_stars
        
        return mark_safe(html)
    except (ValueError, TypeError):
        # Return empty stars for invalid input
        return mark_safe('<i class="far fa-star text-yellow-500"></i>' * 5)

@register.filter
def currency(value, currency_symbol='$'):
    """
    Format a numeric value as currency.
    
    This filter formats numbers as currency values with the specified currency symbol,
    thousands separators, and two decimal places.
    
    Args:
        value (float/int): The numeric value to format
        currency_symbol (str, optional): The currency symbol to use. Defaults to '$'.
        
    Returns:
        str: Formatted currency string
        
    Example usage in templates:
        {{ tour.price|currency:"€" }}
    """
    try:
        value = float(value)
        formatted = f"{currency_symbol}{value:,.2f}"
        return formatted
    except (ValueError, TypeError):
        return f"{currency_symbol}0.00"

@register.filter
def shorten_text(value, length=100):
    """
    Shorten text to the specified length and add ellipsis if truncated.
    
    This filter is useful for creating excerpts or previews of longer text content.
    
    Args:
        value (str): The text to shorten
        length (int, optional): Maximum length before truncation. Defaults to 100.
        
    Returns:
        str: Shortened text with ellipsis if truncated
        
    Example usage in templates:
        {{ tour.description|shorten_text:150 }}
    """
    if not value:
        return ''
        
    if len(value) <= length:
        return value
    
    # Try to cut at the nearest space to avoid cutting words
    truncated = value[:length]
    last_space = truncated.rfind(' ')
    
    if last_space > length * 0.8:  # Only trim at space if it's not too far back
        truncated = truncated[:last_space]
        
    return truncated + '...'

@register.filter
def format_duration(days):
    """
    Format a duration in days to a human-readable string.
    
    This filter converts a number of days into a more readable format,
    especially useful for displaying tour durations.
    
    Args:
        days (int): Number of days
        
    Returns:
        str: Formatted duration string
        
    Example usage in templates:
        {{ tour.duration_days|format_duration }}
    """
    try:
        days = int(days)
        if days == 1:
            return "1 day"
        elif days < 7:
            return f"{days} days"
        elif days == 7:
            return "1 week"
        elif days % 7 == 0:
            weeks = days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''}"
        else:
            weeks = days // 7
            remaining_days = days % 7
            if weeks == 0:
                return f"{days} days"
            else:
                week_text = f"{weeks} week{'s' if weeks > 1 else ''}"
                day_text = f"{remaining_days} day{'s' if remaining_days > 1 else ''}"
                return f"{week_text}, {day_text}"
    except (ValueError, TypeError):
        return "N/A"
