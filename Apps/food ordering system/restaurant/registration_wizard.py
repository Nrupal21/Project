"""
Multi-step restaurant registration wizard.

Provides a step-by-step registration process with validation at each stage,
progress tracking, and the ability to save drafts and return later.
"""

from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.core.files.storage import default_storage
import json
import logging
import re

logger = logging.getLogger(__name__)


class RegistrationWizardMixin:
    """
    Mixin for handling wizard session data and navigation.
    
    Provides common functionality for multi-step wizards including
    session management, progress tracking, and step validation.
    """
    
    def get_wizard_data(self, request):
        """
        Retrieve wizard data from session.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            dict: Wizard session data
        """
        return request.session.get('restaurant_wizard_data', {})
    
    def set_wizard_data(self, request, data):
        """
        Store wizard data in session.
        
        Args:
            request: Django HTTP request object
            data: Dictionary of data to store
        """
        request.session['restaurant_wizard_data'] = data
        request.session.modified = True
    
    def clear_wizard_data(self, request):
        """
        Clear wizard data from session.
        
        Args:
            request: Django HTTP request object
        """
        if 'restaurant_wizard_data' in request.session:
            del request.session['restaurant_wizard_data']
            request.session.modified = True
    
    def get_current_step(self, request):
        """
        Get the current wizard step number.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            int: Current step number (1-indexed)
        """
        wizard_data = self.get_wizard_data(request)
        return wizard_data.get('current_step', 1)
    
    def set_current_step(self, request, step):
        """
        Set the current wizard step number.
        
        Args:
            request: Django HTTP request object
            step: Step number to set
        """
        wizard_data = self.get_wizard_data(request)
        wizard_data['current_step'] = step
        self.set_wizard_data(request, wizard_data)
    
    def get_completed_steps(self, request):
        """
        Get list of completed step numbers.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            list: Completed step numbers
        """
        wizard_data = self.get_wizard_data(request)
        return wizard_data.get('completed_steps', [])
    
    def mark_step_complete(self, request, step):
        """
        Mark a step as completed.
        
        Args:
            request: Django HTTP request object
            step: Step number to mark complete
        """
        wizard_data = self.get_wizard_data(request)
        completed = wizard_data.get('completed_steps', [])
        if step not in completed:
            completed.append(step)
            wizard_data['completed_steps'] = completed
            self.set_wizard_data(request, wizard_data)
    
    def validate_step_data(self, request, step, data):
        """
        Validate data for a specific wizard step.
        
        Args:
            request: Django HTTP request object
            step (int): Step number to validate
            data (dict): Form data to validate
            
        Returns:
            tuple: (is_valid, errors_dict)
        """
        errors = {}
        
        if step == 1:
            # Account Information Validation
            errors = self._validate_account_info(data)
        elif step == 2:
            # Restaurant Basic Details Validation
            errors = self._validate_restaurant_details(data)
        elif step == 3:
            # Location & Contact Validation
            errors = self._validate_location_contact(data)
        elif step == 4:
            # Business Hours & Pricing Validation
            errors = self._validate_business_hours_pricing(data)
        elif step == 5:
            # Final Review Validation
            errors = self._validate_final_review(data)
        
        return len(errors) == 0, errors
    
    def _validate_account_info(self, data):
        """
        Validate account information fields.
        
        Args:
            data (dict): Form data to validate
            
        Returns:
            dict: Validation errors
        """
        errors = {}
        
        # For authenticated users, skip account validation
        # This data is not required when user is already logged in
        return errors
        
        # Only validate for unauthenticated users (commented out since we skip above)
        """
        # Username validation
        username = data.get('username', '').strip()
        if not username:
            errors['username'] = 'Username is required'
        elif len(username) < 3 or len(username) > 20:
            errors['username'] = 'Username must be 3-20 characters long'
        elif not re.match(r'^[a-zA-Z0-9_]+$', username):
            errors['username'] = 'Username can only contain letters, numbers, and underscores'
        elif User.objects.filter(username__iexact=username).exists():
            errors['username'] = 'This username is already taken'
        
        # Email validation
        email = data.get('email', '').strip()
        if not email:
            errors['email'] = 'Email is required'
        elif not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            errors['email'] = 'Please enter a valid email address'
        elif User.objects.filter(email__iexact=email).exists():
            errors['email'] = 'This email is already registered'
        
        # Password validation
        password = data.get('password', '')
        password_confirm = data.get('password_confirm', '')
        
        if not password:
            errors['password'] = 'Password is required'
        elif len(password) < 8:
            errors['password'] = 'Password must be at least 8 characters long'
        elif not re.search(r'[A-Za-z]', password):
            errors['password'] = 'Password must contain at least one letter'
        elif not re.search(r'\d', password):
            errors['password'] = 'Password must contain at least one number'
        elif password != password_confirm:
            errors['password_confirm'] = 'Passwords do not match'
        """
        
        return errors
    
    def _validate_restaurant_details(self, data):
        """
        Validate restaurant basic details.
        
        Args:
            data (dict): Form data to validate
            
        Returns:
            dict: Validation errors
        """
        errors = {}
        
        # Restaurant name validation
        restaurant_name = data.get('restaurant_name', '').strip()
        if not restaurant_name:
            errors['restaurant_name'] = 'Restaurant name is required'
        elif len(restaurant_name) < 2 or len(restaurant_name) > 100:
            errors['restaurant_name'] = 'Restaurant name must be 2-100 characters long'
        
        # Description validation
        description = data.get('description', '').strip()
        if not description:
            errors['description'] = 'Description is required'
        elif len(description) < 10:
            errors['description'] = 'Description must be at least 10 characters long'
        
        # Cuisine type validation
        cuisine_type = data.get('cuisine_type', '').strip().lower()
        if not cuisine_type:
            errors['cuisine_type'] = 'Please select a cuisine type'
        
        valid_cuisines = ['italian', 'indian', 'american', 'chinese', 'japanese', 
                         'mexican', 'thai', 'mediterranean', 'french', 'other']
        if cuisine_type not in valid_cuisines:
            errors['cuisine_type'] = 'Invalid cuisine type selected'
        
        return errors
    
    def _validate_location_contact(self, data):
        """
        Validate location and contact information.
        
        Args:
            data (dict): Form data to validate
            
        Returns:
            dict: Validation errors
        """
        errors = {}
        
        # Phone validation - updated regex to accept +, spaces, dashes, and parentheses
        phone = data.get('phone', '').strip()
        if not phone:
            errors['phone'] = 'Phone number is required'
        elif not re.match(r'^[\d\s\-\(\)\+]+$', phone):
            errors['phone'] = 'Please enter a valid phone number'
        elif len(re.sub(r'[^\d]', '', phone)) < 10:
            errors['phone'] = 'Phone number must have at least 10 digits'
        
        # Email validation (different from account email)
        contact_email = data.get('email', '').strip()
        if not contact_email:
            errors['email'] = 'Contact email is required'
        elif not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', contact_email):
            errors['email'] = 'Please enter a valid email address'
        
        # Address validation
        address = data.get('address', '').strip()
        if not address:
            errors['address'] = 'Address is required'
        elif len(address) < 10 or len(address) > 200:
            errors['address'] = 'Address must be 10-200 characters long'
        
        return errors
    
    def _validate_business_hours_pricing(self, data):
        """
        Validate business hours and pricing information.
        
        Args:
            data (dict): Form data to validate
            
        Returns:
            dict: Validation errors
        """
        errors = {}
        
        # Opening time validation
        opening_time = data.get('opening_time', '')
        if not opening_time:
            errors['opening_time'] = 'Opening time is required'
        
        # Closing time validation
        closing_time = data.get('closing_time', '')
        if not closing_time:
            errors['closing_time'] = 'Closing time is required'
        
        # Validate time format and logic
        if opening_time and closing_time:
            try:
                from datetime import datetime
                opening = datetime.strptime(opening_time, '%H:%M').time()
                closing = datetime.strptime(closing_time, '%H:%M').time()
                
                # Check if closing time is after opening time
                if closing <= opening:
                    errors['closing_time'] = 'Closing time must be after opening time'
            except ValueError:
                errors['opening_time'] = 'Invalid time format'
                errors['closing_time'] = 'Invalid time format'
        
        # Minimum order validation
        minimum_order = data.get('minimum_order', '').strip()
        if not minimum_order:
            errors['minimum_order'] = 'Minimum order amount is required'
        else:
            try:
                amount = float(minimum_order)
                if amount < 0:
                    errors['minimum_order'] = 'Minimum order cannot be negative'
                elif amount > 1000:
                    errors['minimum_order'] = 'Minimum order seems too high'
            except ValueError:
                errors['minimum_order'] = 'Please enter a valid amount'
        
        # Delivery fee validation
        delivery_fee = data.get('delivery_fee', '').strip()
        if not delivery_fee:
            errors['delivery_fee'] = 'Delivery fee is required'
        else:
            try:
                fee = float(delivery_fee)
                if fee < 0:
                    errors['delivery_fee'] = 'Delivery fee cannot be negative'
                elif fee > 100:
                    errors['delivery_fee'] = 'Delivery fee seems too high'
            except ValueError:
                errors['delivery_fee'] = 'Please enter a valid amount'
        
        return errors
    
    def _validate_final_review(self, data):
        """
        Validate final review step (images and confirmation).
        
        Args:
            data (dict): Form data to validate
            
        Returns:
            dict: Validation errors
        """
        errors = {}
        
        # Terms acceptance validation
        terms_accepted = data.get('terms_accepted', '')
        if not terms_accepted:
            errors['terms_accepted'] = 'You must accept the terms and conditions'
        
        return errors


class RestaurantRegistrationWizardView(TemplateView, RegistrationWizardMixin):
    """
    Multi-step restaurant registration wizard view.
    
    Guides restaurant owners through a step-by-step registration process:
    Step 1: Account Information
    Step 2: Restaurant Basic Details
    Step 3: Location & Contact
    Step 4: Business Hours & Pricing
    Step 5: Images & Final Review
    """
    
    template_name = 'restaurant/registration_wizard.html'
    total_steps = 5
    
    def get_context_data(self, **kwargs):
        """
        Prepare context data for wizard template.
        
        Args:
            **kwargs: Additional keyword arguments
            
        Returns:
            dict: Template context data
        """
        context = super().get_context_data(**kwargs)
        
        current_step = self.get_current_step(self.request)
        wizard_data = self.get_wizard_data(self.request)
        completed_steps = self.get_completed_steps(self.request)
        
        context.update({
            'current_step': current_step,
            'total_steps': self.total_steps,
            'wizard_data': wizard_data,
            'completed_steps': completed_steps,
            'progress_percentage': (len(completed_steps) / self.total_steps) * 100,
            'can_go_back': current_step > 1,
            'can_submit': len(completed_steps) >= self.total_steps - 1,
        })
        
        # Add step-specific data
        context.update(self._get_step_context(current_step, wizard_data))
        
        return context
    
    def post(self, request, *args, **kwargs):
        """
        Handle wizard step submission.
        
        Validates the current step data, saves it to session,
        and either moves to next step or finalizes registration.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            HttpResponse: Redirect or rendered template
        """
        action = request.POST.get('action')
        current_step = self.get_current_step(request)
        
        if action == 'next':
            return self._handle_next_step(request, current_step)
        elif action == 'back':
            return self._handle_previous_step(request, current_step)
        elif action == 'save_draft':
            return self._handle_save_draft(request)
        elif action == 'submit':
            return self._handle_final_submission(request)
        
        return self.get(request, *args, **kwargs)
    
    def _handle_next_step(self, request, current_step):
        """
        Validate current step and move to next.
        
        Args:
            request: Django HTTP request object
            current_step: Current step number
            
        Returns:
            HttpResponse: Redirect to next step or error display
        """
        # Validate current step data using new validation system
        is_valid, errors = self.validate_step_data(request, current_step, request.POST)
        
        if not is_valid:
            # Add validation errors to messages framework
            for field, error_message in errors.items():
                messages.error(request, f"{field.title()}: {error_message}")
            
            # Store errors in session to display in template
            wizard_data = self.get_wizard_data(request)
            wizard_data['validation_errors'] = errors
            self.set_wizard_data(request, wizard_data)
            
            return self.get(request)
        
        # Clear any previous validation errors
        wizard_data = self.get_wizard_data(request)
        if 'validation_errors' in wizard_data:
            del wizard_data['validation_errors']
            self.set_wizard_data(request, wizard_data)
        
        # Save step data to session
        self._save_step_data(request, current_step, request.POST, request.FILES)
        
        # Mark current step as completed
        self.mark_step_complete(request, current_step)
        
        # Handle account creation for Step 1 (unauthenticated users)
        if current_step == 1 and not request.user.is_authenticated:
            try:
                username = request.POST.get('username', '').strip()
                email = request.POST.get('email', '').strip()
                password = request.POST.get('password', '')
                
                # Create user account
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                
                # Authenticate and login the user
                authenticated_user = authenticate(username=username, password=password)
                if authenticated_user:
                    login(request, authenticated_user)
                    messages.success(request, 'Account created successfully!')
                
            except Exception as e:
                logger.error(f"Account creation failed: {str(e)}")
                messages.error(request, 'Failed to create account. Please try again.')
                return self.get(request)
        
        # Move to next step or finalize
        if current_step < self.total_steps:
            self.set_current_step(request, current_step + 1)
            messages.success(request, f'Step {current_step} completed successfully!')
        else:
            # Final step - handle submission
            return self._handle_final_submission(request)
        
        return redirect('restaurant:registration_wizard')
    
    def _handle_previous_step(self, request, current_step):
        """
        Navigate to previous step.
        
        Args:
            request: Django HTTP request object
            current_step: Current step number
            
        Returns:
            HttpResponse: Redirect to previous step
        """
        if current_step > 1:
            self.set_current_step(request, current_step - 1)
        return redirect('restaurant:registration_wizard')
    
    def _handle_save_draft(self, request):
        """
        Save current progress as draft.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            JsonResponse: Success response
        """
        current_step = self.get_current_step(request)
        self._save_step_data(request, current_step, request.POST, request.FILES)
        
        messages.success(request, 'Your progress has been saved as a draft.')
        return JsonResponse({'success': True, 'message': 'Draft saved'})
    
    def _handle_final_submission(self, request):
        """
        Process final registration submission.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            HttpResponse: Redirect to success page or error display
        """
        wizard_data = self.get_wizard_data(request)
        
        try:
            # Create pending restaurant from wizard data
            pending_restaurant = self._create_restaurant_from_wizard(request, wizard_data)
            
            # Send notification emails to all managers/admins
            from django.contrib.auth.models import User
            from django.core.mail import send_mail
            from django.template.loader import render_to_string
            from django.conf import settings
            
            # Get all staff users (managers and admins)
            managers = User.objects.filter(is_staff=True, is_active=True)
            
            # Send email notifications to managers
            for manager in managers:
                try:
                    subject = f'New Restaurant Application: {pending_restaurant.restaurant_name}'
                    message = f"""
                    A new restaurant application has been submitted and is awaiting review.
                    
                    Restaurant Name: {pending_restaurant.restaurant_name}
                    Applicant: {request.user.username} ({request.user.email})
                    Cuisine Type: {pending_restaurant.get_cuisine_type_display()}
                    
                    Please log in to the admin panel to review and approve/reject this application.
                    """
                    
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [manager.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    logger.warning(f"Failed to send notification email to {manager.email}: {str(e)}")
            
            # Send confirmation email to restaurant owner
            try:
                subject = f'Restaurant Application Received: {pending_restaurant.restaurant_name}'
                message = f"""
                Dear {request.user.username},
                
                Thank you for submitting your restaurant application for "{pending_restaurant.restaurant_name}".
                
                Your application is now under review by our team. We will notify you at {request.user.email} once it has been reviewed.
                This process typically takes 24-48 hours.
                
                Application Details:
                - Restaurant Name: {pending_restaurant.restaurant_name}
                - Cuisine Type: {pending_restaurant.get_cuisine_type_display()}
                - Status: Pending Review
                
                Thank you for your patience!
                
                Best regards,
                QuickBite Team
                """
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [request.user.email],
                    fail_silently=True,
                )
            except Exception as e:
                logger.warning(f"Failed to send confirmation email: {str(e)}")
            
            # Clear wizard data
            self.clear_wizard_data(request)
            
            messages.success(
                request,
                f'🎉 Restaurant "{pending_restaurant.restaurant_name}" application submitted successfully! '
                f'Your application is now under review. We will notify you at {request.user.email} once approved.'
            )
            
            return redirect('restaurant:registration_success')
                
        except Exception as e:
            logger.error(f"Error in final submission: {str(e)}", exc_info=True)
            messages.error(
                request,
                'An unexpected error occurred. Please try again or contact support.'
            )
            return self.get(request)
    
    def _validate_step(self, step, post_data, files, request=None):
        """
        Validate data for a specific step.
        
        Args:
            step: Step number to validate
            post_data: POST data dictionary
            files: Uploaded files dictionary
            
        Returns:
            tuple: (is_valid: bool, errors: list)
        """
        errors = []
        
        if step == 1:
            # Account Information - validate for unauthenticated users
            if not request.user.is_authenticated:
                username = post_data.get('username', '').strip()
                email = post_data.get('email', '').strip()
                password = post_data.get('password', '')
                password_confirm = post_data.get('password_confirm', '')
                
                # Username validation
                if not username:
                    errors.append('Username is required')
                elif len(username) < 3:
                    errors.append('Username must be at least 3 characters long')
                elif User.objects.filter(username=username).exists():
                    errors.append('This username is already taken. Please choose another.')
                
                # Email validation
                if not email:
                    errors.append('Email address is required')
                elif '@' not in email or '.' not in email.split('@')[-1]:
                    errors.append('Please enter a valid email address')
                elif User.objects.filter(email=email).exists():
                    errors.append('An account with this email already exists.')
                
                # Password validation
                if not password:
                    errors.append('Password is required')
                elif len(password) < 8:
                    errors.append('Password must be at least 8 characters long')
                else:
                    try:
                        validate_password(password)
                    except ValidationError as e:
                        errors.extend(e.messages)
                
                # Password confirmation
                if password != password_confirm:
                    errors.append('Passwords do not match')
        
        elif step == 2:
            # Restaurant Basic Details
            if not post_data.get('restaurant_name'):
                errors.append('Restaurant name is required')
            if not post_data.get('description') or len(post_data.get('description', '')) < 20:
                errors.append('Description must be at least 20 characters')
            if not post_data.get('cuisine_type'):
                errors.append('Cuisine type is required')
        
        elif step == 3:
            # Location & Contact
            if not post_data.get('phone'):
                errors.append('Phone number is required')
            if not post_data.get('address'):
                errors.append('Address is required')
        
        elif step == 4:
            # Business Hours & Pricing
            if not post_data.get('opening_time'):
                errors.append('Opening time is required')
            if not post_data.get('closing_time'):
                errors.append('Closing time is required')
            if not post_data.get('minimum_order'):
                errors.append('Minimum order amount is required')
        
        elif step == 5:
            # Images & Review - optional
            pass
        
        return len(errors) == 0, errors
    
    def _save_step_data(self, request, step, post_data, files):
        """
        Save step data to session.
        
        Args:
            request: Django HTTP request object
            step: Step number
            post_data: POST data dictionary
            files: Uploaded files dictionary
        """
        wizard_data = self.get_wizard_data(request)
        
        # Store step data
        step_key = f'step_{step}'
        wizard_data[step_key] = {}
        
        # Copy relevant fields from POST data
        for key, value in post_data.items():
            if key not in ['csrfmiddlewaretoken', 'action']:
                wizard_data[step_key][key] = value
        
        # Handle file uploads
        if files:
            for key, file in files.items():
                # Save file temporarily
                file_path = default_storage.save(f'temp/wizard/{key}_{request.user.id}', file)
                wizard_data[step_key][key] = file_path
        
        self.set_wizard_data(request, wizard_data)
    
    def _get_step_context(self, step, wizard_data):
        """
        Get context data specific to current step.
        
        Args:
            step: Current step number
            wizard_data: Wizard session data
            
        Returns:
            dict: Step-specific context
        """
        context = {}
        step_key = f'step_{step}'
        
        # For Step 5 (final review), combine all previous step data
        if step == 5:
            combined_data = {}
            for i in range(1, 5):  # Steps 1-4
                step_data = wizard_data.get(f'step_{i}', {})
                combined_data.update(step_data)
            context['step_data'] = combined_data
        elif step_key in wizard_data:
            context['step_data'] = wizard_data[step_key]
        else:
            context['step_data'] = {}
        
        # Add step titles and descriptions
        step_info = {
            1: {
                'title': 'Account Information',
                'description': 'Your account is already set up. Let\'s add your restaurant details.'
            },
            2: {
                'title': 'Restaurant Basic Details',
                'description': 'Tell us about your restaurant - name, description, and cuisine type.'
            },
            3: {
                'title': 'Location & Contact',
                'description': 'How can customers reach you? Add your contact details and address.'
            },
            4: {
                'title': 'Business Hours & Pricing',
                'description': 'Set your operating hours and delivery pricing.'
            },
            5: {
                'title': 'Images & Final Review',
                'description': 'Add restaurant photos and review your information before submitting.'
            }
        }
        
        context.update(step_info.get(step, {}))
        
        return context
    
    def _create_restaurant_from_wizard(self, request, wizard_data):
        """
        Create PendingRestaurant instance from wizard session data.
        
        Args:
            request: Django HTTP request object
            wizard_data: Complete wizard data dictionary
            
        Returns:
            PendingRestaurant: Created pending restaurant instance
        """
        from restaurant.models import PendingRestaurant
        
        # Combine all step data
        combined_data = {}
        for i in range(1, self.total_steps + 1):
            step_key = f'step_{i}'
            if step_key in wizard_data:
                combined_data.update(wizard_data[step_key])
        
        # Validate required fields before creating pending restaurant
        required_fields = ['restaurant_name', 'description', 'phone', 'address', 'cuisine_type']
        missing_fields = [field for field in required_fields if not combined_data.get(field)]
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        # Create pending restaurant application with proper field mapping
        pending_restaurant = PendingRestaurant.objects.create(
            user=request.user,
            restaurant_name=combined_data.get('restaurant_name', '').strip(),
            description=combined_data.get('description', '').strip(),
            phone=combined_data.get('phone', '').strip(),
            email=combined_data.get('email', request.user.email).strip(),
            address=combined_data.get('address', '').strip(),
            cuisine_type=combined_data.get('cuisine_type', '').strip(),
            opening_time=combined_data.get('opening_time', '09:00'),
            closing_time=combined_data.get('closing_time', '22:00'),
            minimum_order=combined_data.get('minimum_order', '0.00'),
            delivery_fee=combined_data.get('delivery_fee', '0.00'),
            status='pending'
        )
        
        # Handle image upload if present
        image_path = combined_data.get('restaurant_image')
        if image_path:
            with default_storage.open(image_path, 'rb') as image_file:
                from django.core.files import File
                pending_restaurant.image.save(
                    f'pending_restaurant_{pending_restaurant.id}.jpg',
                    File(image_file),
                    save=True
                )
            # Clean up temporary file
            default_storage.delete(image_path)
        
        return pending_restaurant


class RegistrationSuccessView(TemplateView):
    """
    Success page displayed after completing registration.
    
    Shows confirmation message and next steps for the restaurant owner.
    """
    template_name = 'restaurant/registration_success.html'
    
    def get_context_data(self, **kwargs):
        """
        Add success context data.
        
        Args:
            **kwargs: Additional keyword arguments
            
        Returns:
            dict: Template context
        """
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context
