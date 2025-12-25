"""
Quick script to check if pizzapalace123 user has restaurants associated.
This will help debug the dashboard redirect issue.
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

from django.contrib.auth.models import User
from restaurant.models import Restaurant

# Check the user
username = 'pizzapalace123'
try:
    user = User.objects.get(username=username)
    print(f"✓ User found: {user.username}")
    print(f"  - Email: {user.email}")
    print(f"  - Is staff: {user.is_staff}")
    print(f"  - Is superuser: {user.is_superuser}")
    
    # Check restaurants
    restaurants = user.restaurants.all()
    print(f"\n📊 Restaurant Check:")
    print(f"  - Has restaurants: {user.restaurants.exists()}")
    print(f"  - Restaurant count: {restaurants.count()}")
    
    if restaurants.exists():
        print(f"\n🏪 Restaurants owned by {username}:")
        for restaurant in restaurants:
            print(f"  - {restaurant.name} (ID: {restaurant.id}, Active: {restaurant.is_active})")
    else:
        print(f"\n❌ No restaurants found for user {username}")
        print(f"   This is why the dashboard redirect is failing!")
        
        # Check if there are any restaurants without owner
        orphan_restaurants = Restaurant.objects.filter(owner__isnull=True)
        if orphan_restaurants.exists():
            print(f"\n⚠️  Found {orphan_restaurants.count()} restaurants without owner:")
            for r in orphan_restaurants[:5]:
                print(f"  - {r.name} (ID: {r.id})")
        
        # Check if there are restaurants with similar names
        similar = Restaurant.objects.filter(name__icontains='pizza')
        if similar.exists():
            print(f"\n🔍 Found {similar.count()} restaurants with 'pizza' in name:")
            for r in similar[:5]:
                print(f"  - {r.name} (Owner: {r.owner.username if r.owner else 'None'})")
    
    # Check groups
    print(f"\n👥 User Groups:")
    groups = user.groups.all()
    if groups.exists():
        for group in groups:
            print(f"  - {group.name}")
    else:
        print(f"  - No groups assigned")
        
except User.DoesNotExist:
    print(f"❌ User '{username}' not found in database")
except Exception as e:
    print(f"❌ Error: {e}")
