"""
Template-based views for the accounts app.

This module contains template-based views for user authentication
and profile management that render HTML templates.
"""
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordResetForm
from django.contrib.auth.views import LoginView as BaseLoginView, PasswordResetView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render, resolve_url
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView, TemplateView, UpdateView, CreateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.views import (
    PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView,
    PasswordChangeView, PasswordChangeDoneView
)

User = get_user_model()

class LoginView(FormView):
    """
    View for user login.
    Uses the modernized login template with responsive design.
    """
    template_name = 'account/login.html'  # Updated to match the template location
    form_class = AuthenticationForm
    redirect_authenticated_user = True
    
    def get_success_url(self):
        next_url = self.request.GET.get('next')
        return next_url if next_url else reverse_lazy('core:home')
    
    def form_valid(self, form):
        """Security check complete. Log the user in."""
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        
        if user is not None:
            login(self.request, user)
            remember_me = form.cleaned_data.get('remember_me', False)
            if not remember_me:
                # Set session to expire when browser is closed
                self.request.session.set_expiry(0)
            else:
                # Session expires after 30 days
                self.request.session.set_expiry(60 * 60 * 24 * 30)
                
            messages.success(self.request, f'Welcome back, {user.get_full_name() or user.username}!')
            return super().form_valid(form)
        else:
            messages.error(self.request, 'Invalid username or password.')
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        return context
        
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['username'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Enter your email or username',
            'autofocus': 'autofocus'
        })
        form.fields['password'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': '••••••••',
        })
        return form

def logout_view(request):
    """
    View for user logout.
    """
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
    return redirect('core:home')

class RegisterView(FormView):
    """
    View for user registration.
    """
    template_name = 'account/signup.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('core:home')
    
    def get_form(self, form_class=None):
        """Return an instance of the form to be used in this view."""
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(self.request.POST or None)
    
    def form_valid(self, form):
        """If the form is valid, save the user and log them in."""
        user = form.save()
        login(self.request, user)
        messages.success(self.request, f'Account created successfully! Welcome, {user.username}!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """If the form is invalid, render the invalid form with errors."""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field.title()}: {error}")
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        """
        Add extra context data to be passed to the template.
        """
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        return context


class ProfileView(LoginRequiredMixin, UpdateView):
    """
    View for user profile management.
    """
    template_name = 'account/profile.html'
    model = User
    fields = ['first_name', 'last_name', 'email']
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self, queryset=None):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Your profile has been updated successfully.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'My Profile'
        return context


class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view with template support."""
    template_name = 'account/password_reset.html'
    email_template_name = 'account/email/password_reset_email.html'
    subject_template_name = 'account/email/password_reset_subject.txt'
    success_url = reverse_lazy('account_reset_password_done')


class CustomPasswordResetDoneView(PasswordResetDoneView):
    """Custom password reset done view."""
    template_name = 'account/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Custom password reset confirm view."""
    template_name = 'account/password_reset_confirm.html'
    success_url = reverse_lazy('account_reset_password_complete')


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """Custom password reset complete view."""
    template_name = 'account/password_reset_complete.html'


class CustomPasswordChangeView(PasswordChangeView):
    """Custom password change view."""
    template_name = 'account/password_change.html'
    success_url = reverse_lazy('account_change_password_done')


class CustomPasswordChangeDoneView(PasswordChangeDoneView):
    """Custom password change done view."""
    template_name = 'account/password_change_done.html'
