import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

# Disable OTP device creation signal
from django.db.models.signals import post_save
from accounts.signals import create_user_profile
post_save.disconnect(create_user_profile, sender=get_user_model())

try:
    # Create normal user
    User = get_user_model()
    user = User.objects.create_user(
        username='normaluser',
        email='user@example.com',
        password='user123',
        is_staff=False,
        is_superuser=False
    )
    print(f"Successfully created user: {user.email}")
    
    # Reconnect the signal for future user creations
    post_save.connect(create_user_profile, sender=get_user_model())
    
except Exception as e:
    print(f"Error creating user: {str(e)}")
