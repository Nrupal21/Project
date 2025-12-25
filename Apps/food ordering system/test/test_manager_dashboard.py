#!/usr/bin/env python
"""
Test the manager dashboard view to verify pending restaurants are displayed correctly.
"""
import os
import sys
import django

# Add project path to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from restaurant.views import manager_dashboard
from restaurant.models import PendingRestaurant

def test_manager_dashboard():
    """Test the manager dashboard view with pending restaurants."""
    print("=" * 60)
    print("TESTING MANAGER DASHBOARD VIEW")
    print("=" * 60)
    
    # Create a mock request
    factory = RequestFactory()
    
    # Get or create a staff user
    try:
        staff_user = User.objects.get(username='nrupal21')
        if not staff_user.is_staff:
            staff_user.is_staff = True
            staff_user.save()
            print(f"✅ Made {staff_user.username} a staff user")
        else:
            print(f"✅ {staff_user.username} is already a staff user")
    except User.DoesNotExist:
        print("❌ Staff user not found. Creating test staff user...")
        staff_user = User.objects.create_user(
            username='test_staff',
            email='staff@test.com',
            password='testpass123',
            is_staff=True
        )
        print(f"✅ Created test staff user: {staff_user.username}")
    
    # Create a mock GET request
    request = factory.get('/restaurant/manager/dashboard/')
    request.user = staff_user
    
    print(f"\n📊 Testing with user: {request.user.username}")
    print(f"   Is Staff: {request.user.is_staff}")
    print(f"   Is Superuser: {request.user.is_superuser}")
    
    # Call the view
    try:
        response = manager_dashboard(request)
        print(f"✅ View executed successfully")
        print(f"   Status Code: {response.status_code}")
        print(f"   Template Used: {response.templates[0].name if hasattr(response, 'templates') else 'Unknown'}")
        
        # Check context data
        if hasattr(response, 'context_data'):
            context = response.context_data
            pending_restaurants = context.get('pending_restaurants', [])
            
            print(f"\n📋 Context Data:")
            print(f"   pending_restaurants count: {len(pending_restaurants)}")
            print(f"   total_pending: {context.get('total_pending', 0)}")
            print(f"   total_approved: {context.get('total_approved', 0)}")
            print(f"   total_rejected: {context.get('total_rejected', 0)}")
            
            if pending_restaurants:
                print(f"\n📝 Pending Restaurants in Context:")
                for i, pr in enumerate(pending_restaurants, 1):
                    print(f"   {i}. {pr.restaurant_name} - {pr.status}")
            else:
                print(f"\n❌ No pending restaurants found in context!")
        else:
            print(f"\n❌ No context data available in response")
            
    except Exception as e:
        print(f"❌ Error executing view: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_manager_dashboard()
