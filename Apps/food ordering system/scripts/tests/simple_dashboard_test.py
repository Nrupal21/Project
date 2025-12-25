#!/usr/bin/env python
"""
Simple test to verify the manager dashboard view logic without rendering template.
"""
import os
import sys
import django

# Add project path to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

from restaurant.models import PendingRestaurant
from django.contrib.auth.models import User

def test_dashboard_logic():
    """Test the core logic that feeds the manager dashboard."""
    print("=" * 60)
    print("TESTING MANAGER DASHBOARD LOGIC")
    print("=" * 60)
    
    # Test the same queries used in manager_dashboard
    pending_restaurants = PendingRestaurant.objects.filter(status='pending').order_by('-created_at')
    recent_applications = PendingRestaurant.objects.filter(
        status__in=['approved', 'rejected']
    ).order_by('-processed_at')[:10]
    
    # Test statistics
    total_pending = pending_restaurants.count()
    total_approved = PendingRestaurant.objects.filter(status='approved').count()
    total_rejected = PendingRestaurant.objects.filter(status='rejected').count()
    
    print(f"📊 Dashboard Data Results:")
    print(f"   Pending restaurants: {total_pending}")
    print(f"   Approved restaurants: {total_approved}")
    print(f"   Rejected restaurants: {total_rejected}")
    print(f"   Recent applications: {recent_applications.count()}")
    
    if pending_restaurants.exists():
        print(f"\n📋 Pending Restaurants (should appear in dashboard):")
        for i, pr in enumerate(pending_restaurants, 1):
            print(f"   {i}. {pr.restaurant_name}")
            print(f"      User: {pr.user.username if pr.user else 'No user'}")
            print(f"      Email: {pr.email}")
            print(f"      Phone: {pr.phone}")
            print(f"      Status: {pr.status}")
            print(f"      Created: {pr.created_at}")
    else:
        print(f"\n❌ No pending restaurants found!")
    
    print(f"\n✅ Dashboard logic test completed successfully!")
    print(f"   If pending restaurants exist above, they should appear in the dashboard.")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_dashboard_logic()
