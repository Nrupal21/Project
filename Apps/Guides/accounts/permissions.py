"""
Custom permission classes for role-based access control.

This module contains permission classes that can be used with Django REST Framework
views to enforce role-based access control.
"""
from rest_framework import permissions
from .models import CustomUser

class IsAdminUser(permissions.BasePermission):
    """
    Permission class to check if the user has admin role.
    """
    message = 'Only administrators can perform this action.'
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)

class IsLocalGuide(permissions.BasePermission):
    """
    Permission class to check if the user has local_guide role.
    """
    message = 'Only local guides can perform this action.'
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_local_guide)

class IsHotelOwner(permissions.BasePermission):
    """
    Permission class to check if the user has hotel_owner role.
    """
    message = 'Only hotel owners can perform this action.'
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_hotel_owner)

def has_role(user, role):
    """
    Check if a user has a specific role.
    
    Args:
        user: The user instance to check
        role (str): The role to check for (must be one of UserRole values)
        
    Returns:
        bool: True if the user has the specified role, False otherwise
    """
    if not user or not user.is_authenticated:
        return False
    return user.role == role

def has_any_role(user, roles):
    """
    Check if a user has any of the specified roles.
    
    Args:
        user: The user instance to check
        roles (list): List of roles to check for
        
    Returns:
        bool: True if the user has any of the specified roles, False otherwise
    """
    if not user or not user.is_authenticated:
        return False
    return user.role in roles
