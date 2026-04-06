"""
Admin configurations for the accounts app.

This module registers the accounts app models with the Django admin interface
and customizes their presentation and management features.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import UserProfile, UserFavorite, UserPreference

# Get the custom user model
User = get_user_model()


class UserProfileInline(admin.StackedInline):
    """
    Inline admin view for UserProfile model.
    
    This allows editing of profile information directly from the User admin page,
    providing a more integrated user management experience.
    """
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class UserAdmin(BaseUserAdmin):
    """
    Enhanced User admin configuration.
    
    Extends the default UserAdmin to include the UserProfile inline,
    enabling administrators to manage user profiles efficiently.
    """
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'groups', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    
    # Add role to fieldsets for the edit form
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions', 'role'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Add role to the add form
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )
    
    def get_inline_instances(self, request, obj=None):
        """
        Get the inline instances for this admin.
        
        Only displays the profile inline when editing an existing user,
        not when creating a new one.
        
        Args:
            request: The HTTP request object
            obj: The User object being edited, or None if creating
            
        Returns:
            list: Inline admin instances
        """
        if not obj:
            return []
        return super().get_inline_instances(request, obj)


@admin.register(UserFavorite)
class UserFavoriteAdmin(admin.ModelAdmin):
    """
    Admin configuration for the UserFavorite model.
    
    Customizes the list display, filtering, and search capabilities
    for user favorites in the admin interface.
    """
    list_display = ('user', 'content_type', 'object_id', 'created_at')
    list_filter = ('content_type', 'created_at')
    search_fields = ('user__username', 'content_type')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        """
        Optimize the queryset for the admin list view.
        
        Adds select_related for the user to avoid additional queries.
        
        Args:
            request: The HTTP request object
            
        Returns:
            QuerySet: Optimized queryset
        """
        return super().get_queryset(request).select_related('user')


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    """
    Admin configuration for the UserPreference model.
    
    Customizes the list display, filtering, and search capabilities
    for user preferences in the admin interface.
    """
    list_display = ('user', 'budget_preference', 'created_at', 'updated_at')
    list_filter = ('budget_preference', 'created_at')
    search_fields = ('user__username',)
    date_hierarchy = 'updated_at'
    ordering = ('-updated_at',)
    
    def get_queryset(self, request):
        """
        Optimize the queryset for the admin list view.
        
        Adds select_related for the user to avoid additional queries.
        
        Args:
            request: The HTTP request object
            
        Returns:
            QuerySet: Optimized queryset
        """
        return super().get_queryset(request).select_related('user')


# Only register the User model if it's not already registered
if not admin.site.is_registered(User):
    admin.site.register(User, UserAdmin)
