"""
Views for user management, authentication, and role-based access control.

This module provides view functions and classes for user registration,
authentication, role management, and access control features for the
TravelGuide application.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import User, Role, RoleAssignment, SecurityLog, TwoFactorAuth, FailedLoginAttempt
from .forms import UserRegistrationForm, UserLoginForm, RoleForm, RoleAssignmentForm, UserRoleUpdateForm
from .utils import (
    generate_totp_secret, generate_totp_uri, generate_qr_code_base64,
    verify_totp_code, verify_backup_code, generate_backup_codes,
    complete_login_after_twofa, get_client_ip
)


def is_admin(user):
    """
    Check if a user has admin role.
    
    Args:
        user (User): The user to check
        
    Returns:
        bool: True if the user has admin role, False otherwise
    """
    if not user.is_authenticated:
        return False
        
    # Use the direct role property from the user model
    return user.is_admin


def is_manager_or_admin(user):
    """
    Check if a user has manager or admin role.
    
    Args:
        user (User): The user to check
        
    Returns:
        bool: True if the user has manager or admin role, False otherwise
    """
    if not user.is_authenticated:
        return False
        
    # Use the role property directly from the user model
    return user.is_manager


def has_permission(user, module, action):
    """
    Check if a user has a specific permission based on their role.
    
    Args:
        user (User): The user to check permissions for
        module (str): The module to check permissions for (e.g., 'destinations')
        action (str): The action to check (e.g., 'create', 'read', 'update', 'delete')
        
    Returns:
        bool: True if the user has the permission, False otherwise
    """
    if not user.is_authenticated:
        return False
        
    # Superusers have all permissions
    if user.is_superuser:
        return True
        
    # Use the has_object_permission method from the user model directly
    return user.has_object_permission(module, action)


def register(request):
    """
    Handle user registration.
    
    This view renders and processes the registration form. After successful
    registration, the user is logged in and redirected to the home page.
    
    Args:
        request (HttpRequest): The HTTP request object
        
    Returns:
        HttpResponse: Rendered registration page or redirect after successful registration
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            
            # Log the registration
            SecurityLog.objects.create(
                user=user,
                ip_address=request.META.get('REMOTE_ADDR', ''),
                event_type=SecurityLog.EVENT_USER_CREATED,
                level=SecurityLog.LEVEL_INFO,
                description=f"User {user.username} registered successfully."
            )
            
            messages.success(request, 'Registration successful!')
            return redirect('home')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'security/register.html', {'form': form})


def user_login(request):
    """
    Handle user login with role-based session management.
    
    This view renders and processes the login form. After successful login, 
    the user's role is stored in the session for role-based UI customization,
    security events are logged with role information, and the user is redirected 
    to a role-appropriate page.
    
    The function integrates with the role-based authentication system to ensure
    proper session management and redirection based on user roles.
    
    Args:
        request (HttpRequest): The HTTP request object
        
    Returns:
        HttpResponse: Rendered login page or role-based redirect after successful login
    """
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST, request=request)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Store user's role in session for role-based UI customization
            request.session['user_role'] = user.role
            
            # Store other useful role-related information in session
            request.session['user_permissions'] = user.permissions
            request.session['user_is_admin'] = user.is_admin
            request.session['user_is_manager'] = user.is_manager
            request.session['user_is_guide'] = user.role == 'LOCAL_GUIDE'
            
            # Log the login with role information
            SecurityLog.objects.create(
                user=user,
                ip_address=get_client_ip(request),
                event_type=SecurityLog.EVENT_LOGIN,
                level=SecurityLog.LEVEL_INFO,
                description=f"User {user.username} logged in successfully with role {user.get_role_display()}",
                extra_data={
                    'role': user.role,
                    'permissions': user.permissions,
                    'user_agent': request.META.get('HTTP_USER_AGENT', '')
                }
            )
            
            messages.success(request, f"Welcome back, {user.username}!")
            
            # Check if there's a 'next' parameter in the request
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
                
            # Role-based redirection
            if user.is_superuser or user.is_admin:
                return redirect('admin:index')
            elif user.is_manager:
                return redirect('management:dashboard')
            elif user.role == 'LOCAL_GUIDE':
                return redirect('guides:dashboard')
            else:
                # Default redirect for travelers and other roles
                return redirect('home')
    else:
        form = UserLoginForm(request=request)
    
    return render(request, 'security/login.html', {'form': form})


@login_required
def user_logout(request):
    """
    Handle user logout with proper session cleanup.
    
    This view logs out the current user, cleans up all role-based session data,
    and redirects to the home page. It also logs the logout event for security tracking.
    
    Args:
        request (HttpRequest): The HTTP request object
        
    Returns:
        HttpResponse: Redirect to home page after logout
    """
    # Store username for logging before logout clears request.user
    username = request.user.username
    
    # Log the logout with role information for audit trail
    SecurityLog.objects.create(
        user=request.user,
        ip_address=get_client_ip(request),
        event_type=SecurityLog.EVENT_LOGOUT,
        level=SecurityLog.LEVEL_INFO,
        description=f"User {username} logged out",
        extra_data={
            'role': request.user.role,
            'user_agent': request.META.get('HTTP_USER_AGENT', '')
        }
    )
    
    # Clean up role-based session data before logout
    role_session_keys = ['user_role', 'user_permissions', 'user_is_admin', 'user_is_manager', 'user_is_guide']
    for key in role_session_keys:
        if key in request.session:
            del request.session[key]
    
    # Perform the logout
    logout(request)
    
    messages.info(request, 'You have been successfully logged out.')
    return redirect('home')


@login_required
@user_passes_test(is_admin)
def user_list(request):
    """
    Display a list of all users.
    
    This view is restricted to admins and displays a list of all users
    with their roles.
    
    Args:
        request (HttpRequest): The HTTP request object
        
    Returns:
        HttpResponse: Rendered user list page
    """
    users = User.objects.all().prefetch_related('role_assignments__role')
    
    # Prepare user data with roles for display
    user_data = []
    for user in users:
        roles = [ra.role.name for ra in user.role_assignments.all()]
        user_data.append({
            'user': user,
            'roles': ', '.join(roles) if roles else 'None'
        })
    
    return render(request, 'security/user_list.html', {'user_data': user_data})


@login_required
@user_passes_test(is_admin)
def user_detail(request, user_id):
    """
    Display and manage user details.
    
    This view is restricted to admins and displays details of a specific user,
    including their roles. It also allows updating the user's roles.
    
    Args:
        request (HttpRequest): The HTTP request object
        user_id (UUID): The ID of the user to display
        
    Returns:
        HttpResponse: Rendered user detail page
    """
    user_obj = get_object_or_404(User, pk=user_id)
    
    if request.method == 'POST':
        form = UserRoleUpdateForm(request.POST, user=user_obj, assigned_by=request.user)
        if form.is_valid():
            with transaction.atomic():
                form.save()
                
                # Log the role change
                SecurityLog.objects.create(
                    user=request.user,
                    ip_address=request.META.get('REMOTE_ADDR', ''),
                    event_type=SecurityLog.EVENT_PERMISSION_CHANGE,
                    level=SecurityLog.LEVEL_INFO,
                    description=f"User {request.user.username} updated roles for {user_obj.username}."
                )
                
            messages.success(request, f'Roles updated for {user_obj.username}')
            return redirect('user_detail', user_id=user_id)
    else:
        form = UserRoleUpdateForm(user=user_obj, assigned_by=request.user)
    
    role_assignments = RoleAssignment.objects.filter(user=user_obj).select_related('role', 'assigned_by')
    
    return render(request, 'security/user_detail.html', {
        'user_obj': user_obj,
        'form': form,
        'role_assignments': role_assignments
    })


class RoleListView(UserPassesTestMixin, ListView):
    """
    Display a list of all roles.
    
    This view is restricted to admins and displays all roles in the system.
    """
    model = Role
    template_name = 'security/role_list.html'
    context_object_name = 'roles'
    
    def test_func(self):
        """
        Check if the current user can access this view.
        
        Returns:
            bool: True if the user is an admin, False otherwise
        """
        return is_admin(self.request.user)


class RoleCreateView(UserPassesTestMixin, CreateView):
    """
    Create a new role.
    
    This view is restricted to admins and allows creating new roles with permissions.
    """
    model = Role
    form_class = RoleForm
    template_name = 'security/role_form.html'
    success_url = reverse_lazy('role_list')
    
    def test_func(self):
        """
        Check if the current user can access this view.
        
        Returns:
            bool: True if the user is an admin, False otherwise
        """
        return is_admin(self.request.user)
    
    def form_valid(self, form):
        """
        Process the valid form data and log the role creation.
        
        Args:
            form (RoleForm): The valid form
            
        Returns:
            HttpResponse: Redirect to success URL
        """
        response = super().form_valid(form)
        
        # Log the role creation
        SecurityLog.objects.create(
            user=self.request.user,
            ip_address=self.request.META.get('REMOTE_ADDR', ''),
            event_type=SecurityLog.EVENT_PERMISSION_CHANGE,
            level=SecurityLog.LEVEL_INFO,
            description=f"User {self.request.user.username} created role {form.instance.name}."
        )
        
        messages.success(self.request, f'Role {form.instance.name} created successfully')
        return response


class RoleUpdateView(UserPassesTestMixin, UpdateView):
    """
    Update an existing role.
    
    This view is restricted to admins and allows updating role permissions.
    """
    model = Role
    form_class = RoleForm
    template_name = 'security/role_form.html'
    success_url = reverse_lazy('role_list')
    
    def test_func(self):
        """
        Check if the current user can access this view.
        
        Returns:
            bool: True if the user is an admin, False otherwise
        """
        return is_admin(self.request.user)
    
    def form_valid(self, form):
        """
        Process the valid form data and log the role update.
        
        Args:
            form (RoleForm): The valid form
            
        Returns:
            HttpResponse: Redirect to success URL
        """
        response = super().form_valid(form)
        
        # Log the role update
        SecurityLog.objects.create(
            user=self.request.user,
            ip_address=self.request.META.get('REMOTE_ADDR', ''),
            event_type=SecurityLog.EVENT_PERMISSION_CHANGE,
            level=SecurityLog.LEVEL_INFO,
            description=f"User {self.request.user.username} updated role {form.instance.name}."
        )
        
        messages.success(self.request, f'Role {form.instance.name} updated successfully')
        return response


class RoleDeleteView(UserPassesTestMixin, DeleteView):
    """
    Delete a role.
    
    This view is restricted to admins and allows deleting roles.
    """
    model = Role
    template_name = 'security/role_confirm_delete.html'
    success_url = reverse_lazy('role_list')
    context_object_name = 'role'
    
    def test_func(self):
        """
        Check if the current user can access this view.
        
        Returns:
            bool: True if the user is an admin, False otherwise
        """
        return is_admin(self.request.user)
    
    def delete(self, request, *args, **kwargs):
        """
        Delete the role and log the deletion.
        
        Args:
            request (HttpRequest): The HTTP request object
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            HttpResponse: Redirect to success URL
        """
        role = self.get_object()
        role_name = role.name
        
        response = super().delete(request, *args, **kwargs)
        
        # Log the role deletion
        SecurityLog.objects.create(
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR', ''),
            event_type=SecurityLog.EVENT_PERMISSION_CHANGE,
            level=SecurityLog.LEVEL_INFO,
            description=f"User {request.user.username} deleted role {role_name}."
        )
        
        messages.success(request, f'Role {role_name} deleted successfully')
        return response


@login_required
def profile(request):
    """
    Display and manage the current user's profile.
    
    This view allows users to view and update their profile information.
    
    Args:
        request (HttpRequest): The HTTP request object
        
    Returns:
        HttpResponse: Rendered profile page
    """
    user = request.user
    roles = RoleAssignment.objects.filter(user=user).select_related('role')
    
    # Get user's permissions based on roles
    permissions = {}
    for role_assignment in roles:
        role = role_assignment.role
        role_perms = role.permissions
        
        # Merge permissions from all roles
        for module, actions in role_perms.items():
            if module not in permissions:
                permissions[module] = actions.copy()
            else:
                for action, value in actions.items():
                    # If any role grants a permission, the user has it
                    permissions[module][action] = permissions[module].get(action, False) or value
    
    return render(request, 'security/profile.html', {
        'user': user,
        'roles': roles,
        'permissions': permissions
    })


def access_denied(request):
    """
    Display access denied page.
    
    This view is shown when a user attempts to access a page they don't have permission for.
    
    Args:
        request (HttpRequest): The HTTP request object
        
    Returns:
        HttpResponse: Rendered access denied page
    """
    return render(request, 'security/access_denied.html')


def permission_required(module, action):
    """
    Decorator to check if a user has a specific permission.
    
    This decorator checks if the user has the specified permission and
    redirects to the access denied page if not.
    
    Args:
        module (str): The module to check permissions for (e.g., 'destinations')
        action (str): The action to check (e.g., 'create', 'read', 'update', 'delete')
        
    Returns:
        function: Decorator function
    """
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            if has_permission(request.user, module, action):
                return view_func(request, *args, **kwargs)
            return redirect('access_denied')
        return wrapped_view
    return decorator


class PermissionRequiredMixin(UserPassesTestMixin):
    """
    Mixin to check if a user has specific permissions to access a class-based view.
    
    This mixin is used with class-based views to enforce permission checks.
    """
    permission_module = None
    permission_action = None
    
    def test_func(self):
        """
        Check if the user has the required permission.
        
        Returns:
            bool: True if the user has the required permission, False otherwise
        """
        if not self.permission_module or not self.permission_action:
            raise ValueError("Both permission_module and permission_action must be specified")
        
        return has_permission(self.request.user, self.permission_module, self.permission_action)


# Two-Factor Authentication Views

class TwoFactorSetupView(LoginRequiredMixin, View):
    """
    View for setting up two-factor authentication.
    
    This view generates a new TOTP secret, creates a QR code,
    and displays setup instructions for the user.
    """
    
    def get(self, request):
        """
        Handle GET request to display 2FA setup page.
        
        Generates a new TOTP secret and QR code for the user to scan
        with their authenticator app.
        
        Args:
            request: The HTTP request object
            
        Returns:
            HttpResponse: Rendered 2FA setup page with QR code
        """
        # Generate a new TOTP secret
        secret = generate_totp_secret()
        
        # Generate the URI for the QR code
        uri = generate_totp_uri(request.user, secret)
        
        # Generate a base64-encoded QR code image
        qr_code = generate_qr_code_base64(uri)
        
        # Store the secret in the session temporarily
        # It will be saved to the database after verification
        request.session['twofa_setup_secret'] = secret
        
        return render(request, 'security/twofa_setup.html', {
            'secret': secret,
            'qr_code': qr_code
        })


class TwoFactorConfirmView(LoginRequiredMixin, View):
    """
    View for confirming two-factor authentication setup.
    
    This view verifies the TOTP code entered by the user against the secret
    generated during setup. If verification succeeds, 2FA is enabled for the user.
    """
    
    def post(self, request):
        """
        Handle POST request to verify and confirm 2FA setup.
        
        Validates the user's TOTP code against the secret from the setup step.
        If valid, enables 2FA for the user's account and generates backup codes.
        
        Args:
            request: The HTTP request object with code in POST data
            
        Returns:
            HttpResponse: Redirect to backup codes page or back to setup with error
        """
        # Get the secret from the session
        secret = request.session.get('twofa_setup_secret')
        if not secret:
            messages.error(request, "Setup session expired. Please try again.")
            return redirect('security:twofa_setup')
        
        # Get the verification code from the form
        code = request.POST.get('code')
        if not code:
            messages.error(request, "Please enter the verification code.")
            return redirect('security:twofa_setup')
        
        # Verify the code
        if verify_totp_code(secret, code):
            # Code is valid, save the secret to the database
            with transaction.atomic():
                # Create or update the 2FA model
                twofa, created = TwoFactorAuth.objects.get_or_create(
                    user=request.user,
                    defaults={
                        'secret': secret,
                        'is_enabled': True
                    }
                )
                
                if not created:
                    twofa.secret = secret
                    twofa.is_enabled = True
                    twofa.save()
                
                # Generate backup codes if none exist
                if not twofa.backup_codes:
                    twofa.backup_codes = generate_backup_codes()
                    twofa.save()
            
            # Log the 2FA setup event
            SecurityLog.objects.create(
                user=request.user,
                event_type=SecurityLog.EVENT_2FA_ENABLED,
                description="Two-factor authentication enabled",
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Clear the setup secret from the session
            if 'twofa_setup_secret' in request.session:
                del request.session['twofa_setup_secret']
            
            messages.success(request, "Two-factor authentication has been enabled successfully!")
            
            # Redirect to backup codes page
            return redirect('security:twofa_backup_codes')
        else:
            # Invalid code
            messages.error(request, "Invalid verification code. Please try again.")
            return redirect('security:twofa_setup')


class TwoFactorBackupCodesView(LoginRequiredMixin, View):
    """
    View for displaying and managing backup codes.
    
    This view shows the user their backup codes and allows them to
    generate new ones if needed.
    """
    
    def get(self, request):
        """
        Handle GET request to display backup codes page.
        
        Retrieves and displays the user's backup codes for 2FA recovery.
        
        Args:
            request: The HTTP request object
            
        Returns:
            HttpResponse: Rendered page with backup codes
        """
        try:
            twofa = TwoFactorAuth.objects.get(user=request.user)
            backup_codes = twofa.backup_codes or []
            
            return render(request, 'security/twofa_backup_codes.html', {
                'backup_codes': backup_codes
            })
        except TwoFactorAuth.DoesNotExist:
            messages.error(request, "Two-factor authentication is not set up for your account.")
            return redirect('security:twofa_setup')


class TwoFactorManageView(LoginRequiredMixin, View):
    """
    View for managing two-factor authentication settings.
    
    This view allows users to view the status of their 2FA setup
    and provides options to enable, disable, or modify their 2FA settings.
    """
    
    def get(self, request):
        """
        Handle GET request to display 2FA management page.
        
        Shows the current status of 2FA and options for management.
        
        Args:
            request: The HTTP request object
            
        Returns:
            HttpResponse: Rendered 2FA management page
        """
        try:
            twofa = TwoFactorAuth.objects.get(user=request.user)
            is_enabled = twofa.is_enabled
            has_backup_codes = bool(twofa.backup_codes)
        except TwoFactorAuth.DoesNotExist:
            is_enabled = False
            has_backup_codes = False
        
        return render(request, 'security/twofa_manage.html', {
            'is_enabled': is_enabled,
            'has_backup_codes': has_backup_codes
        })


class TwoFactorVerifyView(View):
    """
    View for verifying two-factor authentication during login.
    
    This view is shown after the user enters their username and password
    but before they are fully logged in, if they have 2FA enabled.
    """
    
    def get(self, request):
        """
        Handle GET request to display 2FA verification page.
        
        Shows the 2FA verification form during the login process.
        
        Args:
            request: The HTTP request object
            
        Returns:
            HttpResponse: Rendered 2FA verification page or redirect if not applicable
        """
        # Check if there's a user ID in the session that needs 2FA verification
        user_id = request.session.get('twofa_user_id')
        if not user_id:
            # No user to verify, redirect to login
            messages.error(request, "Please log in first.")
            return redirect('accounts:login')
        
        try:
            # Get the user but don't authenticate yet
            user = User.objects.get(id=user_id)
            return render(request, 'security/twofa_verify.html', {
                'username': user.username
            })
        except User.DoesNotExist:
            # Invalid user ID, clear session and redirect
            if 'twofa_user_id' in request.session:
                del request.session['twofa_user_id']
            
            messages.error(request, "Authentication session expired. Please try again.")
            return redirect('accounts:login')
    
    def post(self, request):
        """
        Handle POST request to verify 2FA code.
        
        Validates the TOTP code or backup code entered by the user.
        If valid, completes the login process.
        
        Args:
            request: The HTTP request object with verification code
            
        Returns:
            HttpResponse: Redirect to next page or back to verification with error
        """
        # Check if there's a user ID in the session that needs 2FA verification
        user_id = request.session.get('twofa_user_id')
        if not user_id:
            # No user to verify, redirect to login
            messages.error(request, "Please log in first.")
            return redirect('accounts:login')
        
        try:
            # Get the user
            user = User.objects.get(id=user_id)
            
            # Get the code from the form
            code = request.POST.get('code')
            if not code:
                messages.error(request, "Please enter the verification code.")
                return redirect('security:twofa_verify')
            
            # Check if it's a backup code
            is_backup = request.POST.get('is_backup') == 'true'
            
            # Get the 2FA record
            try:
                twofa = TwoFactorAuth.objects.get(user=user)
                
                # Verify the code
                if is_backup:
                    # Verify backup code
                    is_valid = verify_backup_code(user, code)
                    code_type = "backup"
                else:
                    # Verify TOTP code
                    is_valid = verify_totp_code(twofa.secret, code)
                    code_type = "TOTP"
                
                if is_valid:
                    # Code is valid, complete login
                    complete_login_after_twofa(request, user)
                    
                    # Log the successful verification
                    SecurityLog.objects.create(
                        user=user,
                        event_type=SecurityLog.EVENT_2FA_VERIFIED,
                        description=f"Two-factor authentication verified using {code_type} code",
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    
                    # If using a backup code, notify user
                    if is_backup:
                        messages.info(request, "You used a backup code to log in. This code cannot be used again.")
                    
                    messages.success(request, f"Welcome back, {user.username}!")
                    
                    # Redirect to the originally requested page or default
                    redirect_to = request.session.get('next', 'home')
                    return redirect(redirect_to)
                else:
                    # Invalid code
                    messages.error(request, "Invalid verification code. Please try again.")
                    return redirect('security:twofa_verify')
                    
            except TwoFactorAuth.DoesNotExist:
                # 2FA not set up for this user, should not happen in normal flow
                # Clear session and redirect to login
                if 'twofa_user_id' in request.session:
                    del request.session['twofa_user_id']
                
                messages.error(request, "Two-factor authentication is not set up for your account.")
                return redirect('accounts:login')
                
        except User.DoesNotExist:
            # Invalid user ID, clear session and redirect
            if 'twofa_user_id' in request.session:
                del request.session['twofa_user_id']
            
            messages.error(request, "Authentication session expired. Please try again.")
            return redirect('accounts:login')


def disable_two_factor(request):
    """
    Disable two-factor authentication for a user.
    
    This view handles the request to disable 2FA for the current user's account.
    It requires confirmation and logs the action for security audit purposes.
    
    Args:
        request: The HTTP request object
        
    Returns:
        HttpResponse: Redirect to 2FA management page with status message
    """
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to perform this action.")
        return redirect('accounts:login')
        
    if request.method == 'POST':
        try:
            # Get the 2FA record
            twofa = TwoFactorAuth.objects.get(user=request.user)
            
            # Disable 2FA
            twofa.is_enabled = False
            twofa.save()
            
            # Log the 2FA disabled event
            SecurityLog.objects.create(
                user=request.user,
                event_type=SecurityLog.EVENT_2FA_DISABLED,
                description="Two-factor authentication disabled",
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, "Two-factor authentication has been disabled successfully.")
        except TwoFactorAuth.DoesNotExist:
            # 2FA not set up for this user
            messages.warning(request, "Two-factor authentication was not enabled for your account.")
    
    return redirect('security:twofa_manage')


def regenerate_backup_codes(request):
    """
    Regenerate backup codes for two-factor authentication.
    
    This view handles the request to generate new backup codes for the
    current user, replacing any existing backup codes.
    
    Args:
        request: The HTTP request object
        
    Returns:
        HttpResponse: Redirect to backup codes page with new codes
    """
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to perform this action.")
        return redirect('accounts:login')
        
    if request.method == 'POST':
        try:
            # Get the 2FA record
            twofa = TwoFactorAuth.objects.get(user=request.user)
            
            # Regenerate backup codes
            twofa.backup_codes = generate_backup_codes()
            twofa.save()
            
            # Log the backup codes regeneration event
            SecurityLog.objects.create(
                user=request.user,
                event_type=SecurityLog.EVENT_2FA_BACKUP_REGENERATED,
                description="Two-factor authentication backup codes regenerated",
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, "Backup codes have been regenerated successfully.")
        except TwoFactorAuth.DoesNotExist:
            # 2FA not set up for this user
            messages.error(request, "Two-factor authentication is not set up for your account.")
            return redirect('security:twofa_setup')
    
    return redirect('security:twofa_backup_codes')
