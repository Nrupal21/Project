#!/usr/bin/env python
"""
Fix restaurant association for orders
"""
import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

from orders.models import OrderItem
from restaurant.models import Restaurant
from menu.models import MenuItem

print("=== FIXING RESTAURANT ASSOCIATIONS ===")

try:
    # Fix Pizza Palace orders
    pizza_with_owner = Restaurant.objects.get(name='Pizza Palace', owner__username='pizzapalace')
    pizza_no_owner = Restaurant.objects.get(name='Pizza Palace', owner__isnull=True)
    
    print(f"Fixing Pizza Palace orders...")
    pizza_items = OrderItem.objects.filter(menu_item__restaurant=pizza_no_owner)
    print(f"Found {pizza_items.count()} items to fix")
    
    for item in pizza_items:
        item.menu_item.restaurant = pizza_with_owner
        item.menu_item.save()
    
    # Fix Burger Barn orders
    burger_with_owner = Restaurant.objects.get(name='Burger Barn', owner__username='burgerbarn')
    burger_no_owner = Restaurant.objects.get(name='Burger Barn', owner__isnull=True)
    
    print(f"Fixing Burger Barn orders...")
    burger_items = OrderItem.objects.filter(menu_item__restaurant=burger_no_owner)
    print(f"Found {burger_items.count()} items to fix")
    
    for item in burger_items:
        item.menu_item.restaurant = burger_with_owner
        item.menu_item.save()
    
    print("Done! Verifying fixes...")
    
    # Verify the fixes
    for restaurant in Restaurant.objects.filter(owner__isnull=False):
        orders = Order.objects.filter(items__menu_item__restaurant=restaurant).distinct()
        print(f"Restaurant {restaurant.name} (Owner: {restaurant.owner.username}): {orders.count()} orders")
    
except Exception as e:
    print(f"Error: {e}")
