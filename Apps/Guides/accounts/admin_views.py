"""
Admin views for user role and permission management.

This module contains class-based views for administrators to manage user roles,
permissions, and account settings. These views are protected by permission
checks to ensure only authorized users can access them.
"""

from django.views.generic import ListView, UpdateView, FormView, DetailView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

from .forms_admin import RoleManagementForm, BulkRoleUpdateForm
from security.models import SecurityLog
from security.utils import get_client_ip
from security.views import is_admin, is_manager_or_admin

User = get_user_model()


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that ensures only admin users can access the view.
    
    This mixin combines LoginRequiredMixin to ensure users are authenticated
    and UserPassesTestMixin to verify they have admin privileges. It provides
    a consistent way to protect admin-only views.
    """
    
    def test_func(self):
        """
        Test if the current user is an admin.
        
        Returns:
            bool: True if user is admin, False otherwise
        """
        return is_admin(self.request.user)
        
    def handle_no_permission(self):
        """
        Handle users without admin permission.
        
        Redirects unauthorized users to the login page or displays
        an access denied message if already logged in.
        
        Returns:
            HttpResponse: Redirect to appropriate page
        """
        if self.request.user.is_authenticated:
            messages.error(self.request, "Access denied: Admin privileges required.")
            return redirect('home')
        return super().handle_no_permission()


class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that ensures only manager or admin users can access the view.
    
    This mixin combines LoginRequiredMixin to ensure users are authenticated
    and UserPassesTestMixin to verify they have manager or admin privileges.
    It provides a consistent way to protect management views.
    """
    
    def test_func(self):
        """
        Test if the current user is a manager or admin.
        
        Returns:
            bool: True if user is manager or admin, False otherwise
        """
        return is_manager_or_admin(self.request.user)
        
    def handle_no_permission(self):
        """
        Handle users without manager permission.
        
        Redirects unauthorized users to the login page or displays
        an access denied message if already logged in.
        
        Returns:
            HttpResponse: Redirect to appropriate page
        """
        if self.request.user.is_authenticated:
            messages.error(self.request, "Access denied: Manager privileges required.")
            return redirect('home')
        return super().handle_no_permission()


class UserRoleListView(AdminRequiredMixin, ListView):
    """
    View for listing all users with their roles.
    
    This view displays a paginated list of users with role information
    and provides filtering options for administrators to quickly find
    specific users based on various criteria.
    """
    model = User
    template_name = 'accounts/admin/user_role_list.html'
    context_object_name = 'users'
    paginate_by = 25
    
    def get_queryset(self):
        """
        Get the list of users with optional filtering.
        
        Applies filters based on query parameters for role, username,
        email, or name to help admins quickly find specific users.
        
        Returns:
            QuerySet: Filtered user queryset
        """
        queryset = User.objects.all().order_by('username')
        
        # Apply filters if provided
        role = self.request.GET.get('role')
        search = self.request.GET.get('search')
        
        if role:
            queryset = queryset.filter(role=role)
            
        if search:
            # Search by username, email, or name
            queryset = queryset.filter(
                Q(username__icontains=search) | 
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
            
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Add role choices and filter data to context.
        
        Adds additional context variables for rendering the template,
        including available role choices and current filter selections.
        
        Returns:
            dict: Context dictionary
        """
        context = super().get_context_data(**kwargs)
        context['role_choices'] = User.Role.choices
        context['current_role'] = self.request.GET.get('role', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context


class UserRoleUpdateView(AdminRequiredMixin, UpdateView):
    """
    View for updating a user's role and permissions.
    
    This view allows administrators to change a user's role,
    customize their permissions, and track the changes for
    security audit purposes.
    """
    model = User
    form_class = RoleManagementForm
    template_name = 'accounts/admin/user_role_update.html'
    success_url = reverse_lazy('accounts:admin_user_roles')
    
    def get_form_kwargs(self):
        """
        Provide the current admin user to the form.
        
        Adds the admin user to the form kwargs to enable
        permission-based validations in the form.
        
        Returns:
            dict: Form keyword arguments
        """
        kwargs = super().get_form_kwargs()
        kwargs['admin_user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """
        Process the valid form submission.
        
        Saves the form, logs the role change, and displays
        a success message to the admin user.
        
        Args:
            form: The validated form
            
        Returns:
            HttpResponse: Redirect to success URL
        """
        user = form.save()
        old_role = user.role
        new_role = form.cleaned_data['role']
        change_reason = form.cleaned_data['change_reason']
        
        # Log the role change
        SecurityLog.objects.create(
            user=user,
            event_type='role_change',
            description=f"Role changed from {old_role} to {new_role}",
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            extra_data={
                'changed_by': self.request.user.id,
                'old_role': old_role,
                'new_role': new_role,
                'change_reason': change_reason,
                'permissions': user.permissions
            }
        )
        
        messages.success(self.request, f"Successfully updated role for {user.username} to {user.get_role_display()}")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        """
        Add additional context for the template.
        
        Adds user activity history and permission information
        to the template context for comprehensive user management.
        
        Returns:
            dict: Context dictionary
        """
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        # Get recent security logs for this user
        context['security_logs'] = SecurityLog.objects.filter(user=user).order_by('-timestamp')[:10]
        
        # Format current permissions for display
        context['current_permissions'] = user.permissions
        
        return context


class BulkRoleUpdateView(AdminRequiredMixin, FormView):
    """
    View for updating roles for multiple users at once.
    
    This view provides a form for administrators to efficiently
    update roles for a group of users at once, with appropriate
    safeguards to prevent unauthorized or accidental mass changes.
    """
    form_class = BulkRoleUpdateForm
    template_name = 'accounts/admin/bulk_role_update.html'
    success_url = reverse_lazy('accounts:admin_user_roles')
    
    def get_form_kwargs(self):
        """
        Provide the current admin user to the form.
        
        Adds the admin user to the form kwargs to enable
        permission-based validations in the form.
        
        Returns:
            dict: Form keyword arguments
        """
        kwargs = super().get_form_kwargs()
        kwargs['admin_user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """
        Process the valid form submission.
        
        Updates roles for all selected users, logs the changes,
        and displays a success message summarizing the operation.
        
        Args:
            form: The validated form
            
        Returns:
            HttpResponse: Redirect to success URL
        """
        selected_users = form.cleaned_data['selected_users']
        new_role = form.cleaned_data['role']
        change_reason = form.cleaned_data['change_reason']
        count = 0
        
        for user in selected_users:
            if user.role != new_role:  # Only update if role is changing
                old_role = user.role
                user.role = new_role
                user.role_assigned_at = timezone.now()
                user.role_assigned_by = self.request.user
                user.save()
                count += 1
                
                # Log each role change
                SecurityLog.objects.create(
                    user=user,
                    event_type='role_change',
                    description=f"Role changed from {old_role} to {new_role} (bulk update)",
                    ip_address=get_client_ip(self.request),
                    user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                    extra_data={
                        'changed_by': self.request.user.id,
                        'old_role': old_role,
                        'new_role': new_role,
                        'bulk_update': True,
                        'change_reason': change_reason
                    }
                )
        
        messages.success(self.request, f"Successfully updated roles for {count} users")
        return super().form_valid(form)


class UserPermissionDetailView(AdminRequiredMixin, DetailView):
    """
    View for displaying detailed user permission information.
    
    This view shows comprehensive information about a user's permissions,
    role history, and related security logs to help administrators
    understand and audit user access rights.
    """
    model = User
    template_name = 'accounts/admin/user_permission_detail.html'
    context_object_name = 'user_obj'  # Use user_obj to avoid conflict with request.user
    
    def get_context_data(self, **kwargs):
        """
        Add permission details and history to context.
        
        Enhances the template context with detailed permission information,
        role change history, and other relevant user data for comprehensive
        admin review.
        
        Returns:
            dict: Context dictionary
        """
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        # Get security logs related to this user's permissions
        context['role_changes'] = SecurityLog.objects.filter(
            user=user, 
            event_type='role_change'
        ).order_by('-timestamp')
        
        # Get login history
        context['login_history'] = SecurityLog.objects.filter(
            user=user,
            event_type__in=['login_success', 'login_failed', 'logout']
        ).order_by('-timestamp')[:10]
        
        # Format permissions for readable display
        permissions = user.permissions
        context['formatted_permissions'] = permissions
        
        # Get effective permissions based on user's role
        context['role_display'] = user.get_role_display()
        
        return context
