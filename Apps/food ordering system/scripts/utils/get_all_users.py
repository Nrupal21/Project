#!/usr/bin/env python
"""
Get all users from database with their credentials for testing login functionality.
Run with: python manage.py shell < get_all_users.py
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

from django.contrib.auth import get_user_model
from customer.models import UserProfile

User = get_user_model()

print("=" * 80)
print("ALL USERS IN DATABASE - Login Credentials")
print("=" * 80)

users = User.objects.all()
if not users.exists():
    print("No users found in database!")
    print("Create test users with:")
    print("User.objects.create_user('username', 'email@example.com', 'password')")
else:
    print(f"Total users found: {users.count()}")
    print("-" * 80)
    
    for i, user in enumerate(users, 1):
        print(f"USER #{i}")
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Active: {user.is_active}")
        print(f"Staff: {user.is_staff}")
        print(f"Superuser: {user.is_superuser}")
        print(f"Date Joined: {user.date_joined}")
        
        # Check if user has profile
        try:
            profile = UserProfile.objects.get(user=user)
            print(f"Profile Name: {profile.full_name}")
            print(f"Phone: {profile.phone_number}")
        except UserProfile.DoesNotExist:
            print("Profile: Not found")
        
        print("Password: [Cannot display - passwords are hashed]")
        print("To test login, use the original password or reset with:")
        print(f"  user = User.objects.get(username='{user.username}')")
        print("  user.set_password('new_password')")
        print("  user.save()")
        print("-" * 80)

print("\nTEST LOGIN URLS:")
print("- Customer Login: http://tetech.in:8000/login/")
print("- Admin Login: http://tetech.in:8000/admin/")

print("\nTO CREATE TEST USER:")
print("User.objects.create_user('testuser', 'test@example.com', 'testpass123')")

print("\nTO RESET USER PASSWORD:")
print("user = User.objects.get(username='username')")
print("user.set_password('new_password')")
print("user.save()")
