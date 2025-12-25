#!/usr/bin/env python
"""
Comprehensive script to check and fix restaurant owner identification
"""
import os
import sys
import django

# Add project path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

from django.contrib.auth.models import Group, User
from restaurant.models import Restaurant, PendingRestaurant
from customer.models import UserProfile

def check_restaurant_owner_group():
    """Check if Restaurant Owner group exists and show details"""
    print("=== Restaurant Owner Group Check ===")
    
    try:
        group = Group.objects.get(name='Restaurant Owner')
        print(f"✅ Restaurant Owner group exists")
        print(f"   Group ID: {group.id}")
        print(f"   Number of users: {group.user_set.count()}")
        
        print("\n👥 Users in Restaurant Owner group:")
        for user in group.user_set.all():
            print(f"   - {user.username} (ID: {user.id}, Email: {user.email})")
            
            # Check if they have restaurants
            restaurants = Restaurant.objects.filter(owner=user)
            print(f"     Restaurants: {restaurants.count()}")
            for restaurant in restaurants:
                print(f"       * {restaurant.name} (Status: {restaurant.approval_status})")
                
        return True
    except Group.DoesNotExist:
        print("❌ Restaurant Owner group does NOT exist")
        return False
    except Exception as e:
        print(f"❌ Error checking group: {e}")
        return False

def check_pending_restaurants():
    """Check pending restaurant applications"""
    print("\n=== Pending Restaurant Applications ===")
    
    pending = PendingRestaurant.objects.all()
    print(f"Total pending applications: {pending.count()}")
    
    for app in pending:
        print(f"  - {app.restaurant_name} by {app.user.username}")
        print(f"    Status: {app.status}")
        print(f"    Applied: {app.created_at}")

def check_restaurant_owners_via_model():
    """Check restaurant owners via Restaurant model"""
    print("\n=== Restaurant Owners via Restaurant Model ===")
    
    restaurants = Restaurant.objects.all()
    print(f"Total restaurants: {restaurants.count()}")
    
    owners = set()
    for restaurant in restaurants:
        if restaurant.owner:
            owners.add(restaurant.owner)
            print(f"  - {restaurant.owner.username} owns '{restaurant.name}' ({restaurant.approval_status})")
    
    print(f"\nUnique restaurant owners: {len(owners)}")
    for owner in owners:
        print(f"  - {owner.username}")

def create_restaurant_owner_group():
    """Create the Restaurant Owner group if it doesn't exist"""
    try:
        group, created = Group.objects.get_or_create(name='Restaurant Owner')
        if created:
            print("✅ Created Restaurant Owner group")
        else:
            print("ℹ️  Restaurant Owner group already exists")
        return group
    except Exception as e:
        print(f"❌ Error creating group: {e}")
        return None

def sync_restaurant_owners():
    """Sync all restaurant owners to the Restaurant Owner group"""
    print("\n=== Syncing Restaurant Owners ===")
    
    group = create_restaurant_owner_group()
    if not group:
        return
    
    # Get all users who own approved restaurants
    approved_restaurants = Restaurant.objects.filter(approval_status='approved', owner__isnull=False)
    print(f"Found {approved_restaurants.count()} approved restaurants")
    
    synced_count = 0
    for restaurant in approved_restaurants:
        if restaurant.owner and not restaurant.owner.groups.filter(name='Restaurant Owner').exists():
            restaurant.owner.groups.add(group)
            print(f"  ✅ Added {restaurant.owner.username} to Restaurant Owner group")
            synced_count += 1
        elif restaurant.owner and restaurant.owner.groups.filter(name='Restaurant Owner').exists():
            print(f"  ℹ️  {restaurant.owner.username} already in Restaurant Owner group")
    
    print(f"\nSynced {synced_count} users to Restaurant Owner group")

def show_user_roles():
    """Show all users and their roles"""
    print("\n=== All Users and Their Roles ===")
    
    for user in User.objects.all():
        roles = []
        
        # Check if restaurant owner
        if user.groups.filter(name='Restaurant Owner').exists():
            roles.append("Restaurant Owner")
        
        # Check if staff/superuser
        if user.is_staff:
            roles.append("Staff")
        if user.is_superuser:
            roles.append("Superuser")
        
        # Check if has restaurant
        has_restaurant = Restaurant.objects.filter(owner=user).exists()
        if has_restaurant:
            roles.append("Has Restaurant")
        
        if not roles:
            roles.append("Customer")
        
        print(f"  {user.username}: {', '.join(roles)}")

if __name__ == "__main__":
    print("🔍 Restaurant Owner Status Check\n")
    
    # Check current state
    group_exists = check_restaurant_owner_group()
    check_pending_restaurants()
    check_restaurant_owners_via_model()
    show_user_roles()
    
    # Fix if needed
    if not group_exists:
        print("\n🔧 Creating Restaurant Owner group...")
        create_restaurant_owner_group()
    
    print("\n🔄 Syncing restaurant owners...")
    sync_restaurant_owners()
    
    print("\n✅ Check complete!")
