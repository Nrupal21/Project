"""
Quick authentication test to verify the login system is working.
Run this with: python manage.py shell < quick_auth_test.py
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

from django.contrib.auth import authenticate, get_user_model
from customer.models import UserProfile

User = get_user_model()

print("=== Quick Authentication Test ===")

# Check if users exist
users = User.objects.all()
print(f"Found {users.count()} users in database")

if users.exists():
    # Test first user
    test_user = users.first()
    print(f"\nTesting with user: {test_user.username}")
    print(f"Email: {test_user.email}")
    print(f"Active: {test_user.is_active}")
    
    # Check if profile exists
    try:
        profile = UserProfile.objects.get(user=test_user)
        print(f"Profile exists: {profile.full_name}")
    except UserProfile.DoesNotExist:
        print("⚠ Profile does not exist for this user")
    
    # Test authentication with wrong password (should return None)
    result = authenticate(username=test_user.username, password='wrong_password')
    if result is None:
        print("✓ Authentication working: Wrong password correctly rejected")
    else:
        print("✗ Authentication issue: Wrong password was accepted")
    
    print("\nTo test with correct credentials, use:")
    print(f"username: {test_user.username}")
    print("password: [enter correct password]")
    
else:
    print("⚠ No users found in database")
    print("Create a test user with:")
    print("User.objects.create_user('testuser', 'test@example.com', 'testpass123')")

print("\n=== Test Complete ===")
