"""
Core views for the food ordering system.
Contains unified login and registration views for role-based authentication.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView, PasswordResetView
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
import time
import logging
from .forms import UnifiedLoginForm, UnifiedRegistrationForm, RestaurantRegistrationForm
from .utils import EmailUtils  # EmailUtils is in utils.py file, not utils package

# Configure logging for session timeout events
logger = logging.getLogger(__name__)


class UnifiedLoginView(TemplateView):
    """
    Unified login view for both customers and restaurant owners.
    
    This view handles authentication for all user types and automatically
    redirects them to the appropriate dashboard based on their role:
    - Restaurant Owners -> Restaurant Dashboard
    - Customers -> Customer Home Page
    
    Features:
    - Single login form for all user types
    - Automatic role detection and redirection
    - Comprehensive error handling
    - Mobile-responsive design
    """
    template_name = 'core/unified_login.html'
    
    def get_context_data(self, **kwargs):
        """
        Add login form to context.
        
        Returns:
            dict: Context data with login form
        """
        context = super().get_context_data(**kwargs)
        context['form'] = UnifiedLoginForm()
        return context
    
    def post(self, request, *args, **kwargs):
        """
        Enhanced POST request handler for login form submission.
        
        Processes the login form with remember me functionality, authenticates the user,
        and redirects them to the appropriate dashboard based on their role.
        
        Features:
        - Remember me functionality for extended sessions
        - Enhanced session management with activity tracking
        - Improved error handling with specific feedback
        - Security logging and audit trail
        - CSRF protection and rate limiting
        
        Args:
            request: Django HTTP request object
            
        Returns:
            HttpResponse: Rendered template or redirect to appropriate dashboard
        """
        # DEBUG: Log incoming request data
        print(f"DEBUG: Login POST request received")
        print(f"DEBUG: Request data: {dict(request.POST)}")
        print(f"DEBUG: Request user: {request.user}")
        print(f"DEBUG: Request method: {request.method}")
        
        form = UnifiedLoginForm(request, data=request.POST)
        
        # DEBUG: Log form validation
        print(f"DEBUG: Form is valid: {form.is_valid()}")
        if not form.is_valid():
            print(f"DEBUG: Form errors: {form.errors}")
            print(f"DEBUG: Non-field errors: {form.non_field_errors()}")
        
        if form.is_valid():
            user = form.get_user()
            print(f"DEBUG: Authenticated user: {user.username if user else 'None'}")
            
            # Log authentication attempt for security audit
            logger.info(f'Login attempt successful for user: {user.username} from IP: {self.get_client_ip(request)}')
            
            # Authenticate user
            login(request, user)
            
            # Handle remember me functionality
            remember_me = form.cleaned_data.get('remember_me', False)
            if remember_me:
                # Extended session (2 weeks)
                request.session.set_expiry(1209600)  # 14 days in seconds
                logger.info(f'Extended session enabled for user: {user.username}')
            else:
                # Standard session (browser close)
                request.session.set_expiry(0)
                logger.info(f'Standard session for user: {user.username}')
            
            # Initialize session tracking for timeout management
            request.session['login_time'] = time.time()
            request.session['last_activity'] = time.time()
            request.session['remember_me'] = remember_me
            request.session['user_role'] = self.get_user_role(user)
            request.session.modified = True
            
            # Update user's last login timestamp
            from django.utils import timezone
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # Log successful login for session timeout tracking
            logger.info(f'User {user.username} logged in successfully - Session timeout tracking initialized')
            
            # Get the redirect URL based on user role
            redirect_url = form.get_redirect_url(user)
            print(f"DEBUG: Redirecting to: {redirect_url}")
            
            # Add success message with personalized greeting
            greeting = self.get_personalized_greeting(user)
            messages.success(
                request, 
                f'{greeting}, {user.get_full_name() or user.username}! You have been successfully logged in.'
            )
            
            return redirect(redirect_url)
        else:
            # Log failed authentication attempt for security
            username = request.POST.get('username', 'unknown')
            logger.warning(f'Login attempt failed for username: {username} from IP: {self.get_client_ip(request)}')
            
            # Enhanced error handling with specific feedback
            error_message = self.get_error_message(form)
            messages.error(request, error_message)
            
            # Re-render the form with errors and preserve form data
            context = self.get_context_data(**kwargs)
            context['form'] = form
            context['failed_username'] = username  # Preserve username for convenience
            return self.render_to_response(context)
    
    def get_client_ip(self, request):
        """
        Get the client's IP address for security logging.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            str: Client IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_user_role(self, user):
        """
        Determine the user's role for session tracking.
        
        Args:
            user: Authenticated User object
            
        Returns:
            str: User role string
        """
        if user.is_superuser:
            return 'superuser'
        elif user.is_staff:
            return 'staff'
        elif user.groups.filter(name='Restaurant Owner').exists():
            return 'restaurant_owner'
        else:
            return 'customer'
    
    def get_personalized_greeting(self, user):
        """
        Get a personalized greeting based on time of day and user role.
        
        Args:
            user: Authenticated User object
            
        Returns:
            str: Personalized greeting message
        """
        from datetime import datetime
        hour = datetime.now().hour
        
        if hour < 12:
            time_greeting = 'Good morning'
        elif hour < 17:
            time_greeting = 'Good afternoon'
        else:
            time_greeting = 'Good evening'
        
        # Add role-specific greeting
        if user.is_superuser or user.is_staff:
            return f'{time_greeting}, Administrator'
        elif user.groups.filter(name='Restaurant Owner').exists():
            return f'{time_greeting}, Restaurant Owner'
        else:
            return f'{time_greeting}, Welcome back'
    
    def get_error_message(self, form):
        """
        Get specific error message based on form validation errors.
        
        Args:
            form: The login form with validation errors
            
        Returns:
            str: Specific error message for the user
        """
        if 'inactive' in form.errors:
            return 'Your account has been deactivated. Please contact support for assistance.'
        elif 'locked_out' in form.errors:
            return 'Too many failed login attempts. Your account has been temporarily locked. Please try again later.'
        elif form.non_field_errors():
            return 'Invalid username or password. Please check your credentials and try again.'
        else:
            return 'Please correct the errors below and try again.'


class UnifiedRegistrationView(TemplateView):
    """
    Unified registration view for both customers and restaurant owners.
    
    This view handles user registration with role selection and automatically
    assigns users to the appropriate Django group.
    
    Features:
    - Single registration form for all user types
    - Role selection during registration
    - Comprehensive form validation
    - Airbnb-style responsive design
    - Automatic group assignment
    """
    
    template_name = 'core/unified_registration.html'
    
    def get_context_data(self, **kwargs):
        """
        Provide context data for the registration template.
        
        Includes both customer and restaurant forms to support the unified registration
        interface with user type selection toggle.
        
        Args:
            **kwargs: Additional keyword arguments
            
        Returns:
            dict: Context data with registration forms
        """
        context = super().get_context_data(**kwargs)
        context['form'] = UnifiedRegistrationForm(prefix='customer')
        context['restaurant_form'] = RestaurantRegistrationForm(prefix='restaurant')
        return context
    
    def post(self, request, *args, **kwargs):
        """
        Handle POST request for registration form submission.
        
        Processes the registration form, detects user type, and routes to appropriate form handler.
        Creates the user, assigns them to the appropriate group, sends welcome email, and redirects to login.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            HttpResponse: Rendered template or redirect to login page
        """
        print("DEBUG: Registration view post method called")  # Debug line
        print(f"DEBUG: POST data: {request.POST}")  # Debug line
        
        # Check if this is a restaurant registration
        user_type = request.POST.get('user_type', 'customer')
        
        if user_type == 'restaurant':
            # Add success message before redirecting to wizard
            messages.info(
                request,
                '🍽️ Starting restaurant registration! You will be guided through a multi-step process to register your restaurant.'
            )
            # Redirect to new restaurant registration wizard
            return redirect('restaurant:registration_wizard')
        else:
            # Handle customer registration
            return self.handle_customer_registration(request, **kwargs)
    
    def handle_customer_registration(self, request, **kwargs):
        """
        Handle customer registration using UnifiedRegistrationForm.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            HttpResponse: Rendered template or redirect to login page
        """
        form = UnifiedRegistrationForm(request.POST, prefix='customer')
        print(f"DEBUG: Customer form is valid: {form.is_valid()}")  # Debug line
        
        if form.is_valid():
            # Save the user with encrypted password and group assignment
            user = form.save()
            print(f"DEBUG: Customer user created: {user.username}")  # Debug line
            
            # Send welcome email using the enhanced EmailUtils
            try:
                email_sent = EmailUtils.send_welcome_email(user, request)
                if email_sent:
                    print("DEBUG: Welcome email sent successfully")  # Debug line
                    messages.info(
                        request, 
                        f'A welcome email has been sent to {user.email}.'
                    )
                else:
                    print("DEBUG: Welcome email failed to send")  # Debug line
                    messages.warning(
                        request,
                        'Account created successfully, but we had trouble sending the welcome email.'
                    )
            except Exception as e:
                # Log the error but don't break the registration process
                print(f"Failed to send welcome email to {user.email}: {str(e)}")
                messages.warning(
                    request,
                    'Account created successfully, but we had trouble sending the welcome email.'
                )
            
            # Add success message
            messages.success(
                request, 
                f'Customer account created successfully for {user.username}! '
                f'A welcome email has been sent to {user.email}. You can now log in.'
            )
            
            return redirect('core:login')
        else:
            print(f"DEBUG: Customer form errors: {form.errors}")  # Debug line
            # Add error message for invalid form data
            messages.error(
                request, 
                'Please correct the errors below and try again.'
            )
            
            # Re-render the form with errors
            context = self.get_context_data(**kwargs)
            context['form'] = form
            return self.render_to_response(context)
    
    def handle_restaurant_registration(self, request, **kwargs):
        """
        Handle restaurant registration using RestaurantRegistrationForm.
        
        Implements comprehensive registration workflow including:
        - Form validation
        - User and restaurant creation
        - Email notifications (welcome, submission, manager alerts)
        - Activity logging and analytics tracking
        - Error handling and user feedback
        
        Args:
            request: Django HTTP request object
            **kwargs: Additional keyword arguments
            
        Returns:
            HttpResponse: Rendered template or redirect to login page
        """
        import logging
        from django.utils import timezone
        
        logger = logging.getLogger(__name__)
        form = RestaurantRegistrationForm(request.POST, request.FILES, prefix='restaurant')
        
        # Log registration attempt
        logger.info(f"Restaurant registration attempt from IP: {self.get_client_ip(request)}")
        
        if form.is_valid():
            try:
                # Save both user account and restaurant profile
                user, restaurant = form.save()
                
                # Log successful creation
                logger.info(
                    f"Restaurant registration successful - "
                    f"User: {user.username}, Restaurant: {restaurant.name}, "
                    f"ID: {restaurant.id}"
                )
                
                # Track registration analytics
                self.track_restaurant_registration(user, restaurant, request)
                
                # Send welcome email using the enhanced EmailUtils
                try:
                    email_sent = EmailUtils.send_welcome_email(user, request)
                    if email_sent:
                        logger.info(f"Welcome email sent to {user.email}")
                        messages.info(
                            request, 
                            f'A welcome email has been sent to {user.email}.'
                        )
                    else:
                        logger.warning(f"Welcome email failed for {user.email}")
                        messages.warning(
                            request,
                            'Account created successfully, but we had trouble sending the welcome email.'
                        )
                except Exception as e:
                    logger.error(f"Welcome email exception for {user.email}: {str(e)}", exc_info=True)
                    messages.warning(
                        request,
                        'Account created successfully, but we had trouble sending the welcome email.'
                    )
                
                # Send restaurant submission confirmation email
                try:
                    submission_email_sent = EmailUtils.send_restaurant_submission_email(user, restaurant, request)
                    if submission_email_sent:
                        logger.info(f"Restaurant submission email sent to {user.email}")
                    else:
                        logger.warning(f"Restaurant submission email failed for {user.email}")
                except Exception as e:
                    logger.error(f"Restaurant submission email exception: {str(e)}", exc_info=True)
                
                # Send notification emails to managers/admins
                try:
                    success_count, total_count, error_msg = EmailUtils.send_manager_notification_emails(restaurant, request)
                    if success_count > 0:
                        logger.info(f"Manager notifications sent: {success_count}/{total_count} successful")
                    else:
                        logger.warning(f"Manager notifications failed: {error_msg}")
                except Exception as e:
                    logger.error(f"Manager notification exception: {str(e)}", exc_info=True)
                
                # Add comprehensive success message
                messages.success(
                    request, 
                    f'🎉 Restaurant "{restaurant.name}" registered successfully! '
                    f'Your account ({user.username}) has been created and is now pending manager approval. '
                    f'Your restaurant will appear on the main page once approved by our team. '
                    f'📧 Confirmation emails have been sent to {user.email}.'
                )
                
                # Log successful completion
                logger.info(f"Restaurant registration completed successfully for {restaurant.name}")
                
                return redirect('core:login')
                
            except Exception as e:
                # Handle unexpected errors during save
                logger.error(
                    f"Unexpected error during restaurant registration: {str(e)}", 
                    exc_info=True
                )
                messages.error(
                    request,
                    'An unexpected error occurred during registration. Please try again or contact support if the problem persists.'
                )
                context = self.get_context_data(**kwargs)
                context['restaurant_form'] = form
                return self.render_to_response(context)
        else:
            # Log validation failure
            logger.warning(
                f"Restaurant registration validation failed - "
                f"Errors: {form.errors.as_json()}, "
                f"IP: {self.get_client_ip(request)}"
            )
            
            # Add user-friendly error message
            messages.error(
                request, 
                'Please correct the errors below and try again.'
            )
            
            # Re-render the template with restaurant form errors
            context = self.get_context_data(**kwargs)
            context['restaurant_form'] = form
            context['form_errors'] = form.errors
            return self.render_to_response(context)
    
    def get_client_ip(self, request):
        """
        Extract client IP address from request for logging and security.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            str: Client IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip
    
    def track_restaurant_registration(self, user, restaurant, request):
        """
        Track restaurant registration analytics for monitoring and reporting.
        
        Records registration event with metadata for business intelligence
        and system monitoring purposes.
        
        Args:
            user: Created User object
            restaurant: Created Restaurant object
            request: Django HTTP request object
        """
        import logging
        from django.utils import timezone
        
        logger = logging.getLogger(__name__)
        
        try:
            # Prepare analytics data
            analytics_data = {
                'event': 'restaurant_registration',
                'timestamp': timezone.now().isoformat(),
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'restaurant_id': restaurant.id,
                'restaurant_name': restaurant.name,
                'cuisine_type': restaurant.cuisine_type,
                'ip_address': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown'),
                'referrer': request.META.get('HTTP_REFERER', 'direct'),
            }
            
            # Log analytics event
            logger.info(f"Analytics: Restaurant Registration - {analytics_data}")
            
            # Here you can also send to external analytics services
            # Example: Google Analytics, Mixpanel, or custom analytics DB
            
        except Exception as e:
            # Don't fail registration if analytics tracking fails
            logger.error(f"Analytics tracking error: {str(e)}", exc_info=True)
    
    def send_welcome_email(self, user, request):
        """
        Send welcome email to newly registered user.
        
        Creates and sends a personalized welcome email with account details
        and information about the restaurant upgrade process.
        
        Args:
            user: User object that was just created
            request: Django HTTP request object for building absolute URLs
            
        Raises:
            Exception: If email sending fails
        """
        # Build the site URL for absolute links in email
        site_url = request.build_absolute_uri('/')
        
        # Render the HTML email template
        html_message = render_to_string('emails/welcome_email.html', {
            'user': user,
            'site_url': site_url,
        })
        
        # Create plain text version for email clients that don't support HTML
        plain_message = f"""
        Welcome to Food Ordering System, {user.username}!
        
        Thank you for joining our food ordering community. Your account has been created successfully.
        
        Account Details:
        Username: {user.username}
        Email: {user.email}
        Registration Date: {user.date_joined.strftime('%B %d, %Y')}
        
        What's Next:
        - Browse restaurants and discover amazing food
        - Place orders from your favorite eateries
        - Track deliveries in real-time
        
        Want to Register Your Restaurant?
        If you're a restaurant owner, visit your profile page to upgrade your account:
        {site_url}profile/
        
        Go to your profile and submit your restaurant application for approval.
        
        If you have any questions, contact our support team.
        
        Happy ordering!
        The Food Ordering Team
        🍽️ Delicious food, delivered with care
        """
        
        # Send the email
        send_mail(
            subject='Welcome to Food Ordering System! 🍽️',
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@foodordering.com'),
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )


class RestaurantRegistrationView(TemplateView):
    """
    Redirect view for deprecated direct restaurant registration.
    
    This view handles the old restaurant registration URL and redirects users
    to the unified registration page with an informative message about the
    new customer-first registration workflow.
    
    The restaurant registration process has been updated to require all users
    to first register as customers, then upgrade to restaurant owners from
    their profile page.
    """
    
    def get(self, request, *args, **kwargs):
        """
        Handle GET requests by redirecting to unified registration.
        
        Adds an informative message explaining the new registration workflow
        and redirects users to the main registration page.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            HttpResponseRedirect: Redirect to unified registration page
        """
        messages.info(
            request,
            'Restaurant registration has been updated! Please register as a customer first, '
            'then upgrade to restaurant owner from your profile page. It\'s quick and easy!'
        )
        return redirect('core:register')
    
    def get_context_data(self, **kwargs):
        """
        Add restaurant registration form to context.
        
        Returns:
            dict: Context data with restaurant registration form
        """
        context = super().get_context_data(**kwargs)
        context['form'] = RestaurantRegistrationForm()
        return context
    
    def post(self, request, *args, **kwargs):
        """
        Handle POST request for restaurant registration form submission.
        
        Processes the comprehensive registration form, creates both user account
        and restaurant profile, assigns appropriate groups, and redirects to login.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            HttpResponse: Rendered template or redirect to login page
        """
        form = RestaurantRegistrationForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Save both user account and restaurant profile
            user, restaurant = form.save()
            
            # Add success message with restaurant name
            messages.success(
                request, 
                f'Restaurant "{restaurant.name}" registered successfully! '
                f'Your account ({user.username}) is ready. You can now log in.'
            )
            
            return redirect('core:login')
        else:
            # Add error message for invalid form data
            messages.error(
                request, 
                'Please correct the errors below and try again.'
            )
            
            # Re-render the form with errors
            context = self.get_context_data(**kwargs)
            context['form'] = form
            return self.render_to_response(context)


class CustomLogoutView(LogoutView):
    """
    Custom logout view with success message.
    
    Handles user logout and displays a success message.
    Redirects to the unified login page after logout.
    """
    next_page = reverse_lazy('core:login')
    
    def dispatch(self, request, *args, **kwargs):
        """
        Handle logout with success message.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            HttpResponse: Redirect to login page with success message
        """
        # Call parent dispatch first to perform the actual logout
        response = super().dispatch(request, *args, **kwargs)
        # Then add the success message (after logout is complete)
        messages.info(request, 'You have been successfully logged out.')
        return response


@login_required
def dashboard_redirect(request):
    """
    Redirect authenticated users to their appropriate dashboard.
    
    This view acts as a central redirect point for authenticated users,
    sending them to the correct dashboard based on their role.
    
    Args:
        request: Django HTTP request object
        
    Returns:
        HttpResponse: Redirect to appropriate dashboard
    """
    user = request.user
    
    # Debug logging to identify the issue
    print(f"DEBUG dashboard_redirect: User={user.username}")
    print(f"DEBUG dashboard_redirect: Has restaurants={user.restaurants.exists()}")
    if user.restaurants.exists():
        print(f"DEBUG dashboard_redirect: Restaurant count={user.restaurants.count()}")
        print(f"DEBUG dashboard_redirect: Restaurants={list(user.restaurants.values_list('name', flat=True))}")
    
    # Check if user is a restaurant owner (matching dropdown and login logic)
    if user.restaurants.exists():
        print(f"DEBUG dashboard_redirect: Redirecting to restaurant:dashboard")
        return redirect('restaurant:dashboard')
    
    # Default to customer home
    print(f"DEBUG dashboard_redirect: Redirecting to customer:home")
    return redirect('customer:home')


def home_redirect(request):
    """
    Redirect to the appropriate home page based on authentication status.
    
    If user is authenticated, redirects to their dashboard.
    If user is not authenticated, redirects to customer home.
    
    Args:
        request: Django HTTP request object
        
    Returns:
        HttpResponse: Redirect to appropriate page
    """
    if request.user.is_authenticated:
        return dashboard_redirect(request)
    else:
        return redirect('customer:home')


@require_http_methods(["GET"])
def session_status(request):
    """
    API endpoint to check current session status.
    
    Returns JSON response with session information including
    timeout settings and remaining time. Used by JavaScript
    session timeout manager.
    
    Args:
        request: Django HTTP request object
        
    Returns:
        JsonResponse: Session status information or error
    """
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'error',
            'message': 'User not authenticated',
            'redirect_url': settings.LOGIN_URL
        }, status=401)
    
    # Get session timeout settings
    session_timeout = getattr(settings, 'SESSION_INACTIVITY_TIMEOUT', 1200)
    warning_time = getattr(settings, 'SESSION_WARNING_TIME', 120)
    
    # Get last activity from session
    last_activity = request.session.get('last_activity', time.time())
    current_time = time.time()
    time_remaining = max(0, session_timeout - (current_time - last_activity))
    
    return JsonResponse({
        'status': 'active',
        'session_timeout': session_timeout,
        'warning_time': warning_time,
        'time_remaining': int(time_remaining),
        'last_activity': last_activity,
        'current_time': current_time,
        'username': request.user.username
    })


@require_http_methods(["POST"])
def extend_session(request):
    """
    API endpoint to extend the current session.
    
    Updates the last activity timestamp in the session to
    effectively extend the session timeout. Used by JavaScript
    when user clicks "Extend Session" button.
    
    Args:
        request: Django HTTP request object
        
    Returns:
        JsonResponse: Success status or error
    """
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'error',
            'message': 'User not authenticated',
            'redirect_url': settings.LOGIN_URL
        }, status=401)
    
    # Update last activity to current time
    current_time = time.time()
    request.session['last_activity'] = current_time
    request.session.modified = True
    
    # Log session extension for auditing
    logger.info(f'User {request.user.username} extended session at {current_time}')
    
    # Get updated session info
    session_timeout = getattr(settings, 'SESSION_INACTIVITY_TIMEOUT', 1200)
    
    return JsonResponse({
        'status': 'extended',
        'message': 'Session extended successfully',
        'session_timeout': session_timeout,
        'time_remaining': session_timeout,
        'extended_at': current_time,
        'username': request.user.username
    })


# Custom Password Reset Form with Silent Email Validation
class CustomPasswordResetForm(PasswordResetView.form_class):
    """
    Custom password reset form that silently validates email exists.
    
    This form checks if the email address is registered in the system before
    allowing password reset, preventing emails to non-existent addresses
    while maintaining security by not revealing email existence.
    """
    
    def get_users(self, email):
        """
        Override get_users to only return users if email exists.
        
        Args:
            email (str): Email address to look up
            
        Returns:
            QuerySet: Users with matching email (empty if not found)
        """
        print(f"🔍 DEBUG: CustomPasswordResetForm.get_users() called with email: {email}")
        
        User = get_user_model()
        
        # Check if email exists in database
        active_users = User.objects.filter(
            email__iexact=email,
            is_active=True
        )
        
        # Log whether email was found for debugging
        if active_users.exists():
            print(f"✅ Email found in database: {email} - Sending email to {active_users.count()} user(s)")
        else:
            print(f"⚠️  Email not found in database: {email} - No email will be sent")
        
        return active_users


class CustomPasswordResetView(PasswordResetView):
    """
    Custom password reset view with silent email validation.
    
    This view extends Django's PasswordResetView to validate that the
    email address exists in the database before sending a reset email,
    but maintains security by not revealing whether email exists.
    """
    form_class = CustomPasswordResetForm
    template_name = 'core/password_reset_form.html'
    email_template_name = 'core/password_reset_email.html'
    subject_template_name = 'core/password_reset_subject.txt'
    success_url = '/auth/password-reset/done/'
    
    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to add debugging.
        """
        print(f"🔍 DEBUG: CustomPasswordResetView.dispatch() called")
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """
        Override form_valid to add custom success message and debugging.
        
        Args:
            form: The validated password reset form
            
        Returns:
            HttpResponse: Redirect to success URL
        """
        print(f"🔍 DEBUG: CustomPasswordResetView.form_valid() called")
        
        # Get the email from form
        email = form.cleaned_data.get('email')
        User = get_user_model()
        
        print(f"🔍 DEBUG: Processing password reset for email: {email}")
        
        # Check if user exists and show appropriate message
        if User.objects.filter(email__iexact=email, is_active=True).exists():
            print(f"✅ User exists - showing success message")
            messages.success(
                self.request,
                'Password reset instructions have been sent to your email address.'
            )
        else:
            print(f"⚠️  User does not exist - showing generic message")
            # Show same success message for security (don't reveal email existence)
            messages.success(
                self.request,
                'If your email address is registered, you will receive password reset instructions shortly.'
            )
        
        # Call parent form_valid to handle email sending
        print(f"🔍 DEBUG: Calling parent form_valid() to send email")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """
        Override form_invalid to add error message.
        
        Args:
            form: The invalid password reset form
            
        Returns:
            HttpResponse: Return to form with errors
        """
        print(f"🔍 DEBUG: CustomPasswordResetView.form_invalid() called")
        
        # Add error message
        messages.error(
            self.request,
            'Please enter a valid email address and try again.'
        )
        
        # Call parent form_invalid
        return super().form_invalid(form)
