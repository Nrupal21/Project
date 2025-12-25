#!/usr/bin/env python
"""
Manual Password Reset Test Script
Tests the password reset email content directly without CSRF issues
"""

import os
import sys
import django
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth import get_user_model
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

def test_password_reset_email_content():
    """
    Test sending the actual password reset email content
    """
    print("=" * 60)
    print("TESTING PASSWORD RESET EMAIL CONTENT")
    print("=" * 60)
    
    User = get_user_model()
    
    # Get or create test user
    test_email = 'nrupal7465@gmail.com'  # Use your email
    user = User.objects.filter(email=test_email).first()
    
    if not user:
        print(f"Creating test user: {test_email}")
        user = User.objects.create_user(
            username='adarshkhot',
            email=test_email,
            password='testpass123'
        )
        print("✅ Test user created")
    else:
        print(f"✅ Found existing user: {test_email}")
    
    # Generate token and UID for password reset
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    print(f"Generated token: {token}")
    print(f"Generated UID: {uid}")
    
    # Prepare email context
    context = {
        'user': user,
        'protocol': 'http',
        'domain': 'localhost:8000',
        'uid': uid,
        'token': token,
    }
    
    # Render email subject
    try:
        subject = render_to_string('core/password_reset_subject.txt', context).strip()
        print(f"✅ Email subject: {subject}")
    except Exception as e:
        print(f"❌ Failed to render subject: {e}")
        subject = "Password Reset Request - Food Ordering System"
    
    # Render email body
    try:
        html_message = render_to_string('core/password_reset_email.html', context)
        print("✅ Email HTML rendered successfully")
    except Exception as e:
        print(f"❌ Failed to render HTML email: {e}")
        return False
    
    # Send the email
    try:
        print(f"\n📧 Sending password reset email to: {test_email}")
        
        send_mail(
            subject=subject,
            message='',  # Plain text version (empty since we're using HTML)
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        print("✅ Password reset email sent successfully!")
        print(f"📬 Check your inbox: {test_email}")
        print(f"🔗 Reset link will be: http://localhost:8000/auth/reset/{uid}/{token}/")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

def main():
    """
    Main function to run the manual password reset test
    """
    print("🔐 Manual Password Reset Email Test")
    print("=" * 60)
    
    # Check email backend
    print(f"Current EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    
    if settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
        print("✅ SMTP backend is enabled - emails will be sent to your inbox")
    else:
        print("⚠️  Console backend is enabled - emails will be printed to console")
    
    # Test the password reset email
    success = test_password_reset_email_content()
    
    print("\n" + "=" * 60)
    print("TEST RESULT")
    print("=" * 60)
    
    if success:
        print("🎉 Password reset email test completed successfully!")
        print("\n📋 Next Steps:")
        print("1. Check your email inbox for the password reset message")
        print("2. Click the reset link in the email")
        print("3. Set a new password")
        print("4. Try logging in with the new password")
    else:
        print("❌ Password reset email test failed")
        print("Check the error messages above")

if __name__ == '__main__':
    main()
