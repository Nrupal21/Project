#!/usr/bin/env python
"""
Test Password Reset Link Redirect
Check where the reset link is redirecting
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

def test_reset_link_redirect():
    """
    Test the password reset link and see where it redirects
    """
    print("=" * 60)
    print("TESTING PASSWORD RESET LINK REDIRECT")
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
        response = client.get(reset_url, follow=False)  # Don't follow redirects
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 302:
            redirect_url = response.get('Location', 'No redirect URL')
            print(f"🔄 Redirecting to: {redirect_url}")
            
            # Follow the redirect
            follow_response = client.get(reset_url, follow=True)
            print(f"After redirect - Status: {follow_response.status_code}")
            print(f"After redirect - Final URL: {follow_response.request.get('PATH_INFO', 'Unknown')}")
            
            if follow_response.status_code == 200:
                print("✅ Final page loads successfully")
                
                # Check if it's the password reset form
                content = follow_response.content.decode()
                if 'Set New Password' in content:
                    print("✅ Password reset form found")
                    return True
                elif 'Invalid Reset Link' in content:
                    print("❌ Link shows as invalid")
                    return False
                else:
                    print("⚠️  Unexpected page content")
                    print(f"Page content preview: {content[:200]}...")
                    return False
            else:
                print(f"❌ Final page failed with status: {follow_response.status_code}")
                return False
                
        elif response.status_code == 200:
            print("✅ Reset link loads directly (no redirect)")
            content = response.content.decode()
            if 'Set New Password' in content:
                print("✅ Password reset form found")
                return True
            else:
                print("❌ Password reset form not found")
                return False
                
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(f"Response content: {response.content.decode()[:500]}...")
            return False
            
    except Exception as e:
        print(f"❌ Error testing reset link: {e}")
        return False

def test_manual_reset_url():
    """
    Test with the actual URL from the email
    """
    print("\n" + "=" * 60)
    print("TESTING ACTUAL EMAIL RESET URL")
    print("=" * 60)
    
    client = Client()
    
    # Use the actual URL from the email
    actual_url = "/auth/reset/MTA/czvkv7-791cf42f199375b274e5951f0f156809/"
    print(f"🔗 Testing actual email URL: {actual_url}")
    
    try:
        response = client.get(actual_url, follow=True)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode()
            if 'Set New Password' in content:
                print("✅ Password reset form found!")
                return True
            elif 'Invalid Reset Link' in content:
                print("❌ Link shows as invalid - token may have expired")
                return False
            else:
                print("⚠️  Unexpected content")
                print(f"Content preview: {content[:300]}...")
                return False
        else:
            print(f"❌ Failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """
    Main function to run redirect tests
    """
    print("🔐 Password Reset Redirect Testing")
    print("=" * 60)
    
    # Test fresh reset link
    fresh_link_works = test_reset_link_redirect()
    
    # Test actual email URL
    actual_url_works = test_manual_reset_url()
    
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    
    if fresh_link_works:
        print("✅ Fresh password reset links work correctly")
    else:
        print("❌ Fresh password reset links have issues")
        
    if actual_url_works:
        print("✅ Email reset link works correctly")
    else:
        print("❌ Email reset link has issues (possibly expired)")
    
    print("\n📋 Manual Test Instructions:")
    print("1. Start Django server: python manage.py runserver")
    print("2. Visit: http://localhost:8000/auth/password-reset/")
    print("3. Enter your email to get a fresh reset link")
    print("4. Click the link in the email to test password reset")

if __name__ == '__main__':
    main()
