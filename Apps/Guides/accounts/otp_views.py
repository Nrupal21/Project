"""
OTP views for the accounts app.

This module contains template-based views for OTP (One-Time Password) authentication
including verification and setup.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import FormView, TemplateView, View
from django.urls import reverse, reverse_lazy
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings

from .otp_models import OTPDevice, OTPSession
from .otp_forms import OTPVerificationForm, OTPAuthenticationForm
from .otp_utils import generate_otp_code, verify_otp, get_otp_expiry_timestamp, is_otp_expired
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64
import pyotp
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class OTPLoginView(FormView):
    """
    View for the first step of OTP-based login.
    
    This view handles the username/password authentication before OTP verification.
    """
    template_name = 'accounts/otp_login.html'
    form_class = OTPAuthenticationForm
    
    def form_valid(self, form):
        """
        Process valid form data for OTP login first step.
        
        Authenticates the user credentials and redirects to OTP verification
        if credentials are valid.
        
        Args:
            form: The submitted form with validated data
            
        Returns:
            HttpResponse: Redirect to OTP verification or error
        """
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        remember_me = form.cleaned_data.get('remember_me', False)
        
        # Authenticate user
        user = authenticate(
            request=self.request,
            username=username,
            password=password
        )
        
        if user is None:
            messages.error(self.request, 'Invalid username or password')
            return self.form_invalid(form)
            
        # Check if user has OTP enabled
        try:
            otp_device = OTPDevice.objects.get(user=user)
            if not otp_device.is_verified:
                # If OTP is not verified, redirect to OTP setup
                return redirect('accounts:otp_setup')
                
            # Create OTP session
            session = OTPSession.create_session(user)
            
            # Store user ID in session for the next step
            self.request.session['otp_user_id'] = user.id
            
            # Redirect to OTP verification
            return redirect('otp:request_otp')
            
        except OTPDevice.DoesNotExist:
            # If no OTP device, log the user in directly
            login(self.request, user)
            
            # Set session expiry based on remember me
            if not remember_me:
                self.request.session.set_expiry(0)  # Browser session
                
            # Set OTP verified flag
            self.request.session['otp_verified'] = True
            
            # Redirect to success URL
            return redirect(settings.LOGIN_REDIRECT_URL)
            
        except Exception as e:
            logger.error(f'Error during OTP login: {str(e)}')
            messages.error(self.request, 'An error occurred during login. Please try again.')
            return self.form_invalid(form)
        
        # Authenticate user credentials
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # Store remember_me preference in session
            self.request.session['remember_me'] = remember_me
            
            # Check if user has OTP device
            try:
                otp_device = user.otp_device
                
                # Create OTP session
                otp_session = OTPSession.create_session(user)
                
                # Redirect to OTP verification page
                return redirect(reverse('accounts:otp_verify', kwargs={'session_key': otp_session.session_key}))
                
            except OTPDevice.DoesNotExist:
                # User doesn't have OTP set up yet, create one
                otp_device = OTPDevice(user=user)
                secret_key = otp_device.generate_secret_key()
                otp_device.save()
                
                # Create OTP session
                otp_session = OTPSession.create_session(user)
                
                # Redirect to OTP setup page
                return redirect(reverse('accounts:otp_setup', kwargs={'session_key': otp_session.session_key}))
        
        # Authentication failed
        messages.error(self.request, 'Invalid username or password.')
        return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        """
        Add extra context data to be passed to the template.
        
        Args:
            **kwargs: Additional context data
            
        Returns:
            dict: Context data for the template
        """
        context = super().get_context_data(**kwargs)
        context['title'] = 'Log In with OTP'
        return context


@method_decorator(csrf_exempt, name='dispatch')
class OTPVerifyView(FormView):
    """
    View for verifying OTP code during login.
    
    This is the second step of the OTP-based login process.
    """
    template_name = 'accounts/otp_verify.html'
    form_class = OTPVerificationForm
    success_url = reverse_lazy('core:home')
    
    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to handle AJAX requests.
        """
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return self.ajax_verify_otp(request)
        return super().dispatch(request, *args, **kwargs)
    
    def ajax_verify_otp(self, request):
        """
        Handle AJAX requests for OTP verification.
        
        Args:
            request: The HTTP request
            
        Returns:
            JsonResponse: JSON response with success/error status
        """
        if request.method != 'POST':
            return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)
            
        otp_code = request.POST.get('otp_code')
        session_key = request.POST.get('session_key')
        
        if not otp_code or not session_key:
            return JsonResponse(
                {'success': False, 'message': 'OTP code and session key are required'}, 
                status=400
            )
            
        try:
            # Get the OTP session
            session = OTPSession.objects.get(
                session_key=session_key,
                is_verified=False,
                expires_at__gt=timezone.now()
            )
            
            # Get the OTP device
            try:
                otp_device = OTPDevice.objects.get(user=session.user)
            except OTPDevice.DoesNotExist:
                return JsonResponse(
                    {'success': False, 'message': 'OTP device not found'}, 
                    status=400
                )
                
            # Verify the OTP code
            if not verify_otp(otp_device.secret_key, otp_code):
                return JsonResponse(
                    {'success': False, 'message': 'Invalid verification code'}, 
                    status=400
                )
                
            # Mark session as verified
            session.is_verified = True
            session.save()
            
            # Log the user in
            login(request, session.user)
            
            # Set OTP verified flag in session
            request.session['otp_verified'] = True
            
            return JsonResponse({
                'success': True, 
                'redirect_url': self.get_success_url()
            })
            
        except OTPSession.DoesNotExist:
            return JsonResponse(
                {'success': False, 'message': 'Invalid or expired session'}, 
                status=400
            )
        except Exception as e:
            logger.error(f'Error verifying OTP: {str(e)}')
            return JsonResponse(
                {'success': False, 'message': 'An error occurred. Please try again.'}, 
                status=500
            )
    
    def get_success_url(self):
        """
        Get the URL to redirect to after successful verification.
        
        Returns:
            str: The success URL
        """
        next_url = self.request.GET.get('next') or self.request.session.get('next')
        if next_url:
            return next_url
        return super().get_success_url()
    
    def get_context_data(self, **kwargs):
        """
        Add extra context to the template.
        
        Returns:
            dict: Template context
        """
        context = super().get_context_data(**kwargs)
        context['session_key'] = self.kwargs.get('session_key')
        return context
    
    def get_initial(self):
        """
        Provide initial data for the form.
        
        Sets the session key from the URL in the hidden form field.
        
        Returns:
            dict: Initial form data
        """
        initial = super().get_initial()
        initial['session_key'] = self.kwargs.get('session_key')
        return initial
    
    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to the OTP verification page.
        
        Validates the OTP session before showing the verification form.
        
        Args:
            request: The HTTP request
            *args, **kwargs: Additional arguments and keyword arguments
            
        Returns:
            HttpResponse: Response for GET request
        """
        session_key = self.kwargs.get('session_key')
        
        # Check if session exists and is valid
        try:
            otp_session = OTPSession.objects.get(session_key=session_key)
            
            # Check if session is expired
            if otp_session.is_expired:
                messages.error(request, 'OTP verification session has expired. Please login again.')
                return redirect('accounts:otp_login')
                
            # Continue to verification form
            return super().get(request, *args, **kwargs)
            
        except OTPSession.DoesNotExist:
            messages.error(request, 'Invalid verification session. Please login again.')
            return redirect('accounts:otp_login')
    
    def form_valid(self, form):
        """
        Process valid form data for OTP verification.
        
        Verifies the OTP code and completes login if valid.
        
        Args:
            form: The submitted form with validated data
            
        Returns:
            HttpResponse: Redirect after successful verification
        """
        session_key = form.cleaned_data.get('session_key')
        otp_code = form.cleaned_data.get('otp_code')
        
        try:
            # Get the OTP session
            otp_session = OTPSession.objects.get(session_key=session_key)
            
            # Get the user's OTP device
            otp_device = otp_session.user.otp_device
            
            # Verify OTP code
            is_valid = otp_device.verify_otp(otp_code)
            
            if is_valid:
                # Mark session as verified
                otp_session.is_verified = True
                otp_session.save()
                
                # Mark device as verified if not already
                if not otp_device.is_verified:
                    otp_device.is_verified = True
                    otp_device.save()
                
                # Complete login
                user = otp_session.user
                login(self.request, user)
                
                # Set session expiry based on remember_me
                remember_me = self.request.session.get('remember_me', False)
                if not remember_me:
                    # Session expires when browser is closed
                    self.request.session.set_expiry(0)
                else:
                    # Session expires after 30 days
                    self.request.session.set_expiry(60 * 60 * 24 * 30)
                
                messages.success(self.request, f'Welcome back, {user.get_full_name() or user.username}!')
                return super().form_valid(form)
            else:
                messages.error(self.request, 'Invalid OTP code. Please try again.')
                return self.form_invalid(form)
                
        except (OTPSession.DoesNotExist, OTPDevice.DoesNotExist):
            messages.error(self.request, 'Invalid verification session. Please login again.')
            return redirect('accounts:otp_login')
    
    def get_context_data(self, **kwargs):
        """
        Add extra context data to be passed to the template.
        
        Adds information about the OTP session and user to the template context.
        
        Args:
            **kwargs: Additional context data
            
        Returns:
            dict: Context data for the template
        """
        context = super().get_context_data(**kwargs)
        
        try:
            session_key = self.kwargs.get('session_key')
            otp_session = OTPSession.objects.get(session_key=session_key)
            context['user_email'] = otp_session.user.email
            context['expiry_time'] = otp_session.expires_at
            context['title'] = 'Verify OTP'
        except OTPSession.DoesNotExist:
            pass
            
        return context


class OTPSetupView(LoginRequiredMixin, TemplateView):
    """
    View for setting up OTP for a user.
    
    This view helps users set up OTP authentication by showing QR code
    and handling verification.
    """
    template_name = 'accounts/otp_setup.html'
    
    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to the OTP setup page.
        
        Shows the OTP setup form with QR code.
        
        Args:
            request: The HTTP request
            *args, **kwargs: Additional arguments and keyword arguments
            
        Returns:
            HttpResponse: Response for GET request
        """
        session_key = kwargs.get('session_key')
        
        try:
            # Get the OTP session
            otp_session = OTPSession.objects.get(session_key=session_key)
            
            if otp_session.is_expired:
                messages.error(request, 'OTP setup session has expired. Please login again.')
                return redirect('accounts:otp_login')
            
            # Get or create OTP device
            otp_device, created = OTPDevice.objects.get_or_create(user=otp_session.user)
            
            if not otp_device.secret_key:
                otp_device.generate_secret_key()
                
            # Generate QR code
            totp_uri = pyotp.totp.TOTP(otp_device.secret_key).provisioning_uri(
                name=otp_session.user.email,
                issuer_name='TravelGuide'
            )
            
            # Create QR code image
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(totp_uri)
            qr.make(fit=True)
            
            # Create SVG QR code
            img = qr.make_image(image_factory=qrcode.image.svg.SvgImage)
            stream = BytesIO()
            img.save(stream)
            
            # Convert SVG to base64 for embedding in HTML
            svg_base64 = base64.b64encode(stream.getvalue()).decode('utf-8')
            
            # Prepare context
            context = {
                'session_key': session_key,
                'qr_code': svg_base64,
                'secret_key': otp_device.secret_key,
                'user_email': otp_session.user.email,
                'title': 'Set Up OTP Authentication'
            }
            
            return render(request, self.template_name, context)
            
        except OTPSession.DoesNotExist:
            messages.error(request, 'Invalid setup session. Please login again.')
            return redirect('accounts:otp_login')
    
    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to verify OTP setup.
        
        Verifies the OTP code entered during setup and completes login if valid.
        
        Args:
            request: The HTTP request
            *args, **kwargs: Additional arguments and keyword arguments
            
        Returns:
            HttpResponse: Response for POST request
        """
        session_key = kwargs.get('session_key')
        otp_code = request.POST.get('otp_code')
        
        if not otp_code:
            messages.error(request, 'OTP code is required.')
            return redirect(reverse('accounts:otp_setup', kwargs={'session_key': session_key}))
        
        try:
            # Get the OTP session
            otp_session = OTPSession.objects.get(session_key=session_key)
            
            # Get the OTP device
            otp_device = otp_session.user.otp_device
            
            # Verify OTP code
            is_valid = otp_device.verify_otp(otp_code)
            
            if is_valid:
                # Mark device and session as verified
                otp_device.is_verified = True
                otp_device.save()
                
                otp_session.is_verified = True
                otp_session.save()
                
                # Complete login
                user = otp_session.user
                login(request, user)
                
                # Set session expiry based on remember_me
                remember_me = request.session.get('remember_me', False)
                if not remember_me:
                    # Session expires when browser is closed
                    request.session.set_expiry(0)
                else:
                    # Session expires after 30 days
                    request.session.set_expiry(60 * 60 * 24 * 30)
                
                messages.success(request, 'OTP setup successful! Your account is now protected with two-factor authentication.')
                return redirect('core:home')
            else:
                messages.error(request, 'Invalid OTP code. Please try again.')
                return redirect(reverse('accounts:otp_setup', kwargs={'session_key': session_key}))
                
        except (OTPSession.DoesNotExist, OTPDevice.DoesNotExist):
            messages.error(request, 'Invalid setup session. Please login again.')
            return redirect('accounts:otp_login')


class OTPManageView(LoginRequiredMixin, TemplateView):
    """
    View for managing OTP settings for an authenticated user.
    
    This view allows users to enable, disable, or reset their OTP configuration.
    """
    template_name = 'accounts/otp_manage.html'
    
    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to manage OTP settings.
        
        Args:
            request: The HTTP request
            
        Returns:
            HttpResponse: Redirect to the same page with status message
        """
        action = request.POST.get('action')
        
        try:
            otp_device = OTPDevice.objects.get(user=request.user)
            
            if action == 'disable':
                # Disable OTP
                otp_device.delete()
                messages.success(request, 'Two-factor authentication has been disabled.')
            elif action == 'regenerate':
                # Regenerate secret key
                otp_device.generate_secret_key()
                messages.success(request, 'Your OTP secret key has been regenerated. Please update your authenticator app.')
            
        except OTPDevice.DoesNotExist:
            if action == 'enable':
                # Create new OTP device
                OTPDevice.objects.create(user=request.user)
                messages.success(request, 'Two-factor authentication has been enabled. Please complete the setup.')
                return redirect('otp:setup')
        
        return redirect('otp:manage')
    
    def get_context_data(self, **kwargs):
        """
        Add extra context data to be passed to the template.
        
        Adds OTP status information to the template context.
        
        Args:
            **kwargs: Additional context data
            
        Returns:
            dict: Context data for the template
        """
        context = super().get_context_data(**kwargs)
        
        # Check if user has OTP enabled
        try:
            otp_device = self.request.user.otp_device
            context['has_otp'] = True
            context['is_verified'] = otp_device.is_verified
        except OTPDevice.DoesNotExist:
            context['has_otp'] = False
            context['is_verified'] = False
        
        context['title'] = 'Manage 2FA Settings'
        return context
    
    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to manage OTP settings.
        
        Processes actions like enabling, disabling, or resetting OTP.
        
        Args:
            request: The HTTP request
            *args, **kwargs: Additional arguments and keyword arguments
            
        Returns:
            HttpResponse: Response for POST request
        """
        action = request.POST.get('action')
        
        if action == 'disable':
            # Disable OTP
            try:
                otp_device = request.user.otp_device
                otp_device.delete()
                messages.success(request, 'Two-factor authentication has been disabled.')
            except OTPDevice.DoesNotExist:
                pass
                
        elif action == 'reset':
            # Reset OTP
            try:
                otp_device = request.user.otp_device
                otp_device.delete()
            except OTPDevice.DoesNotExist:
                pass
                
            # Create new OTP device
            otp_device = OTPDevice(user=request.user)
            secret_key = otp_device.generate_secret_key()
            otp_device.save()
            
            # Redirect to setup page
            otp_session = OTPSession.create_session(request.user)
            return redirect(reverse('accounts:otp_setup', kwargs={'session_key': otp_session.session_key}))
            
        elif action == 'enable':
            # Enable OTP
            try:
                # Check if already exists
                otp_device = request.user.otp_device
            except OTPDevice.DoesNotExist:
                # Create new OTP device
                otp_device = OTPDevice(user=request.user)
                secret_key = otp_device.generate_secret_key()
                otp_device.save()
            
            # Redirect to setup page
            otp_session = OTPSession.create_session(request.user)
            return redirect(reverse('accounts:otp_setup', kwargs={'session_key': otp_session.session_key}))
        
        return redirect(reverse('accounts:otp_manage'))
