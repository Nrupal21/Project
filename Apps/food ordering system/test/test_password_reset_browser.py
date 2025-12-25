#!/usr/bin/env python
"""
Generate a fresh password reset link for manual browser testing
This bypasses the redirect loop issue by creating a new token
"""

import os
import sys
import django
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

def generate_fresh_reset_link():
    """
    Generate a fresh password reset link for manual testing
    """
    print("=" * 60)
    print("GENERATING FRESH PASSWORD RESET LINK")
    print("=" * 60)
    
    User = get_user_model()
    
    # Get the test user
    test_email = 'nrupal7465@gmail.com'
    user = User.objects.filter(email=test_email).first()
    
    if not user:
        print(f"❌ User not found: {test_email}")
        return None
    
    print(f"✅ Found user: {user.username} ({user.email})")
    
    # Generate fresh token and UID
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    print(f"Generated UID: {uid}")
    print(f"Generated Token: {token}")
    
    # Create the reset URL
    reset_url = f"http://localhost:8000/auth/reset/{uid}/{token}/"
    
    print(f"\n🔗 FRESH RESET LINK: {reset_url}")
    
    # Also create a simple email content for reference
    email_content = f"""
Subject: Password Reset Request - Food Ordering System

Hello {user.username},

You requested a password reset for your account.

Click the link below to reset your password:
{reset_url}

This link will expire in 24 hours.

If you didn't request this, please ignore this email.

Thanks,
Food Ordering System
"""
    
    print(f"\n📧 Email content preview:")
    print(email_content)
    
    return reset_url

def main():
    """
    Main function
    """
    print("🔐 Password Reset Link Generator")
    print("=" * 60)
    
    reset_url = generate_fresh_reset_link()
    
    if reset_url:
        print("\n" + "=" * 60)
        print("MANUAL TESTING INSTRUCTIONS")
        print("=" * 60)
        print("1. Start Django server: python manage.py runserver")
        print("2. Copy and paste the reset link above into your browser")
        print("3. You should see the password reset form")
        print("4. Fill in new password and confirm")
        print("5. Submit the form")
        print("6. Check if password is actually updated")
        
        print(f"\n📋 Quick Test:")
        print(f"1. Visit: {reset_url}")
        print(f"2. Look for 'Set New Password' form")
        print(f"3. Enter test password like 'NewPass123!'")
        print(f"4. Submit and check if it redirects to success page")
        
        print(f"\n🔍 If you see redirect loop:")
        print(f"- Try in incognito/private browser window")
        print(f"- Clear browser cookies and cache")
        print(f"- Check if the form loads at all")

if __name__ == '__main__':
    main()
