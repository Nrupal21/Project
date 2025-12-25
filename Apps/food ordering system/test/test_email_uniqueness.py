#!/usr/bin/env python
"""
Test script to verify email uniqueness validation in registration forms.

This script tests that the registration forms properly prevent duplicate
email addresses with different cases (e.g., test@example.com vs Test@Example.com).
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
from core.forms import UnifiedRegistrationForm, RestaurantRegistrationForm

def test_email_uniqueness_validation():
    """
    Test email uniqueness validation in registration forms.
    
    This function creates test users and verifies that registration forms
    properly reject duplicate email addresses, regardless of case.
    """
    User = get_user_model()
    
    print("🔧 Testing Email Uniqueness Validation")
    print("=" * 60)
    
    # Test data
    test_email_1 = "testuser@example.com"
    test_email_2 = "TestUser@Example.com"  # Same email, different case
    test_username_1 = "testuser1"
    test_username_2 = "testuser2"
    test_password = "TestPass123!"
    
    # Clean up any existing test users
    User.objects.filter(username__in=[test_username_1, test_username_2]).delete()
    User.objects.filter(email__iexact=test_email_1).delete()
    
    # Create first user
    try:
        user1 = User.objects.create_user(
            username=test_username_1,
            email=test_email_1,
            password=test_password
        )
        print(f"✅ Created first user: {test_username_1} ({test_email_1})")
    except Exception as e:
        print(f"❌ Error creating first user: {e}")
        return False
    
    # Test 1: UnifiedRegistrationForm with exact same email
    print("\n📝 Test 1: UnifiedRegistrationForm with exact same email")
    form_data_exact = {
        'username': 'newuser1',
        'email': test_email_1,  # Exact same email
        'password': test_password,
        'password_confirm': test_password,
        'full_name': 'Test User',
        'phone_number': '+1234567890'
    }
    
    form1 = UnifiedRegistrationForm(data=form_data_exact)
    is_valid1 = form1.is_valid()
    
    if not is_valid1 and 'email' in form1.errors:
        print("✅ SUCCESS: Form rejected exact duplicate email")
        print(f"   Error: {form1.errors['email'][0]}")
    else:
        print("❌ FAILED: Form should have rejected exact duplicate email")
        return False
    
    # Test 2: UnifiedRegistrationForm with different case
    print("\n📝 Test 2: UnifiedRegistrationForm with different case email")
    form_data_case = {
        'username': 'newuser2',
        'email': test_email_2,  # Same email, different case
        'password': test_password,
        'password_confirm': test_password,
        'full_name': 'Test User 2',
        'phone_number': '+1234567890'
    }
    
    form2 = UnifiedRegistrationForm(data=form_data_case)
    is_valid2 = form2.is_valid()
    
    if not is_valid2 and 'email' in form2.errors:
        print("✅ SUCCESS: Form rejected case-insensitive duplicate email")
        print(f"   Error: {form2.errors['email'][0]}")
    else:
        print("❌ FAILED: Form should have rejected case-insensitive duplicate email")
        return False
    
    # Test 3: RestaurantRegistrationForm with different case
    print("\n📝 Test 3: RestaurantRegistrationForm with different case email")
    form_data_restaurant = {
        'username': 'newuser3',
        'email': test_email_2.upper(),  # Same email, uppercase
        'password': test_password,
        'password_confirm': test_password,
        'restaurant_name': 'Test Restaurant',
        'description': 'Test description',
        'address': 'Test address',
        'phone': '+1234567890',
        'cuisine_type': 'other'
    }
    
    form3 = RestaurantRegistrationForm(data=form_data_restaurant)
    is_valid3 = form3.is_valid()
    
    if not is_valid3 and 'email' in form3.errors:
        print("✅ SUCCESS: Restaurant form rejected case-insensitive duplicate email")
        print(f"   Error: {form3.errors['email'][0]}")
    else:
        print("❌ FAILED: Restaurant form should have rejected case-insensitive duplicate email")
        return False
    
    # Test 4: Valid new email should work
    print("\n📝 Test 4: Valid new email should be accepted")
    form_data_valid = {
        'username': 'newuser4',
        'email': 'different@example.com',  # Different email
        'password': test_password,
        'password_confirm': test_password,
        'full_name': 'Different User',
        'phone_number': '+1234567890'
    }
    
    form4 = UnifiedRegistrationForm(data=form_data_valid)
    is_valid4 = form4.is_valid()
    
    if is_valid4:
        print("✅ SUCCESS: Form accepted valid new email")
    else:
        print("❌ FAILED: Form should have accepted valid new email")
        print(f"   Errors: {form4.errors}")
        return False
    
    # Clean up test user
    try:
        user1.delete()
        print(f"\n🧹 Cleaned up test user: {test_username_1}")
    except Exception as e:
        print(f"⚠️  Warning: Could not clean up test user: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 ALL EMAIL VALIDATION TESTS PASSED!")
    print("\n📋 Summary:")
    print("   ✅ Forms reject exact duplicate emails")
    print("   ✅ Forms reject case-insensitive duplicate emails")
    print("   ✅ Both registration forms enforce email uniqueness")
    print("   ✅ Valid new emails are accepted")
    
    return True

if __name__ == "__main__":
    try:
        success = test_email_uniqueness_validation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
