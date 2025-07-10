"""
Forms for the accounts app.

This module contains form classes for user registration, authentication, and profile management.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import UserProfile, UserPreferences
from .otp_forms import OTPVerificationForm as BaseOTPVerificationForm

User = get_user_model()

class MobileOTPLoginForm(forms.Form):
    """
    Form for initiating mobile OTP login.
    
    This form collects the user's mobile number to send an OTP.
    """
    phone_number = forms.CharField(
        label=_('Phone Number'),
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('+1234567890'),
            'autocomplete': 'tel'
        })
    )
    
    def clean_phone_number(self):
        """
        Clean and validate the phone number.
        
        Returns:
            str: The cleaned phone number
            
        Raises:
            ValidationError: If the phone number is invalid
        """
        phone_number = self.cleaned_data.get('phone_number')
        # Add phone number validation logic here
        # Example: Ensure it starts with + and has at least 10 digits
        if not phone_number.startswith('+'):
            raise ValidationError(_('Please enter a valid phone number with country code (e.g., +1234567890)'))
        
        # Remove any non-digit characters except +
        digits = ''.join(c for c in phone_number if c.isdigit() or c == '+')
        if len(digits) < 10:  # Adjust the minimum length as needed
            raise ValidationError(_('Please enter a valid phone number'))
            
        return phone_number


class MobileOTPVerificationForm(forms.Form):
    """
    Form for verifying OTP sent to mobile.
    """
    otp_code = forms.CharField(
        label=_('OTP Code'),
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter 6-digit OTP'),
            'autocomplete': 'one-time-code',
            'inputmode': 'numeric',
            'pattern': '\d{6}'
        })
    )
    phone_number = forms.CharField(widget=forms.HiddenInput())
    
    def clean_otp_code(self):
        """
        Clean and validate the OTP code.
        
        Returns:
            str: The cleaned OTP code
            
        Raises:
            ValidationError: If the OTP code is invalid
        """
        otp_code = self.cleaned_data.get('otp_code')
        if not otp_code.isdigit() or len(otp_code) != 6:
            raise ValidationError(_('Please enter a valid 6-digit OTP code'))
        return otp_code


class MobileOTPCompleteForm(forms.Form):
    """
    Form for completing user registration after OTP verification.
    """
    email = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('your@example.com'),
            'autocomplete': 'email'
        })
    )
    full_name = forms.CharField(
        label=_('Full Name'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('John Doe'),
            'autocomplete': 'name'
        })
    )
    password1 = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Create a password'),
            'autocomplete': 'new-password'
        })
    )
    password2 = forms.CharField(
        label=_('Confirm Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Confirm your password'),
            'autocomplete': 'new-password'
        })
    )
    
    def clean_email(self):
        """
        Validate that the email is not already in use.
        """
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(_('A user with this email already exists.'))
        return email
    
    def clean(self):
        """
        Validate that the two password fields match.
        """
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            self.add_error('password2', _('Passwords do not match'))
            
        return cleaned_data
