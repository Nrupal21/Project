"""
OTP forms for the accounts app.

This module contains forms related to OTP (One-Time Password) functionality
for secure two-factor authentication.
"""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm

User = get_user_model()

class OTPVerificationForm(forms.Form):
    """
    Form for OTP verification during login.
    
    This form validates the OTP code entered by the user.
    """
    otp_code = forms.CharField(
        label="OTP Code",
        max_length=6,
        min_length=6,
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-input',
                'placeholder': 'Enter 6-digit OTP code',
                'autocomplete': 'one-time-code'
            }
        )
    )
    session_key = forms.UUIDField(widget=forms.HiddenInput())
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the OTP verification form.
        
        Sets up any additional form attributes and customizations.
        """
        super().__init__(*args, **kwargs)
        self.fields['otp_code'].widget.attrs.update({
            'autofocus': 'autofocus',
            'inputmode': 'numeric',
            'pattern': '[0-9]*'
        })


class OTPAuthenticationForm(AuthenticationForm):
    """
    Extended authentication form that includes a remember_me field.
    
    This form is used for the first step of OTP-based authentication.
    """
    remember_me = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'})
    )
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the authentication form.
        
        Sets up form fields with custom attributes for styling.
        """
        super().__init__(*args, **kwargs)
        
        # Add custom attributes to form fields
        self.fields['username'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Enter your email or username',
            'autofocus': 'autofocus'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': '••••••••'
        })
        self.fields['remember_me'].label = "Remember me for 30 days"
