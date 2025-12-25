#!/usr/bin/env python
"""
Django Email Sending Test Script
Tests both console and SMTP email backends to ensure proper functionality
"""

import os
import sys
import django
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

def test_console_email_backend():
    """
    Test email sending using console backend (development)
    This should print the email content to console
    """
    print("=" * 60)
    print("TESTING CONSOLE EMAIL BACKEND")
    print("=" * 60)
    
    try:
        # Test simple email
        subject = 'Test Email - Console Backend'
        message = 'This is a test email sent using Django console backend.'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = ['adarshkhot982@gmail.com']
        
        print(f"Sending simple email...")
        print(f"From: {from_email}")
        print(f"To: {recipient_list}")
        print(f"Subject: {subject}")
        print(f"Message: {message}")
        
        result = send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        
        print(f"✅ Console email sent successfully! Return value: {result}")
        print("(Check console output above for email content)")
        
    except Exception as e:
        print(f"❌ Console email test failed: {e}")
        return False
    
    return True

def test_html_email():
    """
    Test HTML email sending using console backend
    """
    print("\n" + "=" * 60)
    print("TESTING HTML EMAIL")
    print("=" * 60)
    
    try:
        subject = 'HTML Test Email - Food Ordering System'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = 'adarshkhot982@gmail.com'
        
        # Create HTML content
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Test Email</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #4f46e5; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; }
                .footer { background-color: #f3f4f6; padding: 10px; text-align: center; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🍔 Tetech Food Ordering System</h1>
                <p>Test HTML Email</p>
            </div>
            <div class="content">
                <h2>Hello Customer!</h2>
                <p>This is a test HTML email from your food ordering system.</p>
                <p><strong>Features tested:</strong></p>
                <ul>
                    <li>✅ HTML formatting</li>
                    <li>✅ CSS styling</li>
                    <li>✅ Images and emojis</li>
                    <li>✅ Responsive design</li>
                </ul>
                <p>Order your favorite food now! 🍕🍟🥤</p>
            </div>
            <div class="footer">
                <p>&copy; 2024 Tetech Food Ordering. All rights reserved.</p>
                <p>This is an automated test email.</p>
            </div>
        </body>
        </html>
        """
        
        # Create text alternative
        text_content = """
        Tetech Food Ordering System - Test Email
        
        Hello Customer!
        
        This is a test HTML email from your food ordering system.
        
        Features tested:
        - HTML formatting
        - CSS styling  
        - Images and emojis
        - Responsive design
        
        Order your favorite food now!
        
        © 2024 Tetech Food Ordering. All rights reserved.
        This is an automated test email.
        """
        
        # Create email with both HTML and text
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[to_email],
        )
        
        email.attach_alternative(html_content, "text/html")
        
        print(f"Sending HTML email to: {to_email}")
        result = email.send()
        
        print(f"✅ HTML email sent successfully! Return value: {result}")
        print("(Check console output above for email content)")
        
    except Exception as e:
        print(f"❌ HTML email test failed: {e}")
        return False
    
    return True

def test_template_email():
    """
    Test email using Django templates
    """
    print("\n" + "=" * 60)
    print("TESTING TEMPLATE-BASED EMAIL")
    print("=" * 60)
    
    try:
        subject = 'Template Test Email - Order Confirmation'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = 'customer@example.com'
        
        # Context for template
        context = {
            'customer_name': 'John Doe',
            'order_number': 'ORD-2024-001',
            'order_total': '₹599.00',
            'restaurant_name': 'Spice Garden',
            'delivery_address': '123 Main St, Mumbai, Maharashtra 400001',
            'items': [
                {'name': 'Butter Chicken', 'quantity': 2, 'price': '₹249.00'},
                {'name': 'Naan Bread', 'quantity': 4, 'price': '₹80.00'},
                {'name': 'Mango Lassi', 'quantity': 2, 'price': '₹120.00'},
            ]
        }
        
        # Try to render template (fallback to simple HTML if template doesn't exist)
        try:
            html_content = render_to_string('emails/order_status_update.html', context)
        except:
            # Create fallback HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Order Confirmation</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ background-color: #10b981; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .order-item {{ border-bottom: 1px solid #e5e7eb; padding: 10px 0; }}
                    .total {{ font-size: 18px; font-weight: bold; color: #059669; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>📦 Order Confirmed!</h1>
                    <p>Thank you for your order, {context['customer_name']}</p>
                </div>
                <div class="content">
                    <h2>Order Details</h2>
                    <p><strong>Order Number:</strong> {context['order_number']}</p>
                    <p><strong>Restaurant:</strong> {context['restaurant_name']}</p>
                    <p><strong>Delivery Address:</strong> {context['delivery_address']}</p>
                    
                    <h3>Order Items:</h3>
                    {''.join([f'<div class="order-item">{item["name"]} x{item["quantity"]} - {item["price"]}</div>' for item in context['items']])}
                    
                    <p class="total">Total: {context['order_total']}</p>
                    
                    <p>Your order is being prepared and will be delivered soon!</p>
                </div>
            </body>
            </html>
            """
        
        # Create email
        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=from_email,
            to=[to_email],
        )
        email.content_subtype = "html"
        
        print(f"Sending template email to: {to_email}")
        result = email.send()
        
        print(f"✅ Template email sent successfully! Return value: {result}")
        print("(Check console output above for email content)")
        
    except Exception as e:
        print(f"❌ Template email test failed: {e}")
        return False
    
    return True

def test_smtp_configuration():
    """
    Test SMTP configuration (without actually sending)
    This validates the SMTP settings are properly configured
    """
    print("\n" + "=" * 60)
    print("TESTING SMTP CONFIGURATION")
    print("=" * 60)
    
    # Check current email backend
    print(f"Current EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"Default from email: {settings.DEFAULT_FROM_EMAIL}")
    
    # Check if SMTP settings are configured (even if commented)
    smtp_settings = {
        'EMAIL_HOST': getattr(settings, 'EMAIL_HOST', 'Not set'),
        'EMAIL_PORT': getattr(settings, 'EMAIL_PORT', 'Not set'),
        'EMAIL_USE_TLS': getattr(settings, 'EMAIL_USE_TLS', 'Not set'),
        'EMAIL_HOST_USER': getattr(settings, 'EMAIL_HOST_USER', 'Not set'),
        'EMAIL_HOST_PASSWORD': '***' if getattr(settings, 'EMAIL_HOST_PASSWORD', None) else 'Not set',
    }
    
    print("\nSMTP Settings:")
    for key, value in smtp_settings.items():
        print(f"  {key}: {value}")
    
    # Check if all required SMTP settings are configured
    required_settings = ['EMAIL_HOST', 'EMAIL_PORT', 'EMAIL_USE_TLS', 'EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD']
    missing_settings = [setting for setting in required_settings if getattr(settings, setting, None) is None]
    
    if missing_settings:
        print(f"\n⚠️  SMTP settings not configured: {', '.join(missing_settings)}")
        print("To enable SMTP email sending, uncomment and configure the SMTP settings in settings.py")
        return False
    else:
        print("\n✅ All SMTP settings are configured!")
        return True

def test_smtp_email_sending():
    """
    Test actual SMTP email sending (only if SMTP is configured)
    """
    print("\n" + "=" * 60)
    print("TESTING SMTP EMAIL SENDING")
    print("=" * 60)
    
    # Check if SMTP is configured
    if not getattr(settings, 'EMAIL_HOST', None):
        print("❌ SMTP not configured. Skipping SMTP email test.")
        return False
    
    try:
        # Temporarily switch to SMTP backend
        original_backend = settings.EMAIL_BACKEND
        settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
        
        subject = 'SMTP Test Email - Food Ordering System'
        message = 'This is a test email sent using SMTP backend.'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = ['test@example.com']  # Replace with actual email for testing
        
        print(f"Sending SMTP email...")
        print(f"From: {from_email}")
        print(f"To: {recipient_list}")
        print(f"SMTP Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        print(f"TLS: {settings.EMAIL_USE_TLS}")
        
        result = send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        
        print(f"✅ SMTP email sent successfully! Return value: {result}")
        
        # Restore original backend
        settings.EMAIL_BACKEND = original_backend
        
    except Exception as e:
        print(f"❌ SMTP email test failed: {e}")
        # Restore original backend
        settings.EMAIL_BACKEND = original_backend
        return False
    
    return True

def main():
    """
    Main function to run all email tests
    """
    print("🍔 Django Email Testing - Tetech Food Ordering System")
    print("=" * 60)
    
    test_results = []
    
    # Run all tests
    test_results.append(("Console Backend", test_console_email_backend()))
    test_results.append(("HTML Email", test_html_email()))
    test_results.append(("Template Email", test_template_email()))
    test_results.append(("SMTP Configuration", test_smtp_configuration()))
    
    # Only test SMTP sending if configured
    if getattr(settings, 'EMAIL_HOST', None):
        test_results.append(("SMTP Sending", test_smtp_email_sending()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All email tests passed successfully!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print("\nNext Steps:")
    print("1. For production: Configure SMTP settings in settings.py")
    print("2. Replace test@example.com with actual recipient emails")
    print("3. Test with real email addresses to verify delivery")
    print("4. Check spam folders if emails don't arrive")

if __name__ == '__main__':
    main()
