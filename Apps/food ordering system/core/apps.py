"""
Core app configuration for the food ordering system.

This AppConfig handles initialization tasks including:
- Creating default groups (Restaurant Owner)
- Setting up user role methods safely
- Initializing system components
"""
from django.apps import AppConfig
from django.db.models.signals import post_migrate


class CoreConfig(AppConfig):
    """Core app configuration with restaurant owner management."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core'
    
    def ready(self):
        """
        Called when the app is ready.
        
        This method connects signals to ensure the system is properly initialized.
        User role extensions are now available as standalone utility functions
        to avoid circular import issues.
        """
        # Connect post_migrate signal to create default groups
        post_migrate.connect(create_default_groups, sender=self)
    
    def extend_user_model(self):
        """
        Note: User model monkey-patching removed to avoid circular import issues.
        
        The user role utility functions are now available as standalone functions
        and can be imported directly when needed.
        
        Example usage in views or other code:
        ```python
        from core.utils.user_roles import (
            is_restaurant_owner, 
            get_user_role, 
            is_active_restaurant_owner,
            get_user_restaurants,
            can_access_restaurant_dashboard
        )
        
        # Usage: is_restaurant_owner(user) instead of user.is_restaurant_owner()
        ```
        """


def create_default_groups(sender, **kwargs):
    """
    Create default groups after migrations.
    
    This function creates the 'Restaurant Owner' group and assigns
    appropriate permissions to ensure the system works correctly.
    
    Args:
        sender: The app config that sent the signal
        **kwargs: Additional signal arguments
    """
    # Lazy imports to avoid AppRegistryNotReady error
    from django.apps import apps
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Restaurant = apps.get_model('restaurant', 'Restaurant')
    
    # Create Restaurant Owner group
    restaurant_owner_group, created = Group.objects.get_or_create(
        name='Restaurant Owner',
        defaults={'name': 'Restaurant Owner'}
    )
    
    if created:
        print("✅ Created 'Restaurant Owner' group")
        
        # Add permissions for restaurant management
        restaurant_content_type = ContentType.objects.get_for_model(Restaurant)
        
        # Get all permissions for Restaurant model
        restaurant_permissions = Permission.objects.filter(
            content_type=restaurant_content_type
        )
        
        # Add permissions to the group
        restaurant_owner_group.permissions.add(*restaurant_permissions)
        
        print(f"✅ Added {restaurant_permissions.count()} permissions to Restaurant Owner group")
    else:
        print("ℹ️  'Restaurant Owner' group already exists")
    
    # Sync existing restaurant owners to the group
    sync_restaurant_owners_to_group()


def sync_restaurant_owners_to_group():
    """
    Sync users who own restaurants to the Restaurant Owner group.
    
    This ensures that all users with restaurants are properly
    categorized as restaurant owners in the system.
    """
    from django.apps import apps
    
    # Get models through apps registry to avoid import issues
    User = apps.get_model('auth', 'User')
    Restaurant = apps.get_model('restaurant', 'Restaurant')
    Group = apps.get_model('auth', 'Group')
    
    restaurant_owner_group = Group.objects.get(name='Restaurant Owner')
    
    # Get all users who own restaurants
    users_with_restaurants = User.objects.filter(
        restaurants__isnull=False
    ).distinct()
    
    # Add them to the Restaurant Owner group
    added_count = 0
    for user in users_with_restaurants:
        if not restaurant_owner_group.user_set.filter(id=user.id).exists():
            restaurant_owner_group.user_set.add(user)
            added_count += 1
    
    if added_count > 0:
        print(f"✅ Synced {added_count} users to Restaurant Owner group")
    else:
        print("ℹ️  All restaurant owners already in group")
