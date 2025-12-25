"""
Custom authentication backend for the food ordering system.

This backend allows users to login using either their username or email address,
providing a more flexible authentication experience.
"""
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.db.models import Q


class UsernameOrEmailBackend(BaseBackend):
    """
    Custom authentication backend that accepts either username or email.
    
    This backend extends Django's default authentication to allow users to login
    with either their username or email address. It checks if the provided
    username contains an '@' symbol to determine if it's an email address.
    
    Usage:
    - Add this backend to AUTHENTICATION_BACKENDS in settings.py
    - Users can login with username: "john_doe" or email: "john@example.com"
    
    Features:
    - Case-insensitive email authentication
    - Case-sensitive username authentication (Django default)
    - Maintains all Django authentication security features
    - Works with existing Django forms and views
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user using either username or email.
        
        Args:
            request: Django HTTP request object (optional)
            username: Username or email address provided by user
            password: Password provided by user
            **kwargs: Additional keyword arguments
            
        Returns:
            User: Authenticated user object if credentials are valid, None otherwise
        """
        User = get_user_model()
        
        if username is None or password is None:
            return None
        
        # Check if username is an email address
        if '@' in username:
            # Authenticate using email (case-insensitive)
            try:
                user = User.objects.filter(email__iexact=username).first()
                if user and user.check_password(password) and self.user_can_authenticate(user):
                    return user
            except Exception:
                return None
        else:
            # Authenticate using username (case-sensitive, Django default)
            try:
                user = User.objects.get(username=username)
                if user.check_password(password) and self.user_can_authenticate(user):
                    return user
            except User.DoesNotExist:
                return None
        
        return None
    
    def get_user(self, user_id):
        """
        Retrieve user by primary key.
        
        Args:
            user_id: Primary key of the user
            
        Returns:
            User: User object if found and can authenticate, None otherwise
        """
        User = get_user_model()
        
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        
        return user if self.user_can_authenticate(user) else None
    
    def user_can_authenticate(self, user):
        """
        Check if a given user can be authenticated.
        
        This method ensures that inactive users cannot authenticate,
        maintaining Django's security model.
        
        Args:
            user: User object to check
            
        Returns:
            bool: True if user can authenticate, False otherwise
        """
        is_active = getattr(user, 'is_active', False)
        return is_active and user.has_usable_password()


class CaseInsensitiveUsernameBackend(BaseBackend):
    """
    Alternative backend that allows case-insensitive username authentication.
    
    This backend can be used if you want usernames to be case-insensitive
    like email addresses. This is an optional alternative to the main backend.
    
    Note: Use only one backend at a time to avoid confusion.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user using case-insensitive username or email.
        
        Args:
            request: Django HTTP request object (optional)
            username: Username or email address provided by user
            password: Password provided by user
            **kwargs: Additional keyword arguments
            
        Returns:
            User: Authenticated user object if credentials are valid, None otherwise
        """
        User = get_user_model()
        
        if username is None or password is None:
            return None
        
        # Try to find user by username (case-insensitive) or email (case-insensitive)
        try:
            user = User.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except User.DoesNotExist:
            return None
        
        return None
    
    def get_user(self, user_id):
        """
        Retrieve user by primary key.
        
        Args:
            user_id: Primary key of the user
            
        Returns:
            User: User object if found and can authenticate, None otherwise
        """
        User = get_user_model()
        
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        
        return user if self.user_can_authenticate(user) else None
    
    def user_can_authenticate(self, user):
        """
        Check if a given user can be authenticated.
        
        Args:
            user: User object to check
            
        Returns:
            bool: True if user can authenticate, False otherwise
        """
        is_active = getattr(user, 'is_active', False)
        return is_active and user.has_usable_password()
