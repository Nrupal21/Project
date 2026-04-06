"""
Template filters for the accounts app.

This module contains custom template filters used in account templates,
particularly for handling special data formats and display logic.
"""

from django import template
from django.forms import CheckboxInput, RadioSelect
from django.template import Node, TemplateSyntaxError
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    """
    Add CSS class(es) to a form field.
    
    This filter allows you to add one or more CSS classes to a form field.
    It handles various form field types including text inputs, checkboxes, and radio buttons.
    
    Args:
        field: The form field to add classes to
        css_class: A string of space-separated CSS classes to add
        
    Returns:
        The field with the added CSS class(es)
    """
    if not field:
        return ''
        
    # If the field is already a SafeString (from |safe filter), return as is
    if hasattr(field, '__html__'):
        return field
        
    # Make sure it's a form field
    if not hasattr(field, 'field'):
        return field
        
    try:
        # Handle different field types
        if isinstance(field.field.widget, CheckboxInput):
            # For checkboxes, we need to handle the input and label separately
            return field.as_widget(attrs={'class': f'{css_class} form-checkbox h-4 w-4 text-indigo-600 transition duration-150 ease-in-out'})
        elif isinstance(field.field.widget, RadioSelect):
            # For radio selects, we need to handle each option
            return field
        else:
            # For regular inputs, just add the class
            return field.as_widget(attrs={'class': f'form-input {css_class}'})
    except AttributeError:
        # If something goes wrong, return the field as is
        return field

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Template filter to access dictionary values by key.
    
    This is particularly useful when the key is a variable or
    when dealing with status counts in the guide application admin view.
    
    Args:
        dictionary: The dictionary to access
        key: The key to look up
        
    Returns:
        The value associated with the key, or None if the key doesn't exist
    """
    return dictionary.get(key, None)
