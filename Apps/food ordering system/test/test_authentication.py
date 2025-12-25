#!/usr/bin/env python
"""
Test script to diagnose authentication issues in the food ordering system.

This script helps identify problems with:
1. User database connectivity
2. Password verification
3. Authentication backend configuration
4. UserProfile signal interference

Usage:
    python manage.py shell < test_authentication.py
    OR run individual commands in Django shell
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group
from customer.models import UserProfile

User = get_user_model()

def test_user_database():
    """Test if user database is accessible and has records."""
    print("=== Testing User Database ===")
    try:
        user_count = User.objects.count()
        print(f"✓ User database accessible - Found {user_count} users")
        
        # List all users (without passwords)
        users = User.objects.all()
        for user in users[:5]:  # Show first 5 users
            print(f"  - User: {user.username} | Email: {user.email} | Active: {user.is_active}")
        
        return True
    except Exception as e:
        print(f"✗ User database error: {e}")
        return False

def test_authentication_backend():
    """Test Django authentication backend."""
    print("\n=== Testing Authentication Backend ===")
    try:
        # Test with a known user if exists
        users = User.objects.all()
        if users.exists():
            test_user = users.first()
            print(f"Testing authentication backend with user: {test_user.username}")
            
            # This should fail (wrong password) but backend should work
            result = authenticate(username=test_user.username, password='definitely_wrong_password')
            if result is None:
                print("✓ Authentication backend working correctly (None returned for wrong password)")
                return True
            else:
                print("✗ Authentication backend issue - should return None for wrong password")
                return False
        else:
            print("⚠ No users found to test authentication")
            return True
    except Exception as e:
        print(f"✗ Authentication backend error: {e}")
        return False

def test_user_profiles():
    """Test UserProfile creation and signals."""
    print("\n=== Testing UserProfile System ===")
    try:
        users = User.objects.all()
        if users.exists():
            test_user = users.first()
            print(f"Testing UserProfile for user: {test_user.username}")
            
            # Check if profile exists
            try:
                profile = UserProfile.objects.get(user=test_user)
                print(f"✓ UserProfile exists: {profile.full_name}")
                return True
            except UserProfile.DoesNotExist:
                print("⚠ UserProfile does not exist - testing signal creation...")
                
                # Test signal by creating a new user
                test_username = f"test_user_{int(time.time())}"
                test_user = User.objects.create_user(
                    username=test_username,
                    email="test@example.com",
                    password="testpass123"
                )
                
                # Check if profile was created automatically
                try:
                    profile = UserProfile.objects.get(user=test_user)
                    print(f"✓ UserProfile signal working: {profile.full_name}")
                    # Clean up test user
                    test_user.delete()
                    return True
                except UserProfile.DoesNotExist:
                    print("✗ UserProfile signal not working")
                    test_user.delete()
                    return False
        else:
            print("⚠ No users found to test UserProfile")
            return True
    except Exception as e:
        print(f"✗ UserProfile system error: {e}")
        return False

def test_specific_user_credentials():
    """Test specific user credentials that might be failing."""
    print("\n=== Testing Specific User Credentials ===")
    
    # Ask for user credentials to test
    username = input("Enter username to test (or press Enter to skip): ").strip()
    if not username:
        print("Skipping specific user test")
        return True
        
    try:
        user = User.objects.get(username=username)
        print(f"✓ User found: {user.username}")
        print(f"  - Email: {user.email}")
        print(f"  - Active: {user.is_active}")
        print(f"  - Staff: {user.is_staff}")
        print(f"  - Superuser: {user.is_superuser}")
        
        # Test password verification
        password = input(f"Enter password for {username}: ").strip()
        if password:
            if user.check_password(password):
                print("✓ Password verification successful")
                
                # Test full authentication
                auth_user = authenticate(username=username, password=password)
                if auth_user:
                    print("✓ Full authentication successful")
                    return True
                else:
                    print("✗ Full authentication failed despite correct password")
                    return False
            else:
                print("✗ Password verification failed")
                return False
        
        return True
    except User.DoesNotExist:
        print(f"✗ User '{username}' not found")
        return False
    except Exception as e:
        print(f"✗ Error testing user: {e}")
        return False

def main():
    """Run all authentication tests."""
    print("Food Ordering System - Authentication Diagnostic Tool")
    print("=" * 60)
    
    tests = [
        test_user_database,
        test_authentication_backend,
        test_user_profiles,
        test_specific_user_credentials,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except KeyboardInterrupt:
            print("\nTest interrupted by user")
            break
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All authentication systems appear to be working correctly")
        print("The login issue might be related to:")
        print("  - Incorrect user credentials")
        print("  - Browser session/cookie issues")
        print("  - CSRF token problems")
        print("  - Frontend form submission issues")
    else:
        print("✗ Some authentication systems have issues that need fixing")

if __name__ == "__main__":
    import time
    main()
