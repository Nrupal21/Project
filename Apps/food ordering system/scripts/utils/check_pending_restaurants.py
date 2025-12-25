#!/usr/bin/env python
"""
Check if restaurant registrations are being saved to the database.
"""
import os
import sys
import django

# Add project path to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

from restaurant.models import PendingRestaurant, Restaurant
from django.contrib.auth.models import User

def check_pending_restaurants():
    """Check the database for pending restaurant applications."""
    print("=" * 60)
    print("CHECKING PENDING RESTAURANT APPLICATIONS")
    print("=" * 60)
    
    # Check PendingRestaurant count
    pending_count = PendingRestaurant.objects.count()
    print(f"\n📊 Total PendingRestaurant records: {pending_count}")
    
    if pending_count > 0:
        print("\n📋 Pending Restaurant Applications:")
        for i, pr in enumerate(PendingRestaurant.objects.all(), 1):
            print(f"\n{i}. {pr.restaurant_name}")
            print(f"   Status: {pr.status}")
            print(f"   User: {pr.user.username if pr.user else 'No user'}")
            print(f"   Email: {pr.email}")
            print(f"   Phone: {pr.phone}")
            print(f"   Cuisine: {pr.cuisine_type}")
            print(f"   Created: {pr.created_at}")
            print(f"   Updated: {pr.updated_at}")
    else:
        print("\n❌ No pending restaurant applications found in database.")
    
    # Check regular Restaurant count
    restaurant_count = Restaurant.objects.count()
    print(f"\n📊 Total Restaurant records: {restaurant_count}")
    
    if restaurant_count > 0:
        print("\n📋 Approved Restaurants:")
        for i, r in enumerate(Restaurant.objects.all(), 1):
            print(f"\n{i}. {r.name}")
            print(f"   Status: {r.approval_status}")
            print(f"   Owner: {r.owner.username if r.owner else 'No owner'}")
            print(f"   Created: {r.created_at}")
    
    # Check recent users (who might have submitted applications)
    print("\n📊 Recent Users (last 5):")
    recent_users = User.objects.all().order_by('-date_joined')[:5]
    for i, user in enumerate(recent_users, 1):
        print(f"\n{i}. {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Joined: {user.date_joined}")
        print(f"   Staff: {user.is_staff}")
        print(f"   Active: {user.is_active}")
    
    print("\n" + "=" * 60)
    print("CHECK COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    check_pending_restaurants()
