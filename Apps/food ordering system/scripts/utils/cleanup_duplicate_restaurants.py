#!/usr/bin/env python
"""
Clean up duplicate restaurant records
"""
import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

from restaurant.models import Restaurant
from menu.models import MenuItem

print("=== CLEANING UP DUPLICATE RESTAURANTS ===")

try:
    # Find and remove duplicate restaurants without owners
    duplicate_names = ['Pizza Palace', 'Burger Barn', 'Dragon Wok', 'Spice Garden']
    
    for name in duplicate_names:
        # Get restaurants with this name
        restaurants = Restaurant.objects.filter(name=name)
        
        if restaurants.count() > 1:
            print(f"\nProcessing duplicates for: {name}")
            
            # Find the one with an owner
            with_owner = restaurants.filter(owner__isnull=False).first()
            without_owner = restaurants.filter(owner__isnull=True)
            
            if with_owner:
                print(f"  Keeping: {with_owner.name} (Owner: {with_owner.owner.username})")
                
                # Move any remaining menu items from ownerless to owner restaurant
                for ownerless in without_owner:
                    items_to_move = MenuItem.objects.filter(restaurant=ownerless)
                    if items_to_move.exists():
                        print(f"    Moving {items_to_move.count()} menu items from ownerless restaurant")
                        items_to_move.update(restaurant=with_owner)
                    
                    print(f"    Deleting ownerless restaurant record")
                    ownerless.delete()
            else:
                print(f"  No owner found for {name}, keeping all records")
    
    print("\n=== FINAL RESTAURANT LIST ===")
    for restaurant in Restaurant.objects.all():
        owner_name = restaurant.owner.username if restaurant.owner else "No owner"
        print(f"Restaurant: {restaurant.name} (Owner: {owner_name})")
        
except Exception as e:
    print(f"Error: {e}")
