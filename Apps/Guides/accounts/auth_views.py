"""
Authentication views for the accounts app.

This module contains view functions and classes for user authentication
including login, registration, password reset, and account verification.
"""

import logging
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView, PasswordChangeView,
    PasswordChangeDoneView
)
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, FormView, CreateView, UpdateView, ListView
from django.conf import settings
from django.db import transaction, IntegrityError

from .forms import (
    RegisterForm, LoginForm, CustomPasswordResetForm,
    CustomSetPasswordForm, CustomPasswordChangeForm, GuideApplicationForm
)
from .models import User, UserProfile, UserPreference, GuideApplication
from .utils import get_client_ip, complete_login_after_twofa

# Import security models and utilities
from security.models import TwoFactorAuth, SecurityLog, FailedLoginAttempt
from security.utils import get_client_ip, complete_login_after_twofa

# Set up logging
logger = logging.getLogger(__name__)

class UserLoginView(LoginView):
    """
    Custom login view extending Django's built-in LoginView.
    
    This view handles user authentication with custom form and template,
    providing role-based redirection after login. It also integrates with
    the two-factor authentication system and security logging.
    
    The view supports authentication by either username or email and stores
    the user's role in the session for role-based UI customization.
    """
    form_class = LoginForm
    
    def get_success_url(self):
        """
        Determine the URL to redirect to after successful login.
        
        This method checks for a 'next' parameter in the URL and redirects there if present.
        Otherwise, it performs role-based redirection based on the user's assigned role.
        
        Returns:
            str: URL to redirect to based on user's role and context
        """
        user = self.request.user
        
        # Check if there's a 'next' parameter in the URL
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
            
        # Role-based redirection using the direct role property
        if user.is_superuser or user.role == user.Role.ADMIN or user.role == user.Role.MANAGER:
            return reverse_lazy('admin:index')  # Both admins and managers go to admin
        elif user.role == user.Role.LOCAL_GUIDE:
            # Temporarily redirecting guides to home page until guide dashboard is implemented
            return reverse_lazy('core:home')
        # Default redirect for travelers and other roles
        return reverse_lazy('core:home')
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to ensure CSRF cookie is set before processing the form.
        """
        # Ensure CSRF cookie is set
        request.META["CSRF_COOKIE_USED"] = True
        return super().dispatch(request, *args, **kwargs)
        
    def form_valid(self, form):
        """
        Process valid form submission.
        
        Checks if two-factor authentication is enabled for the user:
        - If enabled: Stores user ID in session and redirects to 2FA verification
        - If disabled: Completes login normally
        
        In both cases, security events are logged appropriately.
        
        Args:
            form: The validated login form
            
        Returns:
            HttpResponse: Redirect to 2FA verification or success URL
        """
        user = form.get_user()
        
        # Check if 2FA is enabled for this user
        try:
            twofa = TwoFactorAuth.objects.get(user=user)
            if twofa.is_enabled:
                # Store user ID in session for 2FA verification
                self.request.session['twofa_user_id'] = str(user.id)
                self.request.session['twofa_remember_me'] = form.cleaned_data.get('remember_me', False)
                
                # Log the 2FA required event
                SecurityLog.objects.create(
                    user=user,
                    event_type=SecurityLog.EVENT_2FA_REQUIRED,
                    description="Two-factor authentication required for login",
                    ip_address=get_client_ip(self.request),
                    user_agent=self.request.META.get('HTTP_USER_AGENT', '')
                )
                
                # Don't log in yet, redirect to 2FA verification
                return redirect('security:twofa_verify')
        except TwoFactorAuth.DoesNotExist:
            # 2FA not set up for this user, continue with normal login
            pass
            
        # If we get here, either 2FA is not enabled or the model doesn't exist
        # Clear any failed login attempts
        FailedLoginAttempt.objects.filter(username=user.username).delete()
        
        # Log successful login
        SecurityLog.objects.create(
            user=user,
            event_type=SecurityLog.EVENT_LOGIN,  # Using the correct constant
            description=f"User {user.username} logged in successfully",
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            level=SecurityLog.LEVEL_INFO
        )
        
        messages.success(self.request, f"Welcome back, {user.username}!")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """
        Process invalid form submission.
        
        Records failed login attempt and adds an error message.
        Checks for account lockout conditions.
        
        Args:
            form: The invalid login form
            
        Returns:
            HttpResponse: Rendered login page with errors
        """
        username = form.cleaned_data.get('username')
        
        if username:
            # Record failed login attempt
            ip_address = get_client_ip(self.request)
            
            # Check if the account is already locked
            is_locked, _ = FailedLoginAttempt.is_account_locked(username, ip_address)
            
            if not is_locked:
                # Record a new failed attempt
                is_locked, minutes_until_unlock = FailedLoginAttempt.record_failure(
                    username=username,
                    ip_address=ip_address,
                    user_agent=self.request.META.get('HTTP_USER_AGENT', '')
                )
                
                # Log the failed login event
                # Try to get the user to associate with the log entry
                user = None
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    pass  # User doesn't exist, log with user=None
                    
                SecurityLog.objects.create(
                    event_type=SecurityLog.EVENT_LOGIN_FAIL,
                    description=f"Failed login attempt for username: {username}",
                    ip_address=ip_address,
                    user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                    user=user,  # This can be None if user doesn't exist
                    level=SecurityLog.LEVEL_WARNING
                )
                
                # Check if this attempt triggered a lockout
                if is_locked:
                    messages.error(
                        self.request, 
                        "Too many failed login attempts. Your account is temporarily locked. "
                        "Please try again later or reset your password."
                    )
                    
                    # Log the account lockout event
                    SecurityLog.objects.create(
                        event_type=SecurityLog.EVENT_SECURITY_SCAN,  # Using existing event type
                        description=f"Account locked after multiple failed attempts: {username}",
                        ip_address=ip_address,
                        user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                        username=username
                    )
                    
                    return redirect('accounts:password_reset')
            else:
                # Account is already locked
                messages.error(
                    self.request, 
                    "Your account is temporarily locked due to too many failed login attempts. "
                    "Please try again later or reset your password."
                )
                
                # Log the blocked login attempt
                SecurityLog.objects.create(
                    event_type=SecurityLog.EVENT_LOGIN_BLOCKED,
                    description=f"Blocked login attempt for locked account: {username}",
                    ip_address=ip_address,
                    user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                    username=username
                )
                
                return redirect('accounts:password_reset')
        
        messages.error(self.request, "Invalid username or password.")
        return super().form_invalid(form)


class UserRegisterView(FormView):
    """
    Custom view for user registration.
    
    Handles both GET requests to display the registration form
    and POST requests to process new user registrations.
    Integrates with security logging system for audit trail.
    Sends welcome email and shows success page after registration.
    
    After successful form validation, this view:
    1. Creates a new user with TRAVELER role
    2. Sets up user profile and preferences
    3. Logs the registration event
    4. Sends a welcome email
    5. Logs the user in automatically
    6. Shows a success confirmation page
    """
    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_template_name = 'accounts/registration_success.html'  # Template to render on success
    
    # Fallback URL if direct template rendering fails
    success_url = reverse_lazy('core:home')  # Redirect after successful registration
    
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display registration form.
        
        Redirects already authenticated users to home page.
        Initializes a new empty registration form for new users.
        
        Args:
            request: The HTTP request object containing session data
            
        Returns:
            HttpResponse: Rendered registration form or redirect to home
        """
        if request.user.is_authenticated:
            messages.info(request, 'You are already logged in.')
            return redirect('home')
            
        # Initialize form with any GET parameters
        form = self.form_class()
        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)
        
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to process registration form.
        
        Validates form input including username, first name, last name, email,
        and password fields. Creates a new user with these fields if valid,
        assigns a role based on the registration path, authenticates the user 
        for immediate login after registration, and logs the user creation event 
        in the security logs.
        
        Supports both regular form submissions and AJAX requests with JSON responses.
        
        Args:
            request: The HTTP request object containing form data
            
        Returns:
            HttpResponse: 
                - For AJAX: JSON response with success/error status
                - For regular form: Redirect to home page or rendered form with errors
        """
        form = self.form_class(request.POST, request.FILES)
        
        # Check if this is an AJAX request
        # Safely access headers which might not exist in some environments
        try:
            is_ajax = request.headers and request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        except (AttributeError, TypeError):
            # Fallback if headers attribute is missing or not a dict-like object
            is_ajax = request.META.get('HTTP_X_REQUESTED_WITH', '') == 'XMLHttpRequest'
        
        if form.is_valid():
            try:
                # All new registrations are set as TRAVELER by default
                selected_role = User.Role.TRAVELER
                
                # Log attempt if someone is trying to register as a guide directly
                # First check if extra_context exists and is not None before trying to access its attributes
                is_guide_registration = False
                if hasattr(self, 'extra_context') and self.extra_context is not None:
                    # Now safely get the is_guide_registration flag with a default of False
                    is_guide_registration = self.extra_context.get('is_guide_registration', False)
                
                if is_guide_registration:
                    # Log warning about direct guide registration attempt
                    logger.warning(f"Direct guide registration attempt detected from IP: {get_client_ip(request)}")
                    # For non-AJAX requests, inform user they're registered as regular user
                    if not is_ajax:
                        messages.info(request, "You have been registered as a regular user. To become a local guide, please apply through your profile settings.")
                
                # Create the user with form data and assigned role
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password1'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    role=selected_role,
                    is_active=True,
                    role_assigned_at=timezone.now()
                )
                
                # If a logged-in admin is creating the user, track who assigned the role
                if request.user.is_authenticated and request.user.is_admin:
                    user.role_assigned_by = request.user
                    user.save()
                
                # Create user profile with default preferences
                # Note: UserProfile uses is_verified field instead of email_verified
                try:
                    # Check if profile already exists for this user to avoid duplicate key errors
                    # This may happen if a transaction was partially completed in a previous attempt
                    if not UserProfile.objects.filter(user=user).exists():
                        UserProfile.objects.create(
                            user=user,
                            is_verified=False,  # Will be set to True after email verification
                            phone_number='',
                            address='',
                            bio='',
                            profile_picture=None
                        )
                        logger.info(f"Created profile for user: {user.username}")
                    else:
                        logger.info(f"Profile already exists for user: {user.username}, skipping creation")
                except Exception as e:
                    logger.error(f"Error creating profile for user {user.username}: {str(e)}")
                    # If profile creation fails, we may need to delete the user to avoid orphaned users
                    # However, we'll proceed with registration and handle this in maintenance
                
                # Get marketing preferences from form data with safe defaults
                marketing_emails = form.cleaned_data.get('marketing_emails', False)
                newsletter_subscription = form.cleaned_data.get('newsletter_subscription', False)
                
                # Create default user preferences with marketing preferences
                # This section creates personalization and communication preferences for the user
                try:
                    # Check if preferences already exist to avoid duplication errors
                    if not UserPreference.objects.filter(user=user).exists():
                        # Set default values with marketing preferences from form
                        UserPreference.objects.create(
                            user=user,
                            language='en',        # Default language setting
                            currency='USD',       # Default currency for prices
                            timezone='UTC',       # Default timezone for dates/times
                            email_notifications=True,  # Enable essential notifications
                            sms_notifications=False,   # Disable SMS by default
                            marketing_emails=bool(marketing_emails),  # From form
                            newsletter_subscription=bool(newsletter_subscription)  # From form
                        )
                        logger.info(f"Created preferences for user: {user.username}")
                    else:
                        logger.info(f"Preferences already exist for user: {user.username}, updating marketing settings")
                        # Update existing preferences with new marketing choices
                        prefs = UserPreference.objects.get(user=user)
                        prefs.marketing_emails = bool(marketing_emails)
                        prefs.newsletter_subscription = bool(newsletter_subscription)
                        prefs.save()
                except Exception as e:
                    logger.error(f"Error creating user preferences for {user.username}: {str(e)}")
                    # Continue with registration even if preferences can't be set
                    # These can be created later during profile completion
                
                # Log the user creation event with role information
                # Using EVENT_USER_CREATED instead of EVENT_USER_SIGNUP (which doesn't exist)
                try:
                    SecurityLog.objects.create(
                        user=user,
                        event_type=SecurityLog.EVENT_USER_CREATED,  # Use the correct event type constant
                        level=SecurityLog.LEVEL_INFO,  # Add appropriate security level
                        description=f"New user registered: {user.username} ({user.get_full_name() or user.username}) with role {user.role}",
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    )
                    logger.info(f"Logged registration event for user: {user.username}")
                except Exception as e:
                    # Log error but continue with registration
                    logger.error(f"Failed to create security log for registration: {str(e)}")
                    # This shouldn't block user registration
                
                # Authenticate and log the user in
                user = authenticate(
                    username=form.cleaned_data['username'],
                    password=form.cleaned_data['password1']
                )
                
                if user is not None:
                    login(request, user)
                    
                    # Store role in session for role-based UI customization
                    request.session['user_role'] = user.role
                    
                    # Log successful login after registration
                    # This helps track the user journey for security auditing
                    try:
                        SecurityLog.objects.create(
                            user=user,
                            event_type=SecurityLog.EVENT_LOGIN,  # Use EVENT_LOGIN instead of EVENT_LOGIN_SUCCESS
                            level=SecurityLog.LEVEL_INFO,       # Set appropriate log level
                            description="Initial login after registration",
                            ip_address=get_client_ip(request),
                            user_agent=request.META.get('HTTP_USER_AGENT', '')
                        )
                        logger.info(f"Logged initial login for new user: {user.username}")
                    except Exception as e:
                        # Log error but don't block the registration flow
                        logger.error(f"Failed to create security log for initial login: {str(e)}")
                        # Not critical, user can still proceed
                    
                    # Send welcome email (with detailed HTML formatting)
                    # This is handled in a try-except block so that email failures
                    # don't prevent successful registration
                    try:
                        # Safely get the user's name for the email greeting
                        # Use username as fallback if first_name is empty
                        greeting_name = user.first_name if user.first_name else user.username
                        
                        # Prepare email content with HTML formatting for better appearance
                        subject = 'Welcome to TravelGuide!'
                        
                        # Create plain text message for email clients that don't support HTML
                        plain_message = f'Hi {greeting_name},\n\nThank you for registering with TravelGuide. We\'re excited to have you on board!\n\nBest regards,\nThe TravelGuide Team'
                        
                        # Create HTML message with formatting, colors, and styling
                        # Using indigo/violet color scheme consistent with the site design
                        html_message = f'''
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <style>
                                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                                .header {{ background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                                .content {{ background-color: #f9fafb; padding: 20px; border-radius: 0 0 5px 5px; }}
                                .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #6b7280; }}
                                .button {{ display: inline-block; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white; text-decoration: none; padding: 10px 20px; border-radius: 5px; margin: 20px 0; }}
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <div class="header">
                                    <h1>Welcome to TravelGuide!</h1>
                                </div>
                                <div class="content">
                                    <p>Hi {greeting_name},</p>
                                    <p>Thank you for registering with TravelGuide. We're excited to have you on board!</p>
                                    <p>With TravelGuide, you can:</p>
                                    <ul>
                                        <li>Discover amazing destinations around the world</li>
                                        <li>Book tours with local guides</li>
                                        <li>Create personalized travel itineraries</li>
                                        <li>Connect with fellow travelers</li>
                                    </ul>
                                    <p>Get started by exploring our popular destinations or completing your profile for personalized recommendations.</p>
                                    <div style="text-align: center;">
                                        <a href="{request.build_absolute_uri('/')}" class="button">Start Exploring</a>
                                    </div>
                                </div>
                                <div class="footer">
                                    <p> {timezone.now().year} TravelGuide. All rights reserved.</p>
                                </div>
                            </div>
                        </body>
                        </html>
                        '''
                        
                        # Get the sender email from settings with fallback
                        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@travelguide.com')
                        # Ensure we have a valid recipient email
                        recipient_list = [user.email] if user.email else []
                        
                        # Skip sending if no valid recipients
                        if not recipient_list:
                            logger.warning(f"No valid email address for welcome email to user {user.username}")
                            # Continue with registration
                        else:
                            # Send the actual email with both plain text and HTML versions
                            # The email client will display the HTML version if supported
                            try:
                                # Try to use EmailMultiAlternatives for HTML email
                                from django.core.mail import EmailMultiAlternatives
                                email = EmailMultiAlternatives(
                                    subject,
                                    plain_message,
                                    from_email,
                                    recipient_list
                                )
                                email.attach_alternative(html_message, "text/html")
                                email.send()
                                logger.info(f"HTML welcome email sent to {user.email}")
                            except ImportError:
                                # Fallback to plain text email if EmailMultiAlternatives is not available
                                send_mail(
                                    subject,
                                    plain_message,
                                    from_email,
                                    recipient_list,
                                )
                                logger.info(f"Plain text welcome email sent to {user.email}")
                    except Exception as e:
                        # Log email sending errors but continue with registration
                        # This ensures users can still register even if email sending fails
                        logger.error(f"Error sending welcome email to {user.email if user.email else 'unknown'}: {str(e)}")
                        # Add detailed exception info for debugging
                        import traceback
                        logger.debug(f"Email error traceback: {traceback.format_exc()}")
                        # Note: We intentionally continue with the registration process despite email errors
                    
                    # Store the newly registered user's ID in session for the success page
                    # This allows the registration_success view to retrieve the user details
                    # and display personalized welcome information
                    request.session['registered_user_id'] = user.id
                    
                    # Log successful registration with redirect destination
                    logger.info(f"Registration successful for {user.username} - Redirecting to success page")
                    
                    # Handle AJAX response with success data and redirect information
                    # For AJAX requests, we return a JSON response with user data and redirect URL
                    if is_ajax:
                        return JsonResponse({
                            'success': True,
                            'message': 'Registration successful!',
                            # Direct users to the registration success page for better onboarding experience
                            'redirect_url': reverse('accounts:registration_success'),
                            # Include user information for client-side personalization
                            'user': {
                                'id': user.id,
                                'username': user.username,
                                'email': user.email,
                                'first_name': user.first_name,
                                'last_name': user.last_name,
                                'role': user.role
                            }
                        })
                    
                    # Handle regular form submission with success message and redirect
                    messages.success(request, f"Welcome to TravelGuide, {user.first_name or user.username}!")
                    # Redirect to the dedicated success page rather than home for better user experience
                    # This allows us to show welcome information, next steps, and verification instructions
                    return redirect('accounts:registration_success')
                
            except Exception as e:
                # Log the full error details for debugging
                error_msg = f"An error occurred during registration: {str(e)}"
                logger.error(error_msg)
                
                # Handle AJAX requests with detailed error information
                if is_ajax:
                    # Format error for JSON response using a consistent structure
                    # The '__all__' key is used for non-field-specific errors
                    return JsonResponse({
                        'success': False,
                        'errors': {
                            '__all__': [
                                {
                                    'message': error_msg,
                                    'code': 'registration_error'
                                }
                            ]
                        }
                    }, status=400)
                
                # For regular form submission, add a user-friendly error message
                # and re-render the form
                messages.error(request, "An error occurred during registration. Please try again.")
                return render(request, self.template_name, {'form': form})
        
        # If form is invalid, handle AJAX and regular form submissions differently
        if is_ajax:
            # Format errors for JSON response
            # Handle potential edge cases where errors might be None or not have get_json_data
            try:
                # Convert form errors to JSON-serializable format
                if hasattr(form.errors, 'get_json_data'):
                    errors_data = form.errors.get_json_data()
                else:
                    # Fallback to basic error dictionary if get_json_data is not available
                    errors_data = {field: [{'message': str(error), 'code': 'invalid'} 
                                 for error in errors] 
                                 for field, errors in form.errors.items()}
            except Exception as e:
                # If any error occurs during error formatting, use a simple error message
                logger.error(f"Error formatting form errors: {str(e)}")
                errors_data = {'__all__': [{'message': 'An error occurred processing your form. Please try again.', 
                                         'code': 'processing_error'}]}
            
            # Return the formatted errors in a consistent JSON structure
            return JsonResponse({
                'success': False,
                'errors': errors_data
            }, status=400)
            
        # For regular form submission, re-render the form with errors
        # This uses Django's built-in form error handling
        return render(request, self.template_name, {'form': form})


class CustomPasswordResetView(PasswordResetView):
    """
    Custom password reset request view.
    
    Extends Django's PasswordResetView with custom form, template, and 
    email template for a more integrated user experience.
    
    Uses the reusable email utility for consistent styling and error handling.
    """
    template_name = 'accounts/password_reset.html'
    # Keep email_template_name as fallback but use custom function instead
    email_template_name = 'accounts/password_reset_email.html'
    form_class = CustomPasswordResetForm
    success_url = reverse_lazy('accounts:password_reset_done')
    
    def form_valid(self, form):
        """
        Override form_valid to use our custom email sending function.
        
        This provides consistent email styling and error handling.
        
        Args:
            form: The validated password reset form
            
        Returns:
            HttpResponse: Redirect to success URL
        """
        # Get active users with this email
        email = form.cleaned_data["email"]
        active_users = form.get_users(email)
        site_domain = self.request.get_host()
        use_https = self.request.is_secure()
        
        for user in active_users:
            try:
                # Use our custom password reset email function
                from .utils import send_password_reset_email
                send_password_reset_email(user, site_domain, use_https)
                logger.info(f"Password reset email sent to {user.email}")
            except Exception as e:
                logger.error(f"Error sending password reset email to {user.email}: {str(e)}", exc_info=True)
                # Continue the loop to attempt sending to other matching users if any
        
        # Continue with Django's password reset flow
        return super().form_valid(form)


class UserPasswordResetView(PasswordResetView):
    """
    Custom password reset request view.
    
    Extends Django's PasswordResetView with custom form, template, and 
    email template for a more integrated user experience.
    
    Uses the reusable email utility for consistent styling and error handling.
    """
    template_name = 'accounts/password_reset.html'
    # Keep email_template_name as fallback but use custom function instead
    email_template_name = 'accounts/password_reset_email.html'
    form_class = CustomPasswordResetForm
    success_url = reverse_lazy('accounts:password_reset_done')
    
    def form_valid(self, form):
        """
        Process valid form submission.
        
        Uses our custom email sending function and adds a success message.
        
        Args:
            form: The validated password reset form
            
        Returns:
            HttpResponse: Redirect to success URL
        """
        # Get active users with this email
        email = form.cleaned_data["email"]
        active_users = form.get_users(email)
        site_domain = self.request.get_host()
        use_https = self.request.is_secure()
        
        for user in active_users:
            try:
                # Use our custom password reset email function
                from .utils import send_password_reset_email
                send_password_reset_email(user, site_domain, use_https)
                logger.info(f"Password reset email sent to {user.email}")
            except Exception as e:
                logger.error(f"Error sending password reset email to {user.email}: {str(e)}", exc_info=True)
                # Continue the loop to attempt sending to other matching users if any
        
        # Add success message
        messages.success(self.request, "Password reset instructions have been sent to your email.")
        
        # Continue with Django's password reset flow
        return super().form_valid(form)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    """
    Custom view shown after a password reset request is sent.
    
    Extends Django's PasswordResetDoneView with custom template.
    """
    template_name = 'accounts/password_reset_done.html'


class UserPasswordResetDoneView(PasswordResetDoneView):
    """
    Custom view shown after a password reset request is sent.
    
    Extends Django's PasswordResetDoneView with custom template.
    """
    template_name = 'accounts/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """
    Custom view to handle password reset confirmation links.
    
    Extends Django's PasswordResetConfirmView with custom form and template.
    """
    template_name = 'accounts/password_reset_confirm.html'
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy('accounts:password_reset_complete')


class UserPasswordResetConfirmView(PasswordResetConfirmView):
    """
    Custom view to handle password reset confirmation links.
    
    Extends Django's PasswordResetConfirmView with custom form and template.
    """
    template_name = 'accounts/password_reset_confirm.html'
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy('accounts:password_reset_complete')
    
    def form_valid(self, form):
        """
        Process valid form submission.
        
        Adds a success message after successful password reset.
        
        Args:
            form: The validated password reset form
            
        Returns:
            HttpResponse: Redirect to success URL
        """
        messages.success(self.request, "Your password has been successfully reset!")
        return super().form_valid(form)


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """
    Custom view shown after a password has been successfully reset.
    
    Extends Django's PasswordResetCompleteView with custom template.
    """
    template_name = 'accounts/password_reset_complete.html'


class UserPasswordResetCompleteView(PasswordResetCompleteView):
    """
    Custom view shown after a password has been successfully reset.
    
    Extends Django's PasswordResetCompleteView with custom template.
    """
    template_name = 'accounts/password_reset_complete.html'


class UserLogoutView(LogoutView):
    """
    Custom logout view extending Django's built-in LogoutView.
    
    This view handles user logout with a custom redirect and success message.
    It supports both GET and POST requests for better compatibility.
    """
    # Redirect to home page after logout
    next_page = 'core:home'
    http_method_names = ['get', 'post']  # Allow both GET and POST
    
    def dispatch(self, request, *args, **kwargs):
        """
        Process the logout request and add a success message.
        
        This method handles both GET and POST requests for logout functionality.
        It ensures proper logout and displays a success message to the user.
        
        Args:
            request: The HTTP request object
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            HttpResponse: Redirect to next_page with success message
        """
        # Add logout success message if user is authenticated
        if request.user.is_authenticated:
            messages.success(request, "You have been successfully logged out.")
        
        # Call the parent class's dispatch method to handle the actual logout
        response = super().dispatch(request, *args, **kwargs)
        
        # Ensure the session is properly cleared
        if hasattr(request, 'session'):
            request.session.flush()
        
        return response


class UserPasswordChangeView(PasswordChangeView):
    """
    Custom password change view extending Django's built-in PasswordChangeView.
    
    This view handles user password changes with custom form and template,
    providing a more tailored user experience.
    """
    form_class = CustomPasswordChangeForm
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('accounts:password_change_done')
    
    def form_valid(self, form):
        """
        Process valid form submission.
        
        Adds a success message after successful password change.
        
        Args:
            form: The validated password change form
            
        Returns:
            HttpResponse: Redirect to success URL
        """
        messages.success(self.request, "Your password has been successfully changed!")
        return super().form_valid(form)


class UserPasswordChangeDoneView(PasswordChangeDoneView):
    """
    Custom view shown after a password has been successfully changed.
    
    Extends Django's PasswordChangeDoneView with custom template.
    """
    template_name = 'accounts/password_change_done.html'


class GuideApplicationView(LoginRequiredMixin, FormView):
    """
    View for users to submit applications to become a local guide.
    
    This view handles the guide application process where regular users
    can apply to become local guides by submitting necessary documents
    and information for admin review. Users must be logged in to apply.
    
    The process follows these steps:
    1. User submits application with government ID and other required info
    2. Application is saved with PENDING status
    3. Admins/managers review applications and approve/reject them
    4. If approved, user role is updated to LOCAL_GUIDE
    
    Attributes:
        form_class: The form used for guide application submissions
        template_name: The HTML template for rendering the application form
        success_url: URL to redirect to after successful submission
    
    Flow Control:
        - Prevents duplicate submissions (users can only have one active application)
        - Handles AJAX and non-AJAX form submissions differently
        - Sends notification emails to both admins and the applicant
    """
    form_class = GuideApplicationForm
    template_name = 'accounts/guide_application.html'
    success_url = reverse_lazy('accounts:guide_application_submitted')
    
    def get_form_kwargs(self):
        """
        Pass the current user to the form.
        
        This ensures the application is associated with the logged-in user.
        The user object is passed to the form for validation purposes and
        to check for existing applications from this user.
        
        Returns:
            dict: Form keyword arguments including the current user
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display guide application form.
        
        For authenticated users, shows the guide application form.
        For unauthenticated users, redirects to login page with a warning message.
        This extra security check complements the LoginRequiredMixin to ensure
        proper feedback is provided to users.
        
        Args:
            request: The HTTP request object containing session data
            *args: Variable length argument list passed to parent method
            **kwargs: Arbitrary keyword arguments passed to parent method
            
        Returns:
            HttpResponse: Rendered application form or redirect to login
        """
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in to apply as a guide.")
            return redirect('accounts:login')
            
        return super().get(request, *args, **kwargs)
        
    def get_object(self):
        """
        Retrieve the guide application for the current user.
        
        This method is used by both admin review flows and user submission flows.
        For review flows, it gets an existing application or raises 404.
        For submission flows, it checks if the user is creating a new application
        or updating an existing one.
        
        The method differentiates between POST requests for new submissions 
        (without 'action' parameter) and admin review actions (with 'action' parameter).
        
        Returns:
            GuideApplication: The guide application for the current user if it exists
            None: If creating a new application and no existing application found
            
        Raises:
            Http404: If no application exists for the user and this is an admin review flow
        """
        # Check if this is a POST request for submitting a new application
        if self.request.method == 'POST' and 'action' not in self.request.POST:
            # For new application submission, don't try to get an existing object
            # The post() method will create a new one
            try:
                return GuideApplication.objects.get(user=self.request.user)
            except GuideApplication.DoesNotExist:
                # Return None if we're creating a new application
                return None
        
        # Otherwise, this is likely an admin trying to review an application
        # So we should return a 404 if it doesn't exist
        return get_object_or_404(GuideApplication, user=self.request.user)
        
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to process guide application form.
        
        This method handles the complete guide application submission process:
        1. Validates user authentication
        2. Checks for existing applications to prevent duplicates
        3. Validates form data
        4. Creates and saves the application with PENDING status
        5. Sends notification emails to admins and the user
        6. Provides appropriate feedback via messages framework
        7. Redirects to success page or returns form with errors
        
        Security checks are implemented to prevent unauthorized submissions
        and duplicate applications.
        
        Args:
            request: The HTTP request object containing form data
            *args: Variable length argument list passed to parent method
            **kwargs: Arbitrary keyword arguments passed to parent method
            
        Returns:
            HttpResponse: Redirect to success page or rendered form with errors
        """
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in to submit a guide application.")
            return redirect('accounts:login')
            
        # Check if user already has a pending or approved application
        existing_application = GuideApplication.objects.filter(
            user=request.user,
            status__in=['PENDING', 'APPROVED']
        ).order_by('-application_date').first()
        
        if existing_application:
            if existing_application.status == 'PENDING':
                messages.info(request, "You already have a pending guide application.")
            else:
                messages.info(request, "Your guide application has already been approved.")
            return redirect('accounts:profile')
            
        form = self.get_form()
        if not form.is_valid():
            return self.form_invalid(form)
            
        # Process the form and create guide application
        application = form.save(commit=False)
        application.user = request.user
        application.status = 'PENDING'
        
        # Make sure we save the application to the database and handle any potential errors
        try:
            application.save()
            logger.info(f"Guide application created successfully for user {request.user.id}: {application.id}")
            
            # Debug log to verify application was created with an ID
            logger.debug(f"Application details - ID: {application.id}, User: {application.user.username}, Status: {application.status}")
            
            # Send notification to admin about the new application submission
            # This helps ensure timely review of new applications
            try:
                send_admin_notification(
                    subject=f"New Guide Application from {request.user.get_full_name() or request.user.username}",
                    message="A new guide application has been submitted. Please review it in the admin panel.",
                    url=reverse('admin:accounts_guideapplication_change', args=[application.id])
                )
                logger.info(f"Admin notification sent for guide application {application.id}")
            except Exception as e:
                # Log the error but continue with the process
                logger.error(f"Failed to send admin notification: {str(e)}", exc_info=True)
            
            # Send confirmation email to the user using centralized email utility
            from .utils import send_guide_application_confirmation
            email_sent = False
            try:
                email_sent = send_guide_application_confirmation(request.user, application)
                if email_sent:
                    logger.info(f"Guide application confirmation email sent to {request.user.email} for application {application.id}")
                else:
                    logger.warning(f"Failed to send guide application confirmation email to {request.user.email}")
            except Exception as e:
                logger.error(f"Error sending guide application confirmation email: {str(e)}", exc_info=True)
            
            # Show different success message based on whether email was sent successfully
            if email_sent:
                messages.success(
                    request, 
                    "Your guide application has been submitted successfully! We'll review it soon. A confirmation email has been sent to your registered email address.",
                    extra_tags='bg-green-100 text-green-800 border-green-200'
                )
            else:
                messages.success(
                    request, 
                    "Your guide application has been submitted successfully! We'll review it soon. We tried to send a confirmation email, but there was an issue with our email system. Please check your application status in your profile.",
                    extra_tags='bg-green-100 text-green-800 border-green-200'
                )
            return redirect(self.get_success_url())
            
        except Exception as e:
            logger.error(f"Failed to save guide application for user {request.user.id}: {str(e)}", exc_info=True)
            messages.error(
                request,
                "There was an error submitting your application. Please try again or contact support.",
                extra_tags='bg-red-100 text-red-800 border-red-200'
            )
            return self.form_invalid(form)
            
    def form_invalid(self, form):
        """
        Handle invalid form submission with AJAX support.
        
        This method provides specialized handling for form validation failures
        based on the request type:
        
        - For AJAX requests: Returns a JSON response with detailed error information
          that can be processed by frontend JavaScript for dynamic user feedback
        - For regular form submissions: Calls the parent class method to render the
          template with form errors displayed in the UI
        
        The method also logs form validation failures for debugging purposes.
        
        Args:
            form: The invalid form instance containing validation errors
            
        Returns:
            HttpResponse: JSON response with errors for AJAX, or rendered form for regular requests
        """
        logger.warning("Form validation failed")
        
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # For AJAX requests, return JSON with form errors
            return JsonResponse({
                'success': False,
                'errors': form.errors.get_json_data(),
                'message': 'Please correct the errors below.'
            }, status=400)
            
        # For regular form submissions, use the default behavior
        return super().form_invalid(form)
        
    def form_valid(self, form):
        """
        Handle form_valid in the standard FormView way.
        
        This method is intentionally kept simple since the post() method already
        handles all the guide application submission logic. This is kept as a
        fallback for standard FormView behavior if needed.
        
        Args:
            form: The validated form instance
            
        Returns:
            HttpResponse: Redirect to success URL
        """
        return super().form_valid(form)
    
    def test_func(self):
        """
        Check if the current user has permission to review applications.
        
        Only admins and managers can review guide applications.
        
        Returns:
            bool: True if user is an admin or manager, False otherwise
        """
        return self.request.user.is_authenticated and self.request.user.role in [User.Role.ADMIN, User.Role.MANAGER]
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.
        
        For new guide applications, includes the current user as the applicant.
        
        Returns:
            dict: Context dictionary with form and user data
        """
        context = super().get_context_data(**kwargs)
        
        # Set the current user as the applicant
        context['applicant'] = self.request.user if self.request.user.is_authenticated else None
        
        # Add form to context if not already present
        if 'form' not in context:
            context['form'] = self.get_form()
            
        # Add any existing application for the user
        if self.request.user.is_authenticated:
            try:
                context['existing_application'] = GuideApplication.objects.get(user=self.request.user)
            except GuideApplication.DoesNotExist:
                context['existing_application'] = None
                
        return context


class GuideApplicationSuccessView(LoginRequiredMixin, TemplateView):
    """
    View shown after a guide application is successfully submitted.
    
    This view displays a confirmation message and next steps for the user
    after their guide application is successfully submitted.
    """
    template_name = 'accounts/guide_application_submitted.html'
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.
        
        Args:
            **kwargs: Additional keyword arguments
            
        Returns:
            dict: The context data for the template
        """
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Application Submitted'
        
        # Add expected review timeframe
        context['review_timeframe'] = '3-5 business days'
        return context


class GuideApplicationReviewView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View for reviewing, approving, or rejecting guide applications.
    
    This view allows admin users to review pending guide applications and either
    approve or reject them with feedback.
    """
    model = GuideApplication
    template_name = 'accounts/guide_application_review.html'
    fields = ['status', 'review_notes']
    success_url = reverse_lazy('admin:accounts_guideapplication_changelist')
    
    def test_func(self):
        """
        Check if the current user has permission to review applications.
        
        Returns:
            bool: True if user is admin or manager, False otherwise
        """
        return self.request.user.is_authenticated and self.request.user.role in [User.Role.ADMIN, User.Role.MANAGER]
    
    def get_object(self, queryset=None):
        """
        Get the guide application object to be reviewed.
        
        Args:
            queryset: Optional queryset to use
            
        Returns:
            GuideApplication: The application to review
            
        Raises:
            Http404: If the application does not exist
        """
        # Get the application ID from the URL
        application_id = self.kwargs.get('pk')
        
        # Get the application object
        try:
            return GuideApplication.objects.get(id=application_id)
        except GuideApplication.DoesNotExist:
            raise Http404("Guide application not found")
    
    def post(self, request, *args, **kwargs):
        """
        Processes the approve/reject decision and updates the application status
        and user role accordingly.
        
        Args:
            request: The HTTP request object
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            HttpResponse: Redirect to success URL
        """
        application = self.get_object()
        action = request.POST.get('action')
        notes = request.POST.get('review_notes', '')
        
        if action == 'approve':
            # Approve the application and update user role
            if application.approve_application(request.user, notes):
                messages.success(request, f"Guide application for {application.user.username} has been approved.")
                
                # Send approval notification email to the applicant
                try:
                    send_mail(
                        'Your Guide Application has been Approved!',
                        f"Congratulations {application.user.first_name}!\n\nYour application to become a local guide has been approved. You can now access guide features on the platform.\n\nBest regards,\nThe TravelGuide Team",
                        settings.DEFAULT_FROM_EMAIL,
                        [application.user.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    logger.error(f"Failed to send approval email to {application.user.email}: {str(e)}")
        
        elif action == 'reject':
            # Get rejection reason
            reason = request.POST.get('rejection_reason', 'Your application did not meet our requirements.')
            
            # Reject the application
            if application.reject_application(request.user, reason, notes):
                messages.info(request, f"Guide application for {application.user.username} has been rejected.")
                
                # Send rejection notification email to the applicant
                try:
                    send_mail(
                        'Update on Your Guide Application',
                        f"Dear {application.user.first_name},\n\nThank you for your interest in becoming a local guide. Unfortunately, your application has not been approved at this time.\n\nReason: {reason}\n\nYou may apply again after addressing the concerns.\n\nBest regards,\nThe TravelGuide Team",
                        settings.DEFAULT_FROM_EMAIL,
                        [application.user.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    logger.error(f"Failed to send rejection email to {application.user.email}: {str(e)}")
        
        return redirect(self.success_url)


class AdminGuideApplicationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    View for listing all guide applications for admin review.
    
    Displays pending applications for admins and managers to review.
    """
    model = GuideApplication
    template_name = 'accounts/admin/guide_applications_list.html'
    context_object_name = 'applications'
    
    def test_func(self):
        """
        Check if the current user has permission to view applications.
        
        Only admins and managers can view guide applications.
        
        Returns:
            bool: True if user is an admin or manager, False otherwise
        """
        return self.request.user.is_authenticated and self.request.user.role in [User.Role.ADMIN, User.Role.MANAGER]
    
    def get_queryset(self):
        """
        Get the list of applications to display.
        
        By default, shows pending applications first, then under review ones.
        
        Returns:
            QuerySet: Filtered application queryset
        """
        # Filter by status parameter if provided
        status_filter = self.request.GET.get('status')
        
        if status_filter:
            return GuideApplication.objects.filter(status=status_filter).order_by('-application_date')
        else:
            # By default, show pending applications first, then under review ones
            return GuideApplication.objects.filter(
                status__in=[GuideApplication.Status.PENDING, GuideApplication.Status.UNDER_REVIEW]
            ).order_by('status', '-application_date')
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.
        
        Provides status filter options and counts of applications by status.
        
        Returns:
            dict: Context dictionary with filter options and counts
        """
        context = super().get_context_data(**kwargs)
        
        # Add status filter options
        context['status_options'] = GuideApplication.Status.choices
        
        # Add counts by status
        status_counts = {}
        for status_code, status_name in GuideApplication.Status.choices:
            status_counts[status_code] = GuideApplication.objects.filter(status=status_code).count()
        
        context['status_counts'] = status_counts
        context['current_status_filter'] = self.request.GET.get('status')
        
        return context


class SocialAuthenticationView(View):
    """
    View to handle social authentication success and failure.
    
    This view processes redirects from social authentication providers,
    handling both successful logins and authentication failures.
    """
    def get(self, request):
        """
        Handle GET request after social auth redirect.
        
        Shows success or error messages based on authentication result.
        
        Args:
            request: The HTTP request object
            
        Returns:
            HttpResponse: Redirect to home or login page
        """
        if 'error' in request.GET:
            messages.error(request, "Social authentication failed. Please try again.")
            return redirect('accounts:login')
            
        # If user is authenticated, show success message
        if request.user.is_authenticated:
            messages.success(request, f"Welcome, {request.user.username}!")
            
        return redirect('home')


def verify_email_view(request, token):
    """
    Verify user email using verification token.
    
    Confirms a user's email address by checking the verification token
    and updating their account accordingly.
    
    Args:
        request: The HTTP request object
        token: The email verification token
        
    Returns:
        HttpResponse: Rendered confirmation page
    """
    # This is a placeholder implementation
    # In a real application, you would:
    # 1. Look up the token in your database
    # 2. Check if it's valid and not expired
    # 3. Update the user's verified status
    
    # For demonstration, we'll just show a success message
    messages.success(request, "Your email has been verified successfully!")
    return redirect('accounts:login')


def account_verification_sent_view(request):
    """
    View shown after registration when email verification is required.
    
    Informs the user that a verification email has been sent and
    provides instructions on completing the verification process.
    
    Args:
        request: The HTTP request object
        
    Returns:
        HttpResponse: Rendered verification instructions
    """
    return render(request, 'accounts/verification_sent.html')
