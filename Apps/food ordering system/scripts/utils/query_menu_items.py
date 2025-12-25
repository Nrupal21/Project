#!/usr/bin/env python
"""
Script to read database and provide list of all menu items present in the website.
This script queries the database to show restaurants, categories, and menu items.
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

from django.db import connection
from restaurant.models import Restaurant
from menu.models import Category, MenuItem

def print_separator(title):
    """Print a formatted separator with title."""
    print("\n" + "="*80)
    print(f" {title} ".center(80, "="))
    print("="*80)

def check_database_connection():
    """Check if database connection is working."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def get_restaurants():
    """Get all approved and active restaurants."""
    return Restaurant.objects.filter(is_approved=True, is_active=True).order_by('name')

def get_categories():
    """Get all active categories."""
    return Category.objects.filter(is_active=True).order_by('display_order', 'name')

def get_menu_items():
    """Get all available menu items."""
    return MenuItem.objects.filter(is_available=True).select_related('restaurant', 'category').order_by('restaurant__name', 'category__name', 'name')

def display_restaurants():
    """Display all restaurants."""
    restaurants = get_restaurants()
    if not restaurants:
        print("❌ No restaurants found")
        return
    
    print(f"📊 Total Restaurants: {restaurants.count()}")
    for i, restaurant in enumerate(restaurants, 1):
        print(f"\n{i}. {restaurant.name}")
        print(f"   📍 Address: {restaurant.address}")
        print(f"   📞 Phone: {restaurant.phone}")
        print(f"   🍽️  Cuisine: {restaurant.get_cuisine_type_display()}")
        print(f"   ⭐ Rating: {restaurant.rating}/5")
        print(f"   ⏰ Hours: {restaurant.opening_time} - {restaurant.closing_time}")
        print(f"   💰 Min Order: ₹{restaurant.minimum_order}")
        print(f"   🚚 Delivery Fee: ₹{restaurant.delivery_fee}")

def display_categories():
    """Display all categories."""
    categories = get_categories()
    if not categories:
        print("❌ No categories found")
        return
    
    print(f"📊 Total Categories: {categories.count()}")
    for i, category in enumerate(categories, 1):
        item_count = category.items.filter(is_available=True).count()
        print(f"{i}. {category.name} ({item_count} items)")
        if category.description:
            print(f"   📝 {category.description}")

def display_menu_items():
    """Display all menu items grouped by restaurant and category."""
    menu_items = get_menu_items()
    if not menu_items:
        print("❌ No menu items found")
        return
    
    print(f"📊 Total Menu Items: {menu_items.count()}")
    
    current_restaurant = None
    current_category = None
    
    for item in menu_items:
        # Print restaurant header if changed
        if current_restaurant != item.restaurant:
            current_restaurant = item.restaurant
            current_category = None
            print(f"\n🍽️  {item.restaurant.name} ({item.restaurant.get_cuisine_type_display()})")
            print("-" * 60)
        
        # Print category header if changed
        if current_category != item.category:
            current_category = item.category
            print(f"\n📂 {current_category.name}:")
            print("-" * 40)
        
        # Print menu item
        dietary_icon = ""
        if item.dietary_type == 'veg':
            dietary_icon = "🌱"
        elif item.dietary_type == 'non_veg':
            dietary_icon = "🍖"
        elif item.dietary_type == 'vegan':
            dietary_icon = "🌿"
        
        print(f"  {dietary_icon} {item.name}")
        print(f"     💰 ₹{item.price} | ⏱️  {item.preparation_time} min")
        if item.description:
            # Truncate description if too long
            desc = item.description[:100] + "..." if len(item.description) > 100 else item.description
            print(f"     📝 {desc}")

def display_summary():
    """Display summary statistics."""
    print_separator("📊 SUMMARY STATISTICS")
    
    restaurant_count = get_restaurants().count()
    category_count = get_categories().count()
    menu_item_count = get_menu_items().count()
    
    print(f"🍽️  Total Restaurants: {restaurant_count}")
    print(f"📂 Total Categories: {category_count}")
    print(f"🍛 Total Menu Items: {menu_item_count}")
    
    # Dietary breakdown
    veg_items = MenuItem.objects.filter(is_available=True, dietary_type='veg').count()
    non_veg_items = MenuItem.objects.filter(is_available=True, dietary_type='non_veg').count()
    vegan_items = MenuItem.objects.filter(is_available=True, dietary_type='vegan').count()
    
    print(f"\n🌱 Vegetarian Items: {veg_items}")
    print(f"🍖 Non-Vegetarian Items: {non_veg_items}")
    print(f"🌿 Vegan Items: {vegan_items}")
    
    # Cuisine breakdown
    print(f"\n🍽️  Cuisine Types:")
    for cuisine_code, cuisine_name in Restaurant.CUISINE_CHOICES:
        count = get_restaurants().filter(cuisine_type=cuisine_code).count()
        if count > 0:
            print(f"   {cuisine_name}: {count} restaurants")

def main():
    """Main function to display all menu items."""
    print_separator("🍛 FOOD ORDERING SYSTEM - MENU ITEMS DATABASE")
    
    # Check database connection
    if not check_database_connection():
        return
    
    # Display restaurants
    print_separator("🍽️  RESTAURANTS")
    display_restaurants()
    
    # Display categories
    print_separator("📂 FOOD CATEGORIES")
    display_categories()
    
    # Display menu items
    print_separator("🍛 MENU ITEMS")
    display_menu_items()
    
    # Display summary
    display_summary()
    
    print_separator("✅ QUERY COMPLETE")
    print("Database query completed successfully!")
    print("This shows all menu items currently available on the website.")

if __name__ == "__main__":
    main()
