"""
Admin configuration for the accounts app.

This module registers the CustomUser, UserProfile, and UserPreferences models 
with the Django admin interface.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .models import UserProfile, UserPreferences

# Get the custom user model
User = get_user_model()

class UserAdmin(BaseUserAdmin):
    """
    Custom User admin interface for MongoDB-based CustomUser model.
    
    This admin class configures how CustomUser objects appear and can be edited
    in the Django admin interface. The class is designed to work with MongoDB
    using the Djongo engine.
    
    Attributes:
        list_display: Fields to display in the list view
        list_filter: Fields that can be used to filter the list view
        search_fields: Fields that can be searched via the admin search bar
        ordering: Default ordering for the list view
        fieldsets: Field groupings for the detail view
        add_fieldsets: Fields shown when adding a new user
    """
    list_display = ('email', 'username', 'is_staff', 'is_verified')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_verified', 'groups')
    search_fields = ('username', 'email')
    ordering = ('email',)
    
    # Define fieldsets for the add and change forms
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (_('Personal info'), {'fields': ('phone_number',)}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )

# Register the custom User model with our UserAdmin
admin.site.register(User, UserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for the UserProfile model with MongoDB support.
    
    This class configures how UserProfile objects appear and can be edited
    in the Django admin interface, taking into account the MongoDB backend.
    
    Attributes:
        list_display: Fields to display in the list view
        search_fields: Fields that can be searched
        list_filter: Fields that can be used for filtering
    """
    list_display = ('display_user_email', 'date_of_birth')
    search_fields = ('user__email', 'user__username')
    list_filter = ('date_of_birth',)
    raw_id_fields = ('user',)  # Add this to use a lookup widget for the user field
    
    def display_user_email(self, obj):
        """
        Returns the email of the associated user for display in the admin.
        
        This method provides a user-friendly way to identify UserProfile objects
        in the admin interface by showing the email of the related CustomUser.
        
        Args:
            obj: The UserProfile instance
            
        Returns:
            str: The email of the associated CustomUser, or 'No user' if none exists
        """
        if obj.user_id:  # Check if user_id exists
            try:
                return obj.user.email
            except User.DoesNotExist:
                return 'User not found'
        return 'No user'
    display_user_email.short_description = 'User Email'

@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    """
    Admin interface for the UserPreferences model with MongoDB support.
    
    This class configures how UserPreferences objects appear and can be edited
    in the Django admin interface, designed specifically for the MongoDB backend.
    
    Attributes:
        list_display: Fields to display in the list view
        list_filter: Fields that can be used for filtering
    """
    list_display = ('display_user_email', 'preferred_currency', 'language', 
                    'newsletter_subscription', 'marketing_emails')
    list_filter = ('preferred_currency', 'language', 'newsletter_subscription', 'marketing_emails')
    
    def display_user_email(self, obj):
        """
        Returns the email of the associated user for display in the admin.
        
        This method provides a user-friendly way to identify UserPreferences objects
        in the admin interface by showing the email of the related CustomUser.
        
        Args:
            obj: The UserPreferences instance
            
        Returns:
            str: The email of the associated CustomUser, or 'No user' if none exists
        """
        try:
            user = User.objects.get(id=obj.user)
            return user.email
        except User.DoesNotExist:
            return 'No user'
    display_user_email.short_description = 'User Email'
