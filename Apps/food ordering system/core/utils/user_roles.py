"""
User role utilities for restaurant owner identification and management.

This module provides helper functions to identify user roles throughout the system,
making it easy to check if a user is a restaurant owner, customer, or staff member.
"""

from django.apps import apps


def is_restaurant_owner(user):
    """
    Check if a user is a restaurant owner.
    
    This function checks both the role field and group membership for maximum
    compatibility. The role field is checked first for efficiency.
    
    Args:
        user (User): Django User instance
        
    Returns:
        bool: True if user is a restaurant owner, False otherwise
        
    Example:
        >>> user = User.objects.get(username='pizzapalace')
        >>> if is_restaurant_owner(user):
        ...     print("User is a restaurant owner")
    """
    if not user or not user.is_authenticated:
        return False
    
    # Check role field first (more efficient)
    try:
        if hasattr(user, 'profile') and user.profile.role == 'restaurant_owner':
            return True
    except Exception:
        pass
    
    # Fallback to group-based check for backward compatibility
    return user.groups.filter(name='Restaurant Owner').exists()


def is_active_restaurant_owner(user):
    """
    Check if a user is an active restaurant owner with approved restaurants.
    
    This function checks both group membership and if the user has at least
    one approved restaurant.
    
    Args:
        user (User): Django User instance
        
    Returns:
        bool: True if user is an active restaurant owner, False otherwise
        
    Example:
        >>> if is_active_restaurant_owner(user):
        ...     # Show restaurant owner dashboard
        ... else:
        ...     # Show pending approval message
    """
    if not is_restaurant_owner(user):
        return False
    
    # Lazy import to avoid AppRegistryNotReady error
    Restaurant = apps.get_model('restaurant', 'Restaurant')
    
    return Restaurant.objects.filter(
        owner=user,
        approval_status='approved',
        is_active=True
    ).exists()


def get_user_role(user):
    """
    Get the primary role of a user.
    
    Returns the most important role for the user, with priority:
    1. Superuser
    2. Staff
    3. Active Restaurant Owner
    4. Restaurant Owner (pending)
    5. Customer
    
    This function now checks the role field first for efficiency, then falls back
    to group-based checks for backward compatibility.
    
    Args:
        user (User): Django User instance
        
    Returns:
        str: Primary role of the user
        
    Example:
        >>> role = get_user_role(user)
        >>> print(f"User role: {role}")
    """
    if not user or not user.is_authenticated:
        return 'Anonymous'
    
    if user.is_superuser:
        return 'Superuser'
    
    if user.is_staff:
        return 'Staff'
    
    # Check role field first (more efficient)
    try:
        if hasattr(user, 'profile'):
            if user.profile.role == 'restaurant_owner':
                if is_active_restaurant_owner(user):
                    return 'Restaurant Owner'
                else:
                    return 'Pending Restaurant Owner'
            elif user.profile.role == 'manager':
                return 'Manager'
            elif user.profile.role == 'admin':
                return 'Administrator'
    except Exception:
        pass
    
    # Fallback to group-based checks for backward compatibility
    if is_active_restaurant_owner(user):
        return 'Restaurant Owner'
    
    if is_restaurant_owner(user):
        return 'Pending Restaurant Owner'
    
    return 'Customer'


def set_user_role(user, role):
    """
    Set a user's role and synchronize with group membership.
    
    This function updates the user's role field and ensures appropriate
    group membership for backward compatibility.
    
    Args:
        user (User): Django User instance
        role (str): Role to set ('customer', 'restaurant_owner', 'manager', 'admin')
        
    Returns:
        bool: True if role was set successfully
        
    Example:
        >>> success = set_user_role(user, 'restaurant_owner')
        >>> if success:
        ...     print("Role updated successfully")
    """
    if not user or not user.is_authenticated:
        return False
    
    try:
        from django.contrib.auth.models import Group
        from django.db import transaction
        
        with transaction.atomic():
            # Update role field
            if hasattr(user, 'profile'):
                user.profile.role = role
                user.profile.save(update_fields=['role'])
            
            # Sync groups based on role
            restaurant_group, _ = Group.objects.get_or_create(name='Restaurant Owner')
            manager_group, _ = Group.objects.get_or_create(name='Manager')
            
            # Remove from all role-specific groups first
            user.groups.remove(restaurant_group, manager_group)
            
            # Add to appropriate groups
            if role == 'restaurant_owner':
                user.groups.add(restaurant_group)
            elif role == 'manager':
                user.groups.add(restaurant_group, manager_group)
            elif role == 'admin':
                user.is_staff = True
                user.is_superuser = True
                user.save(update_fields=['is_staff', 'is_superuser'])
            else:  # customer
                user.is_staff = False
                user.is_superuser = False
                user.save(update_fields=['is_staff', 'is_superuser'])
            
            return True
    except Exception:
        return False


def get_user_restaurants(user):
    """
    Get all restaurants owned by a user.
    
    Args:
        user (User): Django User instance
        
    Returns:
        QuerySet: Restaurants owned by the user
        
    Example:
        >>> restaurants = get_user_restaurants(user)
        >>> for restaurant in restaurants:
        ...     print(restaurant.name)
    """
    if not is_restaurant_owner(user):
        # Lazy import to avoid AppRegistryNotReady error
        Restaurant = apps.get_model('restaurant', 'Restaurant')
        return Restaurant.objects.none()
    
    # Lazy import to avoid AppRegistryNotReady error
    Restaurant = apps.get_model('restaurant', 'Restaurant')
    return Restaurant.objects.filter(owner=user)


def get_pending_restaurant_application(user):
    """
    Get pending restaurant application for a user.
    
    Args:
        user (User): Django User instance
        
    Returns:
        PendingRestaurant: Pending application or None
        
    Example:
        >>> pending = get_pending_restaurant_application(user)
        >>> if pending:
        ...     print(f"Application for {pending.restaurant_name}")
    """
    try:
        # Lazy import to avoid AppRegistryNotReady error
        PendingRestaurant = apps.get_model('restaurant', 'PendingRestaurant')
        return PendingRestaurant.objects.filter(
            user=user,
            status='pending'
        ).first()
    except Exception:
        return None


def can_access_restaurant_dashboard(user):
    """
    Check if user can access restaurant dashboard.
    
    Users can access restaurant dashboard if they are:
    - Active restaurant owners (with approved restaurants)
    - Staff members
    - Superusers
    
    Args:
        user (User): Django User instance
        
    Returns:
        bool: True if user can access restaurant dashboard
        
    Example:
        >>> if can_access_restaurant_dashboard(user):
        ...     return redirect('restaurant:dashboard')
        >>> else:
        ...     return redirect('customer:home')
    """
    if not user or not user.is_authenticated:
        return False
    
    return (is_active_restaurant_owner(user) or 
            user.is_staff or 
            user.is_superuser)


def get_restaurant_owners():
    """
    Get all restaurant owners (including pending).
    
    Returns:
        QuerySet: Users who are restaurant owners
        
    Example:
        >>> owners = get_restaurant_owners()
        >>> print(f"Total restaurant owners: {owners.count()}")
    """
    # Lazy import to avoid AppRegistryNotReady error
    User = apps.get_model('auth', 'User')
    return User.objects.filter(groups__name='Restaurant Owner')


def get_active_restaurant_owners():
    """
    Get all active restaurant owners (with approved restaurants).
    
    Returns:
        QuerySet: Users who are active restaurant owners
        
    Example:
        >>> active_owners = get_active_restaurant_owners()
        >>> for owner in active_owners:
        ...     print(f"{owner.username} - {owner.get_user_restaurants().count()} restaurants")
    """
    # Lazy import to avoid AppRegistryNotReady error
    User = apps.get_model('auth', 'User')
    return User.objects.filter(
        groups__name='Restaurant Owner',
        restaurants__approval_status='approved',
        restaurants__is_active=True
    ).distinct()


def sync_restaurant_owner_groups():
    """
    Synchronize restaurant owner groups with actual restaurant ownership.
    
    This function ensures that:
    - Users with approved restaurants are in Restaurant Owner group
    - Users without restaurants are removed from Restaurant Owner group
    
    Returns:
        dict: Statistics about the sync operation
        
    Example:
        >>> stats = sync_restaurant_owner_groups()
        >>> print(f"Added {stats['added']} users, removed {stats['removed']} users")
    """
    from django.db import transaction
    
    # Lazy imports to avoid AppRegistryNotReady error
    User = apps.get_model('auth', 'User')
    Group = apps.get_model('auth', 'Group')
    
    with transaction.atomic():
        group, created = Group.objects.get_or_create(name='Restaurant Owner')
        
        # Users who should be in the group (have restaurants)
        users_with_restaurants = User.objects.filter(
            restaurants__isnull=False
        ).distinct()
        
        # Users currently in the group
        users_in_group = set(group.user_set.all())
        
        # Users who should be in the group
        should_be_in_group = set(users_with_restaurants)
        
        # Add missing users
        to_add = should_be_in_group - users_in_group
        for user in to_add:
            group.user_set.add(user)
        
        # Remove users without restaurants
        to_remove = users_in_group - should_be_in_group
        for user in to_remove:
            group.user_set.remove(user)
        
        return {
            'group_created': created,
            'added': len(to_add),
            'removed': len(to_remove),
            'total_restaurant_owners': len(should_be_in_group)
        }


def get_user_statistics():
    """
    Get comprehensive user statistics.
    
    Returns:
        dict: User statistics by role
        
    Example:
        >>> stats = get_user_statistics()
        >>> print(f"Total users: {stats['total_users']}")
        >>> print(f"Restaurant owners: {stats['restaurant_owners']}")
    """
    # Lazy imports to avoid AppRegistryNotReady error
    User = apps.get_model('auth', 'User')
    Restaurant = apps.get_model('restaurant', 'Restaurant')
    
    return {
        'total_users': User.objects.count(),
        'restaurant_owners': get_restaurant_owners().count(),
        'active_restaurant_owners': get_active_restaurant_owners().count(),
        'pending_restaurant_owners': get_restaurant_owners().count() - get_active_restaurant_owners().count(),
        'staff_users': User.objects.filter(is_staff=True).count(),
        'superusers': User.objects.filter(is_superuser=True).count(),
        'customers': User.objects.filter(
            groups__name__in=['Restaurant Owner'],
            is_staff=False,
            is_superuser=False
        ).count(),
        'total_restaurants': Restaurant.objects.count(),
        'approved_restaurants': Restaurant.objects.filter(approval_status='approved').count(),
        'pending_restaurants': Restaurant.objects.filter(approval_status='pending').count(),
    }


# Note: User model monkey-patching removed to avoid circular import issues
# Use utility functions directly instead:
# from core.utils.user_roles import is_restaurant_owner, get_user_role, etc.
# Example: is_restaurant_owner(user) instead of user.is_restaurant_owner()
