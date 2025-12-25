"""
Admin interface enhancements for user role management.

This module provides custom admin filters and displays to make it easy
for administrators to identify and manage restaurant owners.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User, Group
from django.utils.html import format_html
from django.urls import reverse


class UserRoleFilter(admin.SimpleListFilter):
    """
    Custom filter to display users by their role.
    
    This filter allows administrators to easily view users by:
    - Restaurant Owner
    - Active Restaurant Owner (with approved restaurants)
    - Staff
    - Customer
    """
    
    title = 'User Role'
    parameter_name = 'user_role'
    
    def lookups(self, request, model_admin):
        """
        Return the list of filter options.
        
        Returns:
            list: Tuple of (value, label) pairs for filter options
        """
        return [
            ('restaurant_owner', 'Restaurant Owner'),
            ('active_restaurant_owner', 'Active Restaurant Owner'),
            ('staff', 'Staff Member'),
            ('customer', 'Customer'),
        ]
    
    def queryset(self, request, queryset):
        """
        Filter the queryset based on the selected role.
        
        Args:
            request: HTTP request object
            queryset: User queryset to filter
            
        Returns:
            QuerySet: Filtered queryset based on role
        """
        value = self.value()
        
        if value == 'restaurant_owner':
            return queryset.filter(groups__name='Restaurant Owner')
        elif value == 'active_restaurant_owner':
            return queryset.filter(
                groups__name='Restaurant Owner',
                restaurants__approval_status='approved',
                restaurants__is_active=True
            ).distinct()
        elif value == 'staff':
            return queryset.filter(is_staff=True)
        elif value == 'customer':
            return queryset.filter(
                groups__name__in=['Restaurant Owner'],
                is_staff=False,
                is_superuser=False
            )
        
        return queryset


class UserAdmin(BaseUserAdmin):
    """
    Enhanced User admin with restaurant owner information.
    
    This admin class extends Django's default UserAdmin to include:
    - Role filtering
    - Restaurant count display
    - Quick links to restaurant management
    - Restaurant owner status indicators
    """
    
    list_display = (
        'username', 
        'email', 
        'first_name', 
        'last_name', 
        'user_role_display',
        'restaurant_count',
        'is_staff',
        'is_active',
        'date_joined'
    )
    
    list_filter = (
        UserRoleFilter,
        'is_staff', 
        'is_superuser', 
        'is_active', 
        'groups',
    )
    
    search_fields = (
        'username', 
        'email', 
        'first_name', 
        'last_name'
    )
    
    ordering = ('-date_joined',)
    
    def user_role_display(self, obj):
        """
        Display user's primary role with color-coded badges.
        
        Args:
            obj: User instance
            
        Returns:
            str: HTML with role badge
        """
        # Import user role function to avoid circular import issues
        from .utils.user_roles import get_user_role
        
        role = get_user_role(obj)
        
        # Define badge colors for different roles
        badge_colors = {
            'Superuser': '#dc3545',  # Red
            'Staff': '#fd7e14',      # Orange
            'Restaurant Owner': '#28a745',  # Green
            'Pending Restaurant Owner': '#ffc107',  # Yellow
            'Customer': '#6c757d',   # Gray
            'Anonymous': '#6c757d',  # Gray
        }
        
        color = badge_colors.get(role, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, role
        )
    
    user_role_display.short_description = 'Role'
    
    def restaurant_count(self, obj):
        """
        Display number of restaurants owned by the user with quick links.
        
        Args:
            obj: User instance
            
        Returns:
            str: HTML with restaurant count and links
        """
        # Import user role function to avoid circular import issues
        from .utils.user_roles import get_user_restaurants
        
        restaurants = get_user_restaurants(obj)
        count = restaurants.count()
        
        if count > 0:
            # Create link to restaurants filtered by owner
            restaurant_url = reverse('admin:restaurant_restaurant_changelist') + f'?owner__id__exact={obj.id}'
            
            return format_html(
                '<a href="{}" style="color: #28a745; font-weight: bold;">{} restaurant(s)</a>',
                restaurant_url, count
            )
        
        return format_html('<span style="color: #6c757d;">0</span>')
    
    restaurant_count.short_description = 'Restaurants'
    
    def get_queryset(self, request):
        """
        Optimize queryset with related data to reduce database queries.
        
        Args:
            request: HTTP request object
            
        Returns:
            QuerySet: Optimized queryset with related data
        """
        queryset = super().get_queryset(request)
        return queryset.select_related('profile').prefetch_related('groups', 'restaurants')


class GroupAdmin(admin.ModelAdmin):
    """
    Enhanced Group admin with member count and quick links.
    """
    
    list_display = ('name', 'member_count', 'permissions_display')
    list_filter = ('name',)
    search_fields = ('name',)
    
    def member_count(self, obj):
        """
        Display number of users in the group.
        
        Args:
            obj: Group instance
            
        Returns:
            str: Member count with link to filtered users
        """
        count = obj.user_set.count()
        
        if count > 0:
            user_url = reverse('admin:auth_user_changelist') + f'?groups__id__exact={obj.id}'
            return format_html(
                '<a href="{}" style="font-weight: bold;">{} member(s)</a>',
                user_url, count
            )
        
        return '0'
    
    member_count.short_description = 'Members'
    
    def permissions_display(self, obj):
        """
        Display key permissions for the group.
        
        Args:
            obj: Group instance
            
        Returns:
            str: Summary of important permissions
        """
        permissions = obj.permissions.all()
        
        if obj.name == 'Restaurant Owner':
            restaurant_perms = permissions.filter(
                content_type__model='restaurant'
            ).count()
            
            return format_html(
                '<span style="color: #28a745;">{} restaurant permissions</span>',
                restaurant_perms
            )
        
        return f'{permissions.count()} permissions'
    
    permissions_display.short_description = 'Permissions'


# Register enhanced admin classes
try:
    # Unregister the default User admin and register our enhanced version
    admin.site.unregister(User)
    admin.site.register(User, UserAdmin)
    
    # Register enhanced Group admin
    admin.site.unregister(Group)
    admin.site.register(Group, GroupAdmin)
    
    # Add custom admin site header and title
    admin.site.site_header = 'Food Ordering System Administration'
    admin.site.site_title = 'Food Ordering Admin'
    admin.site.index_title = 'Welcome to Food Ordering System Administration'
    
except admin.sites.NotRegistered:
    # Models not yet registered, will be registered when Django loads
    pass
