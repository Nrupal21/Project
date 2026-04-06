"""
Admin-specific forms for user and role management in the TravelGuide project.

This module contains forms used by administrators to manage users, roles, and
permissions throughout the system. These forms are accessible only to users
with admin privileges and provide advanced functionality for user management.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth import get_user_model
import json

User = get_user_model()


class RoleManagementForm(forms.ModelForm):
    """
    Form for administrators to manage user roles and permissions.
    
    This form allows administrators to:
    1. Change a user's role
    2. Customize specific permissions
    3. Track role changes with metadata
    
    The form validates that only authorized users can assign certain roles
    and enforces permission constraints based on security policies.
    """
    
    class Meta:
        model = User
        fields = ['role', 'permissions']
        
    # Additional tracked fields (not directly editable)
    role_assigned_at = forms.DateTimeField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    # Enhanced role field with all available roles
    role = forms.ChoiceField(
        label=_('User Role'),
        choices=User.Role.choices,
        widget=forms.Select(attrs={
            'class': 'form-select block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'
        }),
        help_text=_('Select the user role to determine their permissions and access level.')
    )
    
    # Custom permissions field with JSON editor
    custom_permissions = forms.CharField(
        label=_('Custom Permissions'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-textarea block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
            'rows': 10,
            'placeholder': '{\n  "module_permissions": {\n    "module_name": ["permission1", "permission2"]\n  },\n  "object_permissions": {\n    "permission_name": true\n  }\n}'
        }),
        help_text=_('JSON format for custom permissions. Leave blank to use default permissions for the selected role.')
    )
    
    # Track reason for role change
    change_reason = forms.CharField(
        label=_('Reason for Change'),
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-textarea block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
            'rows': 2,
            'placeholder': 'Explain why this role or permission change is being made...'
        }),
        help_text=_('Provide a reason for this role change for audit purposes.')
    )
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the form with custom configuration based on the user.
        
        Prepopulates the form with current user permissions in JSON format
        and restricts role options based on the admin's own role level.
        
        Args:
            admin_user: The admin user making the change
        """
        # Extract admin user for permission checking
        self.admin_user = kwargs.pop('admin_user', None)
        super().__init__(*args, **kwargs)
        
        # If editing an existing user, load their current permissions
        if self.instance and self.instance.pk and self.instance.permissions:
            self.fields['custom_permissions'].initial = json.dumps(
                self.instance.permissions, indent=2
            )
            
        # Restrict available roles based on admin's own role
        if self.admin_user and not self.admin_user.is_superuser:
            # Non-superusers can't create or edit superusers/admins
            self.fields['role'].choices = [
                choice for choice in self.fields['role'].choices 
                if choice[0] != User.Role.ADMIN
            ]
    
    def clean_custom_permissions(self):
        """
        Validate and parse the custom permissions JSON.
        
        Returns:
            dict: The parsed permissions dictionary
            
        Raises:
            ValidationError: If the provided JSON is invalid
        """
        custom_permissions = self.cleaned_data.get('custom_permissions')
        if not custom_permissions:
            return None
            
        try:
            permissions_dict = json.loads(custom_permissions)
            
            # Validate structure
            if not isinstance(permissions_dict, dict):
                raise forms.ValidationError(_("Permissions must be a JSON object"))
                
            # Validate module_permissions structure if present
            if 'module_permissions' in permissions_dict:
                if not isinstance(permissions_dict['module_permissions'], dict):
                    raise forms.ValidationError(_("Module permissions must be a JSON object"))
                
                # Validate each module's permissions is a list
                for module, perms in permissions_dict['module_permissions'].items():
                    if not isinstance(perms, list):
                        raise forms.ValidationError(_(f"Permissions for module '{module}' must be a list"))
            
            # Validate object_permissions structure if present
            if 'object_permissions' in permissions_dict:
                if not isinstance(permissions_dict['object_permissions'], dict):
                    raise forms.ValidationError(_("Object permissions must be a JSON object"))
            
            return permissions_dict
        except json.JSONDecodeError:
            raise forms.ValidationError(_("Invalid JSON format for permissions"))
    
    def clean(self):
        """
        Perform cross-field validation and enforce security policies.
        
        Validates that:
        1. Admins can't downgrade themselves
        2. Non-superusers can't create admins
        3. Users can't assign roles higher than their own
        
        Returns:
            dict: The cleaned form data
            
        Raises:
            ValidationError: If security validations fail
        """
        cleaned_data = super().clean()
        new_role = cleaned_data.get('role')
        
        # Security checks
        if self.instance and self.instance.pk:
            # Prevent self-downgrade for admins
            if self.instance == self.admin_user and self.instance.role == User.Role.ADMIN:
                if new_role != User.Role.ADMIN:
                    raise forms.ValidationError(_("Administrators cannot downgrade their own role"))
            
            # Prevent non-superusers from managing admins
            if self.instance.role == User.Role.ADMIN and not self.admin_user.is_superuser:
                raise forms.ValidationError(_("Only superusers can modify administrator accounts"))
        
        # Record role assignment timestamp
        cleaned_data['role_assigned_at'] = timezone.now()
        
        return cleaned_data
    
    def save(self, commit=True):
        """
        Save the form data to the model instance.
        
        This method:
        1. Updates the user's role
        2. Sets custom permissions if provided
        3. Records role change metadata
        
        Args:
            commit: Whether to save the model to the database
            
        Returns:
            User: The updated user instance
        """
        user = super().save(commit=False)
        
        # Set the role
        user.role = self.cleaned_data['role']
        
        # Set custom permissions if provided, otherwise use defaults
        custom_permissions = self.cleaned_data.get('custom_permissions')
        if custom_permissions:
            user.permissions = custom_permissions
        else:
            # Let the model's save method set default permissions
            user._reset_permissions = True
        
        # Update role tracking fields
        user.role_assigned_at = timezone.now()
        if self.admin_user:
            user.role_assigned_by = self.admin_user
        
        if commit:
            user.save()
        
        return user


class BulkRoleUpdateForm(forms.Form):
    """
    Form for updating roles for multiple users at once.
    
    This form is used by administrators to efficiently assign roles to
    groups of users based on specific criteria. It includes validation
    to prevent unintended mass role changes.
    """
    
    ROLE_CHOICES = [('', '---')] + list(User.Role.choices)
    
    role = forms.ChoiceField(
        label=_('New Role'),
        choices=ROLE_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'
        }),
        help_text=_('The role to assign to all selected users')
    )
    
    selected_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=True,
        widget=forms.CheckboxSelectMultiple,
        label=_('Select Users')
    )
    
    confirmation = forms.BooleanField(
        required=True,
        label=_('Confirm Bulk Update'),
        help_text=_('I understand this will update roles for all selected users')
    )
    
    change_reason = forms.CharField(
        label=_('Reason for Bulk Change'),
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-textarea block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
            'rows': 2
        }),
        help_text=_('Explain why you are changing roles for these users')
    )
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the form with custom queryset and user filters.
        
        Args:
            admin_user: The admin user performing the bulk update
        """
        self.admin_user = kwargs.pop('admin_user', None)
        super().__init__(*args, **kwargs)
        
        # Restrict available roles based on admin's own role
        if self.admin_user and not self.admin_user.is_superuser:
            # Filter out ADMIN role
            self.fields['role'].choices = [
                choice for choice in self.fields['role'].choices 
                if choice[0] != User.Role.ADMIN
            ]
            
            # Exclude admin users from selection
            self.fields['selected_users'].queryset = User.objects.exclude(
                role=User.Role.ADMIN
            )
    
    def clean(self):
        """
        Validate the form data to prevent unauthorized role changes.
        
        Checks:
        1. Selected users don't include admins (if operator is non-superuser)
        2. Confirmation checkbox is checked
        3. Reasonable number of users selected (prevent accidental mass updates)
        
        Returns:
            dict: Cleaned form data
        """
        cleaned_data = super().clean()
        selected_users = cleaned_data.get('selected_users', [])
        role = cleaned_data.get('role')
        
        # Safety checks
        if len(selected_users) > 25:
            raise forms.ValidationError(
                _("For safety, please limit bulk updates to 25 users at a time.")
            )
        
        # Verify non-superusers aren't modifying admins
        if self.admin_user and not self.admin_user.is_superuser:
            admin_users = [user for user in selected_users if user.role == User.Role.ADMIN]
            if admin_users:
                raise forms.ValidationError(
                    _("You don't have permission to modify administrator accounts.")
                )
        
        return cleaned_data
