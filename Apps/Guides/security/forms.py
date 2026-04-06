"""
Forms for user authentication, security management, and two-factor authentication.

This module provides form classes for user authentication, role management,
two-factor authentication, and other security-related features.
"""

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import User, Role, RoleAssignment, TwoFactorAuth

class UserRegistrationForm(UserCreationForm):
    """
    Form for user registration with additional fields beyond the basic User model.
    
    This form extends Django's UserCreationForm to handle the creation of new users
    with email validation and additional fields.
    """
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )
    
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )
    
    class Meta:
        """
        Meta options for UserRegistrationForm.
        
        Defines model, fields, and widget attributes.
        """
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def clean_email(self):
        """
        Validate that the email is unique.
        
        Returns:
            str: The validated email
            
        Raises:
            ValidationError: If the email is already in use
        """
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email address is already registered.")
        return email
    
    def save(self, commit=True):
        """
        Save the user with the provided data.
        
        Args:
            commit (bool): Whether to save to the database
            
        Returns:
            User: The created user object
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            # Assign default 'user' role to new registrations
            try:
                user_role = Role.objects.get(name='user')
                RoleAssignment.objects.create(user=user, role=user_role)
            except Role.DoesNotExist:
                pass  # If default role doesn't exist yet, skip assignment
                
        return user


class UserLoginForm(AuthenticationForm):
    """
    Form for user login with additional validation.
    
    This form extends Django's AuthenticationForm to provide custom styling
    and additional security checks like account lockout.
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    
    def clean(self):
        """
        Validate the login credentials and check for account lockout.
        
        Returns:
            dict: The cleaned form data
            
        Raises:
            ValidationError: If authentication fails or the account is locked
        """
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username and password:
            # Check if account is locked by using the FailedLoginAttempt model
            from .models import FailedLoginAttempt
            
            # Get client IP from request
            ip_address = self.request.META.get('REMOTE_ADDR', '')
            
            # Check if account is locked
            is_locked, minutes = FailedLoginAttempt.is_account_locked(username, ip_address)
            
            if is_locked:
                raise ValidationError(
                    f"This account is temporarily locked due to too many failed login attempts. "
                    f"Please try again in {minutes} minutes."
                )
            
            # Attempt authentication
            self.user_cache = authenticate(
                self.request, username=username, password=password
            )
            
            if self.user_cache is None:
                # Record the failed attempt
                FailedLoginAttempt.record_failure(
                    username, 
                    ip_address, 
                    self.request.META.get('HTTP_USER_AGENT', '')
                )
                
                raise ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                    params={'username': self.username_field.verbose_name}
                )
            else:
                self.confirm_login_allowed(self.user_cache)
                
        return self.cleaned_data


class RoleForm(forms.ModelForm):
    """
    Form for creating and editing user roles.
    
    This form allows admins to define roles with permissions represented as JSON.
    """
    permissions = forms.JSONField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
        help_text="Permissions in JSON format"
    )
    
    class Meta:
        """
        Meta options for RoleForm.
        
        Defines model and fields.
        """
        model = Role
        fields = ['name', 'description', 'permissions']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def clean_permissions(self):
        """
        Validate that the permissions field contains valid JSON with the expected structure.
        
        Returns:
            dict: The validated permissions
            
        Raises:
            ValidationError: If the permissions are not in the expected format
        """
        permissions = self.cleaned_data.get('permissions')
        
        # Check that permissions has the expected structure
        required_modules = ['destinations', 'tours', 'users']
        required_actions = ['create', 'read', 'update', 'delete']
        
        for module in required_modules:
            if module not in permissions:
                raise ValidationError(f"Missing required module '{module}' in permissions")
            
            for action in required_actions:
                if action not in permissions[module]:
                    raise ValidationError(f"Missing required action '{action}' for module '{module}'")
                
                if not isinstance(permissions[module][action], bool):
                    raise ValidationError(f"Permission value for {module}.{action} must be a boolean")
                    
        return permissions


class RoleAssignmentForm(forms.ModelForm):
    """
    Form for assigning roles to users.
    
    This form allows admins to assign roles to users and tracks who made the assignment.
    """
    class Meta:
        """
        Meta options for RoleAssignmentForm.
        
        Defines model and fields.
        """
        model = RoleAssignment
        fields = ['user', 'role']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the form with an optional assigned_by parameter.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        self.assigned_by = kwargs.pop('assigned_by', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        """
        Save the role assignment, tracking who made the assignment.
        
        Args:
            commit (bool): Whether to save to the database
            
        Returns:
            RoleAssignment: The created role assignment object
        """
        role_assignment = super().save(commit=False)
        
        if self.assigned_by:
            role_assignment.assigned_by = self.assigned_by
            
        if commit:
            role_assignment.save()
            
        return role_assignment


class UserRoleUpdateForm(forms.Form):
    """
    Form for updating a user's roles with multiple selection.
    
    This form allows admins to assign multiple roles to a user at once.
    """
    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'role-checkbox'}),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the form with a user and assigned_by parameters.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        self.user = kwargs.pop('user')
        self.assigned_by = kwargs.pop('assigned_by')
        super().__init__(*args, **kwargs)
        
        # Pre-select the roles the user already has
        user_roles = Role.objects.filter(roleassignment__user=self.user)
        self.initial['roles'] = user_roles
    
    def save(self):
        """
        Save the updated role assignments for the user.
        
        This method adds and removes role assignments as needed based on the form data.
        
        Returns:
            list: The user's updated role assignments
        """
        selected_roles = self.cleaned_data['roles']
        
        # Get current roles
        current_roles = Role.objects.filter(roleassignment__user=self.user)
        
        # Remove roles that were deselected
        for role in current_roles:
            if role not in selected_roles:
                RoleAssignment.objects.filter(user=self.user, role=role).delete()
        
        # Add new roles that were selected
        for role in selected_roles:
            if role not in current_roles:
                RoleAssignment.objects.create(
                    user=self.user,
                    role=role,
                    assigned_by=self.assigned_by
                )
        
        return RoleAssignment.objects.filter(user=self.user)


class TwoFactorAuthForm(forms.Form):
    """
    Form for setting up two-factor authentication.
    
    This form allows users to select their preferred 2FA method.
    """
    METHOD_CHOICES = TwoFactorAuth.METHOD_CHOICES
    
    method = forms.ChoiceField(
        label=_('Authentication Method'),
        choices=METHOD_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial=TwoFactorAuth.METHOD_APP,
        help_text=_('Select your preferred authentication method')
    )


class TwoFactorVerifyForm(forms.Form):
    """
    Form for verifying a two-factor authentication code.
    
    Used both during setup and during login verification.
    """
    code = forms.CharField(
        label=_('Verification Code'),
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': '000000',
            'autocomplete': 'off',
            'inputmode': 'numeric',
            'pattern': '[0-9]*'
        }),
        help_text=_('Enter the 6-digit code from your authenticator app')
    )
    
    def clean_code(self):
        """
        Validate that the code contains only digits.
        
        Returns:
            str: The validated code
            
        Raises:
            ValidationError: If the code contains non-digit characters
        """
        code = self.cleaned_data.get('code')
        if not code.isdigit():
            raise ValidationError(_('Code must contain only digits'))
        return code


class BackupCodesForm(forms.Form):
    """
    Form for generating new backup codes or verifying a backup code.
    
    Used when user needs to regenerate backup codes or authenticate using a backup code.
    """
    code = forms.CharField(
        label=_('Backup Code'),
        max_length=10,
        min_length=8,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': 'XXXX-XXXX',
            'autocomplete': 'off'
        }),
        help_text=_('Enter one of your backup codes')
    )
    
    confirm = forms.BooleanField(
        label=_('I have saved my backup codes'),
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
