#!/usr/bin/env python
"""
Test Password Reset Email Validation
Debug script to verify if custom password reset view is working
"""

import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

def test_password_reset_validation():
    """
    Test if the custom password reset view is working
    """
    print("=" * 60)
    print("TESTING PASSWORD RESET VALIDATION")
    print("=" * 60)
    
    client = Client()
    
    # Test with non-existent email
    print("🔍 Testing with NON-EXISTENT email...")
    fake_email = 'nonexistent12345@test.com'
    
    response = client.post('/auth/password-reset/', {
        'email': fake_email
    })
    
    print(f"Response status: {response.status_code}")
    print(f"Redirect location: {response.get('Location', 'No redirect')}")
    
    if response.status_code == 302:
        print("✅ Form submitted and redirected")
        
        # Follow redirect to see success page
        follow_response = client.get(response['Location'])
        print(f"Success page status: {follow_response.status_code}")
        
        # Check if success message is shown
        content = follow_response.content.decode()
        if 'Password reset instructions have been sent' in content:
            print("✅ Success message shown")
        elif 'If your email address is registered' in content:
            print("✅ Generic success message shown (good for security)")
        else:
            print("⚠️  Unexpected success message")
            print(f"Content preview: {content[:200]}...")
    
    # Test with existing email
    print(f"\n🔍 Testing with EXISTING email...")
    real_email = 'nrupal7465@gmail.com'
    
    response = client.post('/auth/password-reset/', {
        'email': real_email
    })
    
    print(f"Response status: {response.status_code}")
    print(f"Redirect location: {response.get('Location', 'No redirect')}")
    
    if response.status_code == 302:
        print("✅ Form submitted and redirected")
        
        # Follow redirect to see success page
        follow_response = client.get(response['Location'])
        print(f"Success page status: {follow_response.status_code}")
        
        # Check if success message is shown
        content = follow_response.content.decode()
        if 'Password reset instructions have been sent' in content:
            print("✅ Success message shown")
        elif 'If your email address is registered' in content:
            print("✅ Generic success message shown (good for security)")
        else:
            print("⚠️  Unexpected success message")
            print(f"Content preview: {content[:200]}...")

def test_view_routing():
    """
    Test if our custom view is actually being used
    """
    print("\n" + "=" * 60)
    print("TESTING VIEW ROUTING")
    print("=" * 60)
    
    from django.urls import reverse
    from core import views
    
    # Get the view class from URL
    try:
        from django.urls import resolve
        resolved = resolve('/auth/password-reset/')
        print(f"URL resolves to: {resolved.func}")
        print(f"View class: {resolved.func.__class__}")
        print(f"View name: {resolved.func.view_class}")
        
        # Check if it's our custom view
        if resolved.func.view_class == views.CustomPasswordResetView:
            print("✅ CustomPasswordResetView is being used")
        else:
            print(f"❌ Wrong view being used: {resolved.func.view_class}")
            
    except Exception as e:
        print(f"❌ Error resolving URL: {e}")

def main():
    """
    Main function to run all tests
    """
    print("🔐 Password Reset Validation Test")
    print("=" * 60)
    print("This test will show debug output from the custom view")
    print("Look for 🔍 DEBUG messages in Django console output")
    print("=" * 60)
    
    # Test view routing
    test_view_routing()
    
    # Test password reset validation
    test_password_reset_validation()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("Check the Django console output above for 🔍 DEBUG messages")
    print("If you don't see debug messages, the custom view is not being used")

if __name__ == '__main__':
    main()
