"""
OTP Views for handling OTP authentication.

This module contains views for OTP generation, verification, and authentication.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from .otp_service import OTPService

@login_required
def request_otp(request):
    """
    View to request an OTP code for login verification.
    
    This view generates a new OTP code for the logged-in user and displays
    the OTP input form.
    
    Args:
        request: The HTTP request object
        
    Returns:
        HttpResponse: The OTP input page
    """
    # Generate OTP code
    otp_code, otp_uri = OTPService.generate_otp(request.user)
    
    # In a production environment, you would send the OTP via email or SMS
    # For demo purposes, we'll store it in the session
    request.session['otp_code'] = otp_code
    
    # Create OTP session
    session = OTPService.create_otp_session(request.user)
    
    context = {
        'otp_uri': otp_uri,
        'session_key': str(session.session_key)
    }
    
    return render(request, 'accounts/otp_verify.html', context)

@csrf_exempt
def verify_otp(request):
    """
    View to verify the OTP code and complete authentication.
    
    This view verifies the provided OTP code and logs the user in if valid.
    
    Args:
        request: The HTTP request object
        
    Returns:
        JsonResponse: JSON response with success/error status
    """
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code', '')
        session_key = request.POST.get('session_key', '')
        
        if not otp_code or not session_key:
            return JsonResponse({
                'success': False,
                'message': 'OTP code and session key are required'
            }, status=400)
        
        # Verify OTP
        is_valid, message = OTPService.verify_otp_session(session_key, otp_code)
        
        if is_valid:
            # Clear the OTP code from session
            if 'otp_code' in request.session:
                del request.session['otp_code']
            
            # Set session variable to indicate OTP is verified
            request.session['otp_verified'] = True
            
            return JsonResponse({
                'success': True,
                'redirect_url': settings.LOGIN_REDIRECT_URL or '/'
            })
        
        return JsonResponse({
            'success': False,
            'message': message
        }, status=400)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)

def otp_required(view_func):
    """
    Decorator to ensure OTP verification is completed.
    
    This decorator checks if the user has completed OTP verification.
    If not, it redirects them to the OTP verification page.
    
    Args:
        view_func: The view function to decorate
        
    Returns:
        function: The decorated view function
    """
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
            
        if not request.session.get('otp_verified', False):
            return redirect('request_otp')
            
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view
