"""
Email Verification Views Module.

This module contains view functions for email verification flows in the TravelGuide application,
including verification confirmation, verification required page, and resend verification endpoint.

All views include appropriate security measures, error handling, and user feedback mechanisms.
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import ensure_csrf_cookie

from .email_verification import (
    verify_user_email,
    send_verification_email,
    check_verification_status,
)

# Configure logger
logger = logging.getLogger(__name__)

# Get the User model
User = get_user_model()


def verify_email_view(request, uidb64, token):
    """
    Handle the email verification link clicked by users.
    
    This view is accessed when a user clicks on the verification link in their email.
    It validates the token, updates the user's verification status, and provides
    appropriate feedback.
    
    Args:
        request: HttpRequest object
        uidb64: URL-safe base64 encoded user ID
        token: Verification token to validate
        
    Returns:
        HttpResponse: Rendered verification confirmation page or error page
    """
    # Verify the token and get the user
    success, user = verify_user_email(uidb64, token)
    
    context = {}
    
    if success and user:
        # Verification successful
        logger.info(f"Email verification successful for user {user.email}")
        
        # Add success message
        messages.success(request, _("Your email has been successfully verified. You now have full access to all TravelGuide features!"))
        
        # If user is authenticated, redirect to profile
        if request.user.is_authenticated:
            return redirect('accounts:profile')
        else:
            # Otherwise redirect to login with success message
            return redirect('accounts:login')
    else:
        # Verification failed - show error page
        logger.warning(f"Email verification failed for token: {token[:10]}...")
        
        # Add error message
        messages.error(request, _("Email verification failed. The link may be invalid or expired. Please request a new verification email."))
        
        context = {
            'verification_success': False,
            'title': _("Verification Failed"),
            'message': _("The verification link is invalid or has expired. Please request a new verification email from your account settings.")
        }
        
        # Show verification failed page
        return render(request, 'accounts/verification_result.html', context)


@login_required
def verification_required_view(request):
    """
    Show a page informing users that email verification is required.
    
    This view is shown when a user attempts to access a feature that requires
    email verification, but their email hasn't been verified yet.
    
    Args:
        request: HttpRequest object
        
    Returns:
        HttpResponse: Rendered verification required page
    """
    # Check if the user's email is already verified
    if check_verification_status(request.user):
        # If already verified, redirect to profile
        messages.info(request, _("Your email has already been verified."))
        return redirect('accounts:profile')
    
    # Prepare context
    context = {
        'user': request.user,
        'title': _("Email Verification Required"),
        'verification_sent': True,  # Assume verification was sent during registration
    }
    
    # Show verification required page
    return render(request, 'accounts/verification_required.html', context)


@login_required
@require_http_methods(["POST"])
@ensure_csrf_cookie
def resend_verification_email_view(request):
    """
    Resend the verification email to the user.
    
    This endpoint is called via AJAX when a user requests a new verification email.
    It includes rate limiting to prevent abuse.
    
    Args:
        request: HttpRequest object
        
    Returns:
        JsonResponse: JSON response with success/error message
    """
    user = request.user
    
    # Check if the user's email is already verified
    if check_verification_status(user):
        return JsonResponse({
            'success': False,
            'message': _("Your email address has already been verified.")
        })
    
    # Implement rate limiting (allow 1 email every 5 minutes)
    cache_key = f"email_verification_resend_{user.id}"
    if cache.get(cache_key):
        # Too many requests - return error
        return JsonResponse({
            'success': False,
            'message': _("Please wait at least 5 minutes before requesting another verification email.")
        }, status=429)
    
    # Set rate limiting cache
    cache.set(cache_key, True, 300)  # 5 minutes (300 seconds)
    
    # Send verification email
    try:
        success = send_verification_email(request, user)
        
        if success:
            # Email sent successfully
            logger.info(f"Verification email resent to {user.email}")
            return JsonResponse({
                'success': True,
                'message': _("Verification email sent successfully. Please check your inbox.")
            })
        else:
            # Error sending email
            logger.error(f"Failed to resend verification email to {user.email}")
            return JsonResponse({
                'success': False,
                'message': _("An error occurred while sending the verification email. Please try again later.")
            }, status=500)
            
    except Exception as e:
        # Log the error
        logger.exception(f"Error in resend_verification_email_view: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': _("An unexpected error occurred. Please try again later.")
        }, status=500)


def create_verification_result_template():
    """
    Create the verification result template if it doesn't exist.
    
    This is an auxiliary function that ensures the necessary template exists.
    It's only used once during initial setup.
    
    Returns:
        bool: True if template was created, False if it already exists
    """
    # This is a helper function to create the template file
    # Not meant to be called as a view
    
    import os
    from django.conf import settings
    
    template_path = os.path.join(settings.BASE_DIR, 'templates', 'accounts', 'verification_result.html')
    
    # Check if the file already exists
    if os.path.exists(template_path):
        return False
        
    # Create the template file
    os.makedirs(os.path.dirname(template_path), exist_ok=True)
    
    template_content = """{% extends "base.html" %}
{% load static %}

{# Page title for browser tab #}
{% block title %}{{ title }} - TravelGuide{% endblock %}

{# Main content block #}
{% block content %}
<div class="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
    <div class="sm:mx-auto sm:w-full sm:max-w-md">
        {# TravelGuide Logo #}
        <div class="flex justify-center">
            <img class="h-16 w-auto" src="{% static 'images/logo.png' %}" alt="TravelGuide Logo">
        </div>
        
        {# Page heading #}
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
            {{ title }}
        </h2>
    </div>

    <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div class="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
            {# Success and error messages display #}
            {% if messages %}
                {% for message in messages %}
                    <div class="mb-4 {% if message.tags == 'success' %}bg-green-100 border-green-400 text-green-700{% elif message.tags == 'error' %}bg-red-100 border-red-400 text-red-700{% else %}bg-blue-100 border-blue-400 text-blue-700{% endif %} px-4 py-3 rounded relative" role="alert">
                        <span class="block sm:inline">{{ message }}</span>
                    </div>
                {% endfor %}
            {% endif %}
            
            {# Main content with result #}
            <div class="text-center">
                {% if verification_success %}
                    {# Success icon #}
                    <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
                        <svg class="h-6 w-6 text-green-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                    </div>
                    <h3 class="text-lg leading-6 font-medium text-gray-900">Email Verified Successfully</h3>
                    <p class="mt-2 text-sm text-gray-500">
                        Thank you! Your email address has been verified. You now have full access to all TravelGuide features.
                    </p>
                    
                    {# Continue button #}
                    <div class="mt-6">
                        <a href="{% url 'accounts:profile' %}" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                            Continue to Your Profile
                        </a>
                    </div>
                {% else %}
                    {# Error icon #}
                    <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
                        <svg class="h-6 w-6 text-red-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <h3 class="text-lg leading-6 font-medium text-gray-900">Verification Failed</h3>
                    <p class="mt-2 text-sm text-gray-500">
                        {{ message }}
                    </p>
                    
                    {# Try again options #}
                    <div class="mt-6">
                        {% if user.is_authenticated %}
                            <a href="{% url 'accounts:verification_required' %}" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                                Request a New Verification Email
                            </a>
                        {% else %}
                            <a href="{% url 'accounts:login' %}" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                                Log In to Request New Verification
                            </a>
                        {% endif %}
                    </div>
                {% endif %}
            </div>
            
            {# Return to home link #}
            <div class="mt-6 text-center">
                <a href="{% url 'home' %}" class="text-sm font-medium text-indigo-600 hover:text-indigo-500">
                    Return to Home Page
                </a>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""
    
    with open(template_path, 'w') as f:
        f.write(template_content)
        
    return True
