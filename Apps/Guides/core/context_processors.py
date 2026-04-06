"""
Context processors for the core app.

This module provides context processors that add variables to the template context.
"""

from django.conf import settings


def installed_apps(request):
    """
    Add INSTALLED_APPS to the template context.
    
    This allows templates to check if a specific app is installed.
    
    Args:
        request: The HTTP request object
        
    Returns:
        dict: Dictionary containing the list of installed apps
    """
    return {'INSTALLED_APPS': [app.split('.')[-1] for app in settings.INSTALLED_APPS]}


def adsense_settings(request):
    """
    Add Google AdSense configuration to the template context.
    
    Makes AdSense publisher ID and ad slots available to all templates.
    This enables displaying ads in various template locations without
    repeating configuration in each view.
    
    This context processor provides the following variables to templates:
    - ADSENSE_ENABLED: Boolean indicating if AdSense is enabled site-wide
    - GOOGLE_ADSENSE_PUBLISHER_ID: Your AdSense publisher ID (ca-pub-XXXXXXXXXX)
    - GOOGLE_ADSENSE_SLOTS: Dictionary containing ad slot IDs for different positions
      - GOOGLE_ADSENSE_SLOTS.header: Header ad position slot ID
      - GOOGLE_ADSENSE_SLOTS.sidebar: Sidebar ad position slot ID
      - GOOGLE_ADSENSE_SLOTS.footer: Footer ad position slot ID
      - GOOGLE_ADSENSE_SLOTS.in_article: In-article ad position slot ID
    
    Usage in templates:
    {% if ADSENSE_ENABLED %}
        <!-- AdSense code can be included here -->
    {% endif %}
    
    Args:
        request: The HTTP request object
        
    Returns:
        dict: Dictionary containing AdSense configuration settings
    """
    return {
        # Check if AdSense is globally enabled (default: False)
        'ADSENSE_ENABLED': getattr(settings, 'ADSENSE_ENABLED', False),
        
        # Get the publisher ID (default: empty string)
        'GOOGLE_ADSENSE_PUBLISHER_ID': getattr(settings, 'GOOGLE_ADSENSE_PUBLISHER_ID', ''),
        
        # Get the ad slot IDs dictionary (default: empty dict)
        'GOOGLE_ADSENSE_SLOTS': getattr(settings, 'GOOGLE_ADSENSE_SLOTS', {})
    }
