"""
Custom authentication backends for the accounts app.

This module contains custom authentication backends for handling
role-based authentication and authorization.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

UserModel = get_user_model()

class RoleBasedAuthBackend(ModelBackend):
    """
    Custom authentication backend that handles role-based authentication.
    
    This backend extends Django's ModelBackend to provide comprehensive
    role-based authentication and authorization using a single user table
    with integrated permissions stored as JSON.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate a user with the given credentials.
        
        This method supports authentication by email or username and properly
        validates credentials against the database.
        
        Args:
            request: The current request object
            username: The username or email to authenticate with
            password: The password to authenticate with
            **kwargs: Additional keyword arguments
            
        Returns:
            User: The authenticated user if successful, None otherwise
        """
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        
        if not username or not password:
            return None
            
        # Support authentication with both email and username
        try:
            # First try to authenticate with the provided field as email
            if '@' in username:
                user = UserModel._default_manager.filter(email=username).first()
            else:
                # If not an email, try username
                user = UserModel._default_manager.filter(username=username).first()
                
            if not user:
                # Fall back to default behavior if user not found by direct lookup
                user = UserModel._default_manager.get_by_natural_key(username)
                
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user.
            UserModel().set_password(password)
            return None
        
        if user.check_password(password) and self.user_can_authenticate(user):
            # Log the successful authentication attempt
            if request and hasattr(request, 'session'):
                request.session['user_role'] = user.role
                
            return user
        return None
    
    def has_perm(self, user_obj, perm, obj=None):
        """
        Check if the user has the specified permission.
        
        This method uses Django's permission system and enhances it with
        the custom role-based permissions stored in the permissions JSON field.
        
        Args:
            user_obj: The user object
            perm: The permission to check (in format 'app_label.codename')
            obj: The object to check the permission against
            
        Returns:
            bool: True if the user has the permission, False otherwise
        """
        # Superusers have all permissions
        if user_obj.is_superuser:
            return True
        
        # Parse the permission string to get app_label and action
        try:
            app_label, action_perm = perm.split('.')
            action = action_perm.split('_')[0]  # Extract 'add', 'change', 'view', 'delete'
        except ValueError:
            # Default to standard permission checking if perm format is invalid
            return super().has_perm(user_obj, perm, obj)
            
        # Map Django permission actions to our JSON permission actions
        action_map = {
            'add': 'create',
            'change': 'update',
            'view': 'read',
            'delete': 'delete'
        }
        json_action = action_map.get(action, action)
            
        # Check permissions in the JSON field
        if user_obj.permissions and app_label in user_obj.permissions:
            if json_action in user_obj.permissions[app_label]:
                return user_obj.permissions[app_label][json_action]
        
        # Fall back to standard permission checking
        return super().has_perm(user_obj, perm, obj)
    
    def has_module_perms(self, user_obj, app_label):
        """
        Check if the user has any permissions for the given app.
        
        Args:
            user_obj: The user object
            app_label: The application label to check permissions for
            
        Returns:
            bool: True if the user has any permission for the app, False otherwise
        """
        # Superusers have all permissions
        if user_obj.is_superuser:
            return True
            
        # Check JSON permissions
        if user_obj.permissions and app_label in user_obj.permissions:
            # Return True if the user has any permission for this module
            return any(user_obj.permissions[app_label].values())
            
        # Fall back to standard module permissions checking
        return super().has_module_perms(user_obj, app_label)
    
    def user_can_authenticate(self, user):
        """
        Check if the user is allowed to authenticate.
        
        This method ensures that inactive users cannot log in,
        regardless of correct credentials.
        
        Args:
            user: The user to check
            
        Returns:
            bool: True if the user can authenticate, False otherwise
        """
        is_active = getattr(user, 'is_active', None)
        return is_active or is_active is None
