"""
Context processors for the core app.
Provides additional context data to templates across the entire application.
"""
from django.conf import settings


def session_timeout_context(request):
    """
    Add session timeout configuration to template context.
    
    This context processor provides session timeout settings to JavaScript
    for the session timeout manager functionality.
    
    Args:
        request: Django HTTP request object
        
    Returns:
        dict: Context data with session timeout settings
    """
    context = {}
    
    # Debug: Print authentication status
    print(f"DEBUG: User authenticated: {request.user.is_authenticated}")
    print(f"DEBUG: Username: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
    
    # Only add session info for authenticated users
    if request.user.is_authenticated:
        context.update({
            'session_timeout': getattr(settings, 'SESSION_INACTIVITY_TIMEOUT', 1200),
            'warning_time': getattr(settings, 'SESSION_WARNING_TIME', 120),
            'user_authenticated': True,
        })
        print(f"DEBUG: Context set with user_authenticated=True")
    else:
        context['user_authenticated'] = False
        print(f"DEBUG: Context set with user_authenticated=False")
    
    print(f"DEBUG: Final context: {context}")
    return context


def user_role_context(request):
    """
    Add user role information to template context.
    
    This context processor adds the following variables to all templates:
    - user_role: Primary role of the current user
    - is_restaurant_owner: Boolean indicating if user is a restaurant owner
    - is_active_restaurant_owner: Boolean indicating if user has approved restaurants
    - can_access_restaurant_dashboard: Boolean indicating dashboard access
    
    Usage in templates:
    {% if is_restaurant_owner %}
        <p>Welcome, Restaurant Owner!</p>
    {% endif %}
    
    {% if user_role == 'Restaurant Owner' %}
        <a href="{% url 'restaurant:dashboard' %}">Dashboard</a>
    {% endif %}
    """
    # Lazy imports to avoid AppRegistryNotReady error
    from .utils.user_roles import (
        get_user_role, 
        is_restaurant_owner, 
        is_active_restaurant_owner, 
        can_access_restaurant_dashboard
    )
    
    user = request.user
    
    if user.is_authenticated:
        return {
            'user_role': get_user_role(user),
            'is_restaurant_owner': is_restaurant_owner(user),
            'is_active_restaurant_owner': is_active_restaurant_owner(user),
            'can_access_restaurant_dashboard': can_access_restaurant_dashboard(user),
        }
    
    return {
        'user_role': 'Anonymous',
        'is_restaurant_owner': False,
        'is_active_restaurant_owner': False,
        'can_access_restaurant_dashboard': False,
    }


def site_info_context(request):
    """
    Add site information to template context.
    
    Provides common site data like name, domain, and URLs
    that are frequently used across templates.
    
    Args:
        request: Django HTTP request object
        
    Returns:
        dict: Context data with site information
    """
    return {
        'site_name': getattr(settings, 'SITE_NAME', 'Food Ordering System'),
        'site_domain': getattr(settings, 'SITE_DOMAIN', 'localhost'),
        'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
    }
