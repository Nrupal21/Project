#!/usr/bin/env python
"""
Test SMTP Connection and Email Loading
Debug script to check if SMTP credentials are loading correctly
"""

import os
import sys
import django
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText

# Load environment variables
load_dotenv()

print("=" * 60)
print("TESTING ENVIRONMENT VARIABLES AND SMTP CONNECTION")
print("=" * 60)

# Check if .env file exists and is being read
print("📁 Checking .env file loading:")
env_vars = {
    'EMAIL_HOST': os.getenv('EMAIL_HOST'),
    'EMAIL_PORT': os.getenv('EMAIL_PORT'),
    'EMAIL_USE_TLS': os.getenv('EMAIL_USE_TLS'),
    'EMAIL_HOST_USER': os.getenv('EMAIL_HOST_USER'),
    'EMAIL_HOST_PASSWORD': os.getenv('EMAIL_HOST_PASSWORD'),
    'DEFAULT_FROM_EMAIL': os.getenv('DEFAULT_FROM_EMAIL'),
}

for key, value in env_vars.items():
    if value:
        if 'PASSWORD' in key:
            print(f"  {key}: {'*' * len(value)}")
        else:
            print(f"  {key}: {value}")
    else:
        print(f"  {key}: ❌ NOT SET")

# Test SMTP connection
print(f"\n🔌 Testing SMTP connection to {env_vars['EMAIL_HOST']}:{env_vars['EMAIL_PORT']}")

try:
    # Create SMTP connection
    server = smtplib.SMTP(env_vars['EMAIL_HOST'], int(env_vars['EMAIL_PORT']))
    server.set_debuglevel(1)  # Enable debug output
    
    # Start TLS encryption
    if env_vars['EMAIL_USE_TLS'].lower() == 'true':
        print("🔐 Starting TLS encryption...")
        server.starttls()
    
    # Login to SMTP server
    print(f"🔑 Logging in as {env_vars['EMAIL_HOST_USER']}...")
    server.login(env_vars['EMAIL_HOST_USER'], env_vars['EMAIL_HOST_PASSWORD'])
    
    print("✅ SMTP connection successful!")
    
    # Test sending a simple email
    print("\n📧 Testing email sending...")
    test_email = 'nrupal85@gmail.com'  # Replace with your test email
    
    msg = MIMEText('This is a test email from the food ordering system.')
    msg['Subject'] = 'SMTP Test - Food Ordering System'
    msg['From'] = env_vars['DEFAULT_FROM_EMAIL']
    msg['To'] = test_email
    
    server.send_message(msg)
    print(f"✅ Test email sent to {test_email}!")
    
    server.quit()
    
except smtplib.SMTPAuthenticationError as e:
    print(f"❌ SMTP Authentication Failed: {e}")
    print("\n🔧 Gmail Authentication Issues:")
    print("1. Enable 2-factor authentication on your Gmail account")
    print("2. Generate an App Password instead of using your regular password")
    print("3. Go to: https://myaccount.google.com/apppasswords")
    print("4. Create a new app password and use it in EMAIL_HOST_PASSWORD")
    
except smtplib.SMTPConnectError as e:
    print(f"❌ SMTP Connection Failed: {e}")
    print("Check your internet connection and firewall settings")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("Check all SMTP settings and try again")

print(f"\n📋 Next Steps:")
print("1. If authentication failed, generate a Gmail App Password")
print("2. Update EMAIL_HOST_PASSWORD in .env file with the app password")
print("3. Restart the Django server")
print("4. Test password reset again")
