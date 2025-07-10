"""
Mobile OTP authentication views.

This module contains views for handling mobile OTP-based authentication.
"""
import logging
from django.shortcuts import render, redirect
from django.views.generic import FormView, TemplateView, View
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from django.utils import timezone

from .forms import MobileOTPLoginForm, MobileOTPVerificationForm, MobileOTPCompleteForm
from .sms_otp import send_sms_otp, verify_otp, get_or_create_user_by_phone
from .models import CustomUser

logger = logging.getLogger(__name__)

class MobileOTPLoginView(FormView):
    """
    View for initiating mobile OTP login.
    
    This view handles the first step of the OTP login process where the user
    enters their phone number to receive an OTP.
    """
    template_name = 'accounts/mobile_otp_login.html'
    form_class = MobileOTPLoginForm
    success_url = reverse_lazy('accounts:mobile_otp_verify')
    
    def form_valid(self, form):
        """
        Process the form submission and send OTP to the provided phone number.
        """
        phone_number = form.cleaned_data['phone_number']
        
        # Generate and send OTP
        from .sms_otp import generate_otp_code
        otp_code = generate_otp_code()
        
        # In a production environment, you would uncomment this:
        # if not send_sms_otp(phone_number, otp_code):
        #     messages.error(self.request, 'Failed to send OTP. Please try again.')
        #     return self.form_invalid(form)
        
        # For development, we'll just log the OTP
        logger.info(f"OTP for {phone_number}: {otp_code}")
        
        # Store the OTP in the session
        self.request.session['otp_phone_number'] = phone_number
        self.request.session['otp_code'] = otp_code
        self.request.session['otp_created_at'] = timezone.now().isoformat()
        
        # Set the success URL with the phone number as a query parameter
        self.success_url = f"{reverse('accounts:mobile_otp_verify')}?phone={phone_number}"
        
        messages.info(self.request, f'OTP has been sent to {phone_number}')
        return super().form_valid(form)


class MobileOTPVerifyView(FormView):
    """
    View for verifying the OTP sent to the user's mobile.
    
    This view handles the second step of the OTP login process where the user
    enters the OTP they received on their phone.
    """
    template_name = 'accounts/mobile_otp_verify.html'
    form_class = MobileOTPVerificationForm
    
    def get_initial(self):
        """
        Set initial form data from the query parameters.
        """
        initial = super().get_initial()
        phone_number = self.request.GET.get('phone', '')
        if phone_number:
            initial['phone_number'] = phone_number
        return initial
    
    def get_context_data(self, **kwargs):
        """
        Add extra context to the template.
        """
        context = super().get_context_data(**kwargs)
        context['phone_number'] = self.request.GET.get('phone', '')
        return context
    
    def form_valid(self, form):
        """
        Verify the OTP and log the user in if valid.
        """
        phone_number = form.cleaned_data['phone_number']
        otp_code = form.cleaned_data['otp_code']
        
        # Verify the OTP
        is_valid, message = verify_otp(phone_number, otp_code)
        
        if not is_valid:
            form.add_error('otp_code', message)
            return self.form_invalid(form)
        
        # Get or create the user
        user, created = get_or_create_user_by_phone(phone_number)
        
        # Log the user in
        login(self.request, user)
        
        # Store user ID in session for the next step if this is a new user
        if created:
            self.request.session['new_user_id'] = str(user.id)
            return redirect('accounts:mobile_otp_complete')
        
        messages.success(self.request, 'Successfully logged in!')
        return redirect(settings.LOGIN_REDIRECT_URL)


class MobileOTPCompleteView(FormView):
    """
    View for completing user registration after OTP verification.
    
    This view is shown to new users after they verify their phone number.
    It collects additional information like email and password.
    """
    template_name = 'accounts/mobile_otp_complete.html'
    form_class = MobileOTPCompleteForm
    success_url = reverse_lazy('core:home')
    
    def dispatch(self, request, *args, **kwargs):
        """
        Ensure the user has a valid session before proceeding.
        """
        if 'new_user_id' not in request.session:
            return redirect('accounts:mobile_otp_login')
        return super().dispatch(request, *args, **kwargs)
    
    def get_user(self):
        """
        Get the user from the session.
        """
        try:
            user_id = self.request.session['new_user_id']
            return CustomUser.objects.get(id=user_id)
        except (KeyError, CustomUser.DoesNotExist):
            return None
    
    def get_context_data(self, **kwargs):
        """
        Add the user to the template context.
        """
        context = super().get_context_data(**kwargs)
        context['user'] = self.get_user()
        return context
    
    def form_valid(self, form):
        """
        Update the user with the provided information.
        """
        user = self.get_user()
        if not user:
            return redirect('accounts:mobile_otp_login')
        
        # Update user information
        user.email = form.cleaned_data['email']
        user.set_password(form.cleaned_data['password1'])
        user.save()
        
        # Log the user in
        login(self.request, user)
        
        # Clean up the session
        if 'new_user_id' in self.request.session:
            del self.request.session['new_user_id']
        
        messages.success(self.request, 'Registration complete! Welcome to our platform.')
        return super().form_valid(form)


@method_decorator(csrf_exempt, name='dispatch')
class MobileOTPResendView(View):
    """
    API endpoint for resending OTP.
    """
    def post(self, request, *args, **kwargs):
        """
        Handle OTP resend requests.
        """
        phone_number = request.POST.get('phone_number')
        
        if not phone_number:
            return JsonResponse({'success': False, 'error': 'Phone number is required'}, status=400)
        
        # Generate and send new OTP
        from .sms_otp import generate_otp_code
        otp_code = generate_otp_code()
        
        # In a production environment, you would uncomment this:
        # if not send_sms_otp(phone_number, otp_code):
        #     return JsonResponse({'success': False, 'error': 'Failed to send OTP'}, status=500)
        
        # For development, we'll just log the OTP
        logger.info(f"Resent OTP for {phone_number}: {otp_code}")
        
        # Store the new OTP in the session
        request.session['otp_phone_number'] = phone_number
        request.session['otp_code'] = otp_code
        request.session['otp_created_at'] = timezone.now().isoformat()
        
        return JsonResponse({'success': True, 'message': 'OTP has been resent'})
