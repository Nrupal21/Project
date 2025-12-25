#!/usr/bin/env python
"""
Test script to check order relationships
"""
import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

from orders.models import Order, OrderItem
from menu.models import MenuItem
from restaurant.models import Restaurant

print("=== ORDER ANALYSIS ===")
print(f"Total Orders: {Order.objects.count()}")
print(f"Total OrderItems: {OrderItem.objects.count()}")

print("\n=== ORDER DETAILS ===")
for order in Order.objects.all():
    print(f"Order {order.order_id}: {order.items.count()} items")

print("\n=== ORDERITEM DETAILS ===")
items = OrderItem.objects.select_related('order', 'menu_item__restaurant').all()
for item in items:
    restaurant_name = item.menu_item.restaurant.name if item.menu_item.restaurant else "None"
    print(f"Order {str(item.order.order_id)[:8]} -> MenuItem {item.menu_item.name} -> Restaurant {restaurant_name}")

print("\n=== RESTAURANT ANALYSIS ===")
for restaurant in Restaurant.objects.all():
    orders = Order.objects.filter(items__menu_item__restaurant=restaurant).distinct()
    print(f"Restaurant {restaurant.name}: {orders.count()} orders")
