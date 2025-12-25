#!/usr/bin/env python
"""
Debug authentication issues by testing login directly.
Run with: python debug_auth.py
"""

import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

from django.contrib.auth import authenticate, get_user_model
from core.forms import UnifiedLoginForm

User = get_user_model()

print("=" * 60)
print("AUTHENTICATION DEBUG TEST")
print("=" * 60)

# Test 1: Check if users exist
print("\n1. CHECKING USER DATABASE:")
users = User.objects.all()
for user in users[:5]:  # Show first 5 users
    print(f"   Username: {user.username}, Active: {user.is_active}, Staff: {user.is_staff}")

# Test 2: Direct Django authentication
print("\n2. TESTING DIRECT AUTHENTICATION:")
test_username = input("Enter username to test: ").strip()
test_password = input("Enter password to test: ").strip()

print(f"\n   Testing authentication for: {test_username}")
user = authenticate(username=test_username, password=test_password)

if user:
    print(f"   ✅ SUCCESS: User authenticated - {user.username}")
    print(f"   User ID: {user.id}, Active: {user.is_active}")
else:
    print(f"   ❌ FAILED: Authentication failed")
    
    # Check if user exists
    try:
        existing_user = User.objects.get(username=test_username)
        print(f"   User exists in database: {existing_user.username}")
        print(f"   User is active: {existing_user.is_active}")
        
        # Test password check
        if existing_user.check_password(test_password):
            print(f"   ✅ Password check passed")
        else:
            print(f"   ❌ Password check failed")
            
    except User.DoesNotExist:
        print(f"   ❌ User does not exist in database")

# Test 3: Form-based authentication
print("\n3. TESTING FORM-BASED AUTHENTICATION:")
from django.test import RequestFactory
factory = RequestFactory()
request = factory.post('/login/', {
    'username': test_username,
    'password': test_password,
    'remember_me': False
})

form = UnifiedLoginForm(request, data=request.POST)
print(f"   Form is valid: {form.is_valid()}")

if form.is_valid():
    user = form.get_user()
    print(f"   ✅ Form authentication successful: {user.username}")
else:
    print(f"   ❌ Form validation failed:")
    for field, errors in form.errors.items():
        print(f"      {field}: {errors}")
    for error in form.non_field_errors():
        print(f"      Non-field: {error}")

print("\n" + "=" * 60)
print("DEBUG TEST COMPLETE")
print("=" * 60)
