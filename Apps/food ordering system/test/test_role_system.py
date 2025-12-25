#!/usr/bin/env python
"""
Verification script for the Restaurant Owner role system.

This script tests the dual role management system (role field + groups)
to ensure backward compatibility and proper functionality.
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

from django.contrib.auth.models import User, Group
from customer.models import UserProfile
from core.utils.user_roles import (
    is_restaurant_owner, 
    get_user_role, 
    set_user_role,
    get_user_statistics
)


def test_role_system():
    """
    Comprehensive test of the role system functionality.
    
    Tests both role field and group-based systems for compatibility.
    """
    print("🧪 Testing Restaurant Owner Role System")
    print("=" * 50)
    
    # Test 1: Check existing users have roles
    print("\n1. Testing existing user roles...")
    users = User.objects.all()[:5]  # Test first 5 users
    
    for user in users:
        profile = user.profile
        role_from_field = profile.role
        role_from_utility = get_user_role(user)
        is_owner_from_utility = is_restaurant_owner(user)
        is_owner_from_group = user.groups.filter(name='Restaurant Owner').exists()
        
        print(f"   User: {user.username}")
        print(f"   Profile Role: {role_from_field}")
        print(f"   Utility Role: {role_from_utility}")
        print(f"   Is Owner (Utility): {is_owner_from_utility}")
        print(f"   Is Owner (Group): {is_owner_from_group}")
        
        # Verify consistency
        assert is_owner_from_utility == is_owner_from_group, \
            f"Role mismatch for {user.username}"
        print("   ✅ Consistent")
        print()
    
    # Test 2: Test role setting functionality
    print("2. Testing role setting functionality...")
    test_user = User.objects.filter(username='pizzapalace').first()
    
    if test_user:
        print(f"   Testing with user: {test_user.username}")
        
        # Test setting to customer
        success = set_user_role(test_user, 'customer')
        assert success, "Failed to set role to customer"
        assert test_user.profile.role == 'customer', "Role field not updated"
        assert not is_restaurant_owner(test_user), "Still shows as restaurant owner"
        print("   ✅ Successfully set role to customer")
        
        # Test setting back to restaurant_owner
        success = set_user_role(test_user, 'restaurant_owner')
        assert success, "Failed to set role to restaurant_owner"
        assert test_user.profile.role == 'restaurant_owner', "Role field not updated"
        assert is_restaurant_owner(test_user), "Not showing as restaurant owner"
        print("   ✅ Successfully set role to restaurant_owner")
    
    # Test 3: Test new user creation
    print("\n3. Testing new user creation...")
    new_user = User.objects.create_user(
        username='testuser123',
        email='test@example.com',
        password='testpass123'
    )
    
    print(f"   Created user: {new_user.username}")
    print(f"   Default role: {new_user.profile.role}")
    print(f"   Is restaurant owner: {is_restaurant_owner(new_user)}")
    
    # Test role assignment
    success = set_user_role(new_user, 'restaurant_owner')
    assert success, "Failed to assign restaurant owner role to new user"
    assert new_user.profile.role == 'restaurant_owner', "Role not set correctly"
    assert is_restaurant_owner(new_user), "New user not recognized as restaurant owner"
    print("   ✅ New user role assignment working")
    
    # Clean up test user
    new_user.delete()
    
    # Test 4: Test user statistics
    print("\n4. Testing user statistics...")
    stats = get_user_statistics()
    print(f"   Total users: {stats['total_users']}")
    print(f"   Restaurant owners: {stats['restaurant_owners']}")
    print(f"   Active restaurant owners: {stats['active_restaurant_owners']}")
    print(f"   Customers: {stats['customers']}")
    print("   ✅ Statistics generated successfully")
    
    # Test 5: Test role field choices
    print("\n5. Testing role field choices...")
    expected_roles = ['customer', 'restaurant_owner', 'manager', 'admin']
    actual_roles = [choice[0] for choice in UserProfile.ROLE_CHOICES]
    
    assert set(expected_roles) == set(actual_roles), \
        f"Role choices mismatch: {expected_roles} vs {actual_roles}"
    print(f"   Available roles: {actual_roles}")
    print("   ✅ Role choices correct")
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! Role system is working correctly.")
    print("\n📊 System Summary:")
    print(f"   - Total users: {User.objects.count()}")
    print(f"   - Users with profiles: {UserProfile.objects.count()}")
    print(f"   - Restaurant Owner group members: {Group.objects.get(name='Restaurant Owner').user_set.count()}")
    print(f"   - Role field consistency: ✅ Verified")


if __name__ == '__main__':
    try:
        test_role_system()
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
