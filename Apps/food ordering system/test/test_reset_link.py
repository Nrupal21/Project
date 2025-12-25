#!/usr/bin/env python
"""
Test Password Reset Link Validation
Tests if the reset link token is valid and what happens when accessed
"""

import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

def test_reset_link_validation():
    """
    Test the password reset link validation
    """
    print("=" * 60)
    print("TESTING PASSWORD RESET LINK VALIDATION")
    print("=" * 60)
    
    User = get_user_model()
    client = Client()
    
    # Get the test user
    test_email = 'nrupal7465@gmail.com'
    user = User.objects.filter(email=test_email).first()
    
    if not user:
        print(f"❌ User not found: {test_email}")
        return False
    
    print(f"✅ Found user: {user.username} ({user.email})")
    
    # Generate fresh token and UID
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    print(f"Generated UID: {uid}")
    print(f"Generated Token: {token}")
    
    # Test the reset link
    reset_url = f"/auth/reset/{uid}/{token}/"
    print(f"\n🔗 Testing reset link: {reset_url}")
    
    try:
        # GET request to the reset link
        response = client.get(reset_url)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Reset link is valid - page loads successfully")
            
            # Check if the form is present
            content = response.content.decode()
            if 'Set New Password' in content:
                print("✅ Password reset form found in page")
            else:
                print("⚠️  Password reset form not found in page")
            
            if 'new_password1' in content and 'new_password2' in content:
                print("✅ Password input fields found")
            else:
                print("❌ Password input fields missing")
                
            return True
            
        elif response.status_code == 404:
            print("❌ Reset link returns 404 - URL routing issue")
            return False
            
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
            print(f"Response content: {response.content.decode()[:500]}...")
            return False
            
    except Exception as e:
        print(f"❌ Error testing reset link: {e}")
        return False

def test_token_validation():
    """
    Test if the token is actually valid
    """
    print("\n" + "=" * 60)
    print("TESTING TOKEN VALIDATION")
    print("=" * 60)
    
    User = get_user_model()
    test_email = 'nrupal7465@gmail.com'
    user = User.objects.filter(email=test_email).first()
    
    if not user:
        return False
    
    # Test token generation and validation
    token = default_token_generator.make_token(user)
    is_valid = default_token_generator.check_token(user, token)
    
    print(f"Generated token: {token}")
    print(f"Token is valid: {is_valid}")
    
    if is_valid:
        print("✅ Token validation works correctly")
        return True
    else:
        print("❌ Token validation failed")
        return False

def main():
    """
    Main function to run all reset link tests
    """
    print("🔐 Password Reset Link Testing")
    print("=" * 60)
    
    # Test token validation
    token_valid = test_token_validation()
    
    # Test reset link access
    link_works = test_reset_link_validation()
    
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    
    if token_valid and link_works:
        print("🎉 Password reset links are working correctly!")
        print("\n📋 Manual Test Steps:")
        print("1. Start Django server: python manage.py runserver")
        print("2. Visit: http://localhost:8000/auth/reset/MTA/czvkv7-791cf42f199375b274e5951f0f156809/")
        print("3. You should see the password reset form")
        print("4. Fill in new password and confirm")
        print("5. Submit the form")
    else:
        print("❌ Password reset links have issues")
        print("Check the error messages above for details")

if __name__ == '__main__':
    main()
