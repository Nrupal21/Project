"""
Decorators for role-based access control in function-based views.

This module provides decorators that can be used with Django function-based views
to enforce role-based access control.
"""
from functools import wraps
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from .models import CustomUser

def role_required(*roles, redirect_url=None):
    """
    Decorator to check if the user has one of the required roles.
    
    Args:
        *roles: One or more role values from CustomUser.UserRole
        redirect_url: Optional URL to redirect to if permission is denied
        
    Returns:
        function: Decorated view function
        
    Example:
        @role_required(CustomUser.UserRole.ADMIN, CustomUser.UserRole.MODERATOR)
        def admin_view(request):
            # View code here
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if redirect_url:
                    from django.shortcuts import redirect
                    return redirect(redirect_url)
                raise PermissionDenied("Authentication required")
                
            if not hasattr(request.user, 'role') or request.user.role not in roles:
                if redirect_url:
                    from django.shortcuts import redirect
                    return redirect(redirect_url)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse(
                        {'error': 'You do not have permission to perform this action.'}, 
                        status=403
                    )
                raise PermissionDenied("You do not have permission to access this page.")
                
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def admin_required(redirect_url=None):
    """Decorator to check if the user is an admin."""
    from .models import CustomUser
    return role_required(CustomUser.UserRole.ADMIN, redirect_url=redirect_url)

def local_guide_required(redirect_url=None):
    """Decorator to check if the user is a local guide."""
    from .models import CustomUser
    return role_required(CustomUser.UserRole.LOCAL_GUIDE, redirect_url=redirect_url)

def hotel_owner_required(redirect_url=None):
    """Decorator to check if the user is a hotel owner."""
    from .models import CustomUser
    return role_required(CustomUser.UserRole.HOTEL_OWNER, redirect_url=redirect_url)
