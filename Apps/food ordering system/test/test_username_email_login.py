#!/usr/bin/env python
"""
Test script to verify username or email login functionality.

This script tests the custom authentication backend to ensure users can
login with either their username or email address.
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.authentication import UsernameOrEmailBackend

def test_authentication_backend():
    """
    Test the custom authentication backend with username and email login.
    
    This function creates a test user and verifies they can authenticate
    using both their username and email address.
    """
    User = get_user_model()
    backend = UsernameOrEmailBackend()
    
    print("🔐 Testing Username or Email Authentication Backend")
    print("=" * 60)
    
    # Create a test user (if not exists)
    test_username = "testuser123"
    test_email = "testuser@example.com"
    test_password = "TestPass123!"
    
    try:
        # Clean up any existing test user
        User.objects.filter(username=test_username).delete()
        User.objects.filter(email=test_email).delete()
        
        # Create new test user
        user = User.objects.create_user(
            username=test_username,
            email=test_email,
            password=test_password
        )
        print(f"✅ Created test user: {test_username} ({test_email})")
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return False
    
    # Test 1: Login with username
    print("\n📝 Test 1: Authentication with username")
    user_by_username = backend.authenticate(
        request=None,
        username=test_username,
        password=test_password
    )
    
    if user_by_username and user_by_username.username == test_username:
        print(f"✅ SUCCESS: User authenticated with username '{test_username}'")
    else:
        print(f"❌ FAILED: Could not authenticate with username '{test_username}'")
        return False
    
    # Test 2: Login with email
    print("\n📝 Test 2: Authentication with email")
    user_by_email = backend.authenticate(
        request=None,
        username=test_email,
        password=test_password
    )
    
    if user_by_email and user_by_email.email == test_email:
        print(f"✅ SUCCESS: User authenticated with email '{test_email}'")
    else:
        print(f"❌ FAILED: Could not authenticate with email '{test_email}'")
        return False
    
    # Test 3: Login with wrong password
    print("\n📝 Test 3: Authentication with wrong password")
    user_wrong_pass = backend.authenticate(
        request=None,
        username=test_username,
        password="WrongPassword123!"
    )
    
    if user_wrong_pass is None:
        print("✅ SUCCESS: Authentication failed with wrong password (as expected)")
    else:
        print("❌ FAILED: Authentication should have failed with wrong password")
        return False
    
    # Test 4: Login with non-existent user
    print("\n📝 Test 4: Authentication with non-existent user")
    user_nonexistent = backend.authenticate(
        request=None,
        username="nonexistentuser",
        password=test_password
    )
    
    if user_nonexistent is None:
        print("✅ SUCCESS: Authentication failed for non-existent user (as expected)")
    else:
        print("❌ FAILED: Authentication should have failed for non-existent user")
        return False
    
    # Test 5: Case-insensitive email
    print("\n📝 Test 5: Authentication with case-insensitive email")
    user_case_email = backend.authenticate(
        request=None,
        username="TESTUSER@EXAMPLE.COM",  # Uppercase email
        password=test_password
    )
    
    if user_case_email and user_case_email.email == test_email:
        print("✅ SUCCESS: User authenticated with case-insensitive email")
    else:
        print("❌ FAILED: Could not authenticate with case-insensitive email")
        return False
    
    # Test 6: Get user by ID
    print("\n📝 Test 6: Get user by ID")
    user_by_id = backend.get_user(user.id)
    
    if user_by_id and user_by_id.id == user.id:
        print(f"✅ SUCCESS: Retrieved user by ID {user.id}")
    else:
        print(f"❌ FAILED: Could not retrieve user by ID {user.id}")
        return False
    
    # Clean up test user
    try:
        user.delete()
        print(f"\n🧹 Cleaned up test user: {test_username}")
    except Exception as e:
        print(f"⚠️  Warning: Could not clean up test user: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED! Username or Email login is working correctly.")
    print("\n📋 Summary:")
    print("   ✅ Users can login with username")
    print("   ✅ Users can login with email")
    print("   ✅ Email authentication is case-insensitive")
    print("   ✅ Wrong passwords are rejected")
    print("   ✅ Non-existent users are rejected")
    print("   ✅ User retrieval by ID works")
    
    return True

if __name__ == "__main__":
    try:
        success = test_authentication_backend()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
