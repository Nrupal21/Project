from django import template
from django.forms import widgets

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    """
    Template filter that adds a CSS class to a form field.
    
    Args:
        field: The form field to modify
        css_class: The CSS class string to add to the field
        
    Returns:
        The modified form field with the additional CSS class
        
    Note:
        Handles both form field objects and string values by returning
        the original value if it's not a form field.
    """
    if field is None:
        return ''
        
    if hasattr(field, 'as_widget'):
        return field.as_widget(attrs={"class": css_class})
    
    # If it's a string or doesn't have as_widget, wrap it in a widget
    if isinstance(field, str):
        return f'<span class="{css_class}">{field}</span>'
        
    # For any other case, try to convert to string and wrap
    return f'<span class="{css_class}">{str(field)}</span>'
