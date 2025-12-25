#!/usr/bin/env python
"""
Test Password Reset Functionality
Tests the complete password reset flow to identify why emails aren't being sent
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

def test_password_reset_flow():
    """
    Test the complete password reset flow
    """
    print("=" * 60)
    print("TESTING PASSWORD RESET FLOW")
    print("=" * 60)
    
    User = get_user_model()
    client = Client()
    
    # Check if test user exists, create if not
    test_email = 'test@example.com'
    if not User.objects.filter(email=test_email).exists():
        print(f"Creating test user: {test_email}")
        User.objects.create_user(
            username='testuser',
            email=test_email,
            password='testpass123'
        )
        print("✅ Test user created")
    else:
        print(f"✅ Test user {test_email} already exists")
    
    # Test password reset request
    print(f"\nTesting password reset request for: {test_email}")
    
    # Get the password reset URL
    reset_url = reverse('core:password_reset')
    print(f"Password reset URL: {reset_url}")
    
    # Submit password reset form
    response = client.post(reset_url, {'email': test_email})
    
    print(f"Response status code: {response.status_code}")
    print(f"Response redirects to: {response.get('Location', 'No redirect')}")
    
    if response.status_code == 302:
        print("✅ Password reset form submitted successfully")
        print("✅ Email should have been sent (check console output)")
    else:
        print("❌ Password reset form submission failed")
        print(f"Response content: {response.content.decode()}")
    
    return response.status_code == 302

def check_email_backend_settings():
    """
    Check and explain current email backend settings
    """
    print("\n" + "=" * 60)
    print("CURRENT EMAIL SETTINGS")
    print("=" * 60)
    
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
    print(f"EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
    print(f"EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Not set')}")
    print(f"EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'Not set')}")
    
    if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
        print("\n🔍 DIAGNOSIS:")
        print("You are using the CONSOLE email backend.")
        print("This means emails are printed to the console, NOT sent via SMTP.")
        print("\n📧 TO RECEIVE ACTUAL EMAILS:")
        print("1. Change EMAIL_BACKEND in settings.py to:")
        print("   EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'")
        print("2. Ensure SMTP settings are properly configured")
        print("3. Run the server and check your email inbox")
        
        return False
    else:
        print("\n✅ You are using SMTP email backend")
        print("Emails should be sent to the actual email addresses")
        return True

def main():
    """
    Main function to run password reset tests
    """
    print("🔐 Password Reset Testing - Food Ordering System")
    print("=" * 60)
    
    # Check email settings
    smtp_configured = check_email_backend_settings()
    
    # Test password reset flow
    reset_success = test_password_reset_flow()
    
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    
    if not smtp_configured:
        print("🔧 ISSUE IDENTIFIED:")
        print("Email backend is set to console mode")
        print("Emails are being printed to console, not sent to your inbox")
        print("\n📋 NEXT STEPS:")
        print("1. Check the console output above for the password reset email")
        print("2. To receive actual emails, update settings.py to use SMTP backend")
        print("3. Test with a real email address after configuring SMTP")
    elif reset_success:
        print("✅ Password reset is working correctly!")
        print("Check your email inbox for the reset link")
    else:
        print("❌ Password reset test failed")
        print("Check the error messages above")
    
    print(f"\n🌐 To test manually, visit: http://localhost:8000/auth/password-reset/")

if __name__ == '__main__':
    main()
