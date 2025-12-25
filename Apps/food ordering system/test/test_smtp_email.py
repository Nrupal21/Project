#!/usr/bin/env python
"""
Simple SMTP Email Test Script
Tests actual SMTP email sending using configured Gmail settings
"""

import os
import sys
import django
from django.core.mail import send_mail
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

def test_real_smtp_email():
    """
    Test sending a real email using SMTP backend
    """
    print("🍔 Testing Real SMTP Email Sending")
    print("=" * 50)
    
    # Temporarily switch to SMTP backend
    original_backend = settings.EMAIL_BACKEND
    settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    
    try:
        # Display current SMTP settings
        print(f"SMTP Configuration:")
        print(f"  Host: {settings.EMAIL_HOST}")
        print(f"  Port: {settings.EMAIL_PORT}")
        print(f"  TLS: {settings.EMAIL_USE_TLS}")
        print(f"  User: {settings.EMAIL_HOST_USER}")
        print(f"  From: {settings.DEFAULT_FROM_EMAIL}")
        print()
        
        # Test email details
        subject = '✅ Test Email - Food Ordering System'
        message = """
Hello!

This is a test email from the Tetech Food Ordering System.

If you receive this email, it means:
✅ SMTP configuration is working
✅ Gmail authentication is successful  
✅ Email sending functionality is operational

System Status: READY FOR PRODUCTION 🎉

Best regards,
Tetech Food Ordering Team
        """
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = ['nrupal85@gmail.com']  # Test recipient
        
        print(f"Sending email to: {recipient_list[0]}")
        print(f"Subject: {subject}")
        print("Please wait...")
        
        # Send the email
        result = send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        
        print(f"✅ SUCCESS! Email sent successfully!")
        print(f"   Return value: {result}")
        print(f"   Check your inbox at {recipient_list[0]}")
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        print("\nTroubleshooting:")
        print("1. Check if Gmail app password is correct")
        print("2. Ensure 'Less secure app access' is ON for Gmail")
        print("3. Verify internet connection")
        print("4. Check if Gmail account is blocked")
        return False
        
    finally:
        # Restore original backend
        settings.EMAIL_BACKEND = original_backend
    
    return True

def test_environment_variables():
    """
    Verify all required environment variables are loaded
    """
    print("🔍 Checking Environment Variables")
    print("=" * 50)
    
    required_vars = {
        'EMAIL_HOST': os.getenv('EMAIL_HOST'),
        'EMAIL_PORT': os.getenv('EMAIL_PORT'),
        'EMAIL_USE_TLS': os.getenv('EMAIL_USE_TLS'),
        'EMAIL_HOST_USER': os.getenv('EMAIL_HOST_USER'),
        'EMAIL_HOST_PASSWORD': '***' if os.getenv('EMAIL_HOST_PASSWORD') else None,
        'DEFAULT_FROM_EMAIL': os.getenv('DEFAULT_FROM_EMAIL'),
    }
    
    all_set = True
    for var, value in required_vars.items():
        status = "✅" if value else "❌"
        print(f"{status} {var}: {value}")
        if not value:
            all_set = False
    
    if all_set:
        print("\n✅ All environment variables are properly set!")
    else:
        print("\n❌ Some environment variables are missing!")
        print("Please check your .env file.")
    
    return all_set

if __name__ == '__main__':
    print("🚀 SMTP Email Test - Tetech Food Ordering System")
    print("=" * 60)
    
    # Check environment variables first
    env_ok = test_environment_variables()
    
    if not env_ok:
        print("\n❌ Cannot proceed with SMTP test - missing configuration")
        sys.exit(1)
    
    print()
    
    # Test SMTP email sending
    smtp_ok = test_real_smtp_email()
    
    print("\n" + "=" * 60)
    if smtp_ok:
        print("🎉 SMTP EMAIL TEST PASSED!")
        print("Your email system is ready for production.")
    else:
        print("⚠️  SMTP EMAIL TEST FAILED!")
        print("Please check the error messages above.")
