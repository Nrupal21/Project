"""
Simple test to verify email functionality with complete error tracing.
"""
import os
import traceback
import sys

print("Starting email test script...")
try:
    # Set up Django environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guides.settings')
    
    print("Loading Django settings...")
    import django
    django.setup()
    
    from django.core.mail import send_mail
    from django.conf import settings
    
    # Print configuration details
    print(f"Email backend: {settings.EMAIL_BACKEND}")
    print(f"Email file path: {settings.EMAIL_FILE_PATH}")
    print(f"Default from email: {settings.DEFAULT_FROM_EMAIL}")
    
    # Ensure email directory exists
    if not os.path.exists(settings.EMAIL_FILE_PATH):
        os.makedirs(settings.EMAIL_FILE_PATH)
        print(f"Created email directory: {settings.EMAIL_FILE_PATH}")
    else:
        print(f"Email directory exists: {settings.EMAIL_FILE_PATH}")
    
    # Send test email
    print("\nSending test email...")
    result = send_mail(
        subject='Test Email',
        message='This is a simple test email.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['nrupal85@gmail.com'],
        fail_silently=False,
    )
    
    print(f"Email sent result: {result}")
    
    # Check for email files
    if settings.EMAIL_BACKEND == 'django.core.mail.backends.filebased.EmailBackend':
        email_files = os.listdir(settings.EMAIL_FILE_PATH)
        print(f"\nEmail files ({len(email_files)}):")
        for f in email_files[:5]:  # Show first 5 files
            print(f"- {f}")
        
        # Show content of latest email file
        if email_files:
            latest_file = max(
                email_files,
                key=lambda f: os.path.getmtime(os.path.join(settings.EMAIL_FILE_PATH, f))
            )
            print(f"\nLatest email file: {latest_file}")
            with open(os.path.join(settings.EMAIL_FILE_PATH, latest_file), 'r') as f:
                print("Content:")
                print("-" * 40)
                print(f.read())
                print("-" * 40)
    
    print("\nTest completed successfully!")

except Exception as e:
    print(f"ERROR: {e}")
    print("\nTraceback:")
    traceback.print_exc()
    sys.exit(1)
