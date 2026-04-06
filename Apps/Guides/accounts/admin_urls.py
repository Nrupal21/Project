"""
URL patterns for admin-specific account management views.

This module defines URL patterns for administrative user management,
including role assignment, permission management, and user activity monitoring.
These URLs are included in the main accounts URLconf and protected by
the AdminRequiredMixin to ensure only authorized users can access them.
"""

from django.urls import path
from . import admin_views

# URL patterns for admin user management
urlpatterns = [
    # User role management URLs
    path(
        'users/roles/',
        admin_views.UserRoleListView.as_view(),
        name='admin_user_roles'
    ),
    
    # Edit individual user role
    path(
        'users/<int:pk>/role/',
        admin_views.UserRoleUpdateView.as_view(),
        name='admin_user_role_update'
    ),
    
    # Bulk role update
    path(
        'users/roles/bulk-update/',
        admin_views.BulkRoleUpdateView.as_view(),
        name='admin_bulk_role_update'
    ),
    
    # User permission details
    path(
        'users/<int:pk>/permissions/',
        admin_views.UserPermissionDetailView.as_view(),
        name='admin_user_permissions'
    ),
]
