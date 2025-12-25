"""
Fix restaurant ownership - Assign Pizza Palace to pizzapalace123
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

from django.contrib.auth.models import User
from restaurant.models import Restaurant

# Get the user
user = User.objects.get(username='pizzapalace123')
print(f"User: {user.username}")

# Get the restaurant (you can change this to the correct restaurant ID/name)
restaurant = Restaurant.objects.get(name='Pizza Palace')
print(f"Restaurant: {restaurant.name}")
print(f"Current owner: {restaurant.owner.username if restaurant.owner else 'None'}")

# Update the owner
restaurant.owner = user
restaurant.save()

print(f"\n✅ SUCCESS! Restaurant '{restaurant.name}' is now owned by '{user.username}'")
print(f"\nVerification:")
print(f"  - user.restaurants.exists(): {user.restaurants.exists()}")
print(f"  - user.restaurants.count(): {user.restaurants.count()}")
