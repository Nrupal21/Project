#!/usr/bin/env python
"""
Script to generate a list of menu items for finding images.
This script queries the database to show menu items and their image status.
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

from restaurant.models import Restaurant
from menu.models import Category, MenuItem

def print_separator(title):
    """Print a formatted separator with title."""
    print("\n" + "="*80)
    print(f" {title} ".center(80, "="))
    print("="*80)

def get_menu_items_with_image_status():
    """Get all menu items with their image status."""
    return MenuItem.objects.filter(is_available=True).select_related('restaurant', 'category').order_by('restaurant__name', 'category__name', 'name')

def check_image_status(menu_item):
    """Check the image status of a menu item."""
    has_image_url = bool(menu_item.image_url and menu_item.image_url.strip())
    has_uploaded_image = bool(menu_item.image and hasattr(menu_item.image, 'url'))
    
    # Get the actual image URL that would be displayed
    display_url = menu_item.get_image_url()
    
    return {
        'has_image_url': has_image_url,
        'has_uploaded_image': has_uploaded_image,
        'display_url': display_url,
        'is_fallback': display_url.startswith('/media/placeholders/') or 'image_links' in display_url
    }

def generate_image_list():
    """Generate a comprehensive list of menu items for image finding."""
    menu_items = get_menu_items_with_image_status()
    
    print_separator("🖼️ MENU ITEMS IMAGE STATUS LIST")
    print(f"Total Menu Items: {menu_items.count()}")
    
    current_restaurant = None
    current_category = None
    
    # Track statistics
    stats = {
        'total_items': 0,
        'items_with_custom_images': 0,
        'items_with_uploaded_images': 0,
        'items_using_fallbacks': 0,
        'items_needing_images': 0
    }
    
    for item in menu_items:
        image_status = check_image_status(item)
        stats['total_items'] += 1
        
        # Print restaurant header if changed
        if current_restaurant != item.restaurant:
            current_restaurant = item.restaurant
            current_category = None
            print(f"\n🍽️  {item.restaurant.name} ({item.restaurant.get_cuisine_type_display()})")
            print("-" * 80)
        
        # Print category header if changed
        if current_category != item.category:
            current_category = item.category
            print(f"\n📂 {current_category.name}:")
            print("-" * 50)
        
        # Determine image status
        status_icon = "❌"
        status_text = "NEEDS IMAGE"
        
        if image_status['has_image_url']:
            status_icon = "🌐"
            status_text = "EXTERNAL URL"
            stats['items_with_custom_images'] += 1
        elif image_status['has_uploaded_image']:
            status_icon = "📁"
            status_text = "UPLOADED"
            stats['items_with_uploaded_images'] += 1
        elif image_status['is_fallback']:
            status_icon = "🔄"
            status_text = "FALLBACK"
            stats['items_using_fallbacks'] += 1
            stats['items_needing_images'] += 1
        else:
            stats['items_needing_images'] += 1
        
        # Print menu item with image status
        dietary_icon = ""
        if item.dietary_type == 'veg':
            dietary_icon = "🌱"
        elif item.dietary_type == 'non_veg':
            dietary_icon = "🍖"
        elif item.dietary_type == 'vegan':
            dietary_icon = "🌿"
        
        print(f"  {status_icon} {dietary_icon} {item.name}")
        print(f"     💰 ₹{item.price} | {status_text}")
        
        # Show current image URL
        if image_status['display_url']:
            print(f"     🖼️  {image_status['display_url']}")
        
        print()
    
    return stats

def generate_items_needing_images():
    """Generate a focused list of items that need images."""
    menu_items = get_menu_items_with_image_status()
    
    print_separator("📋 ITEMS THAT NEED IMAGES")
    
    items_needing_images = []
    
    for item in menu_items:
        image_status = check_image_status(item)
        
        if image_status['is_fallback'] or (not image_status['has_image_url'] and not image_status['has_uploaded_image']):
            items_needing_images.append({
                'name': item.name,
                'restaurant': item.restaurant.name,
                'category': item.category.name,
                'price': item.price,
                'dietary_type': item.dietary_type,
                'current_url': image_status['display_url']
            })
    
    if not items_needing_images:
        print("✅ All menu items have proper images!")
        return
    
    print(f"📊 Total Items Needing Images: {len(items_needing_images)}")
    print("\n📝 List for Image Collection:")
    print("-" * 50)
    
    for i, item in enumerate(items_needing_images, 1):
        dietary_icon = ""
        if item['dietary_type'] == 'veg':
            dietary_icon = "🌱"
        elif item['dietary_type'] == 'non_veg':
            dietary_icon = "🍖"
        elif item['dietary_type'] == 'vegan':
            dietary_icon = "🌿"
        
        print(f"{i:2d}. {dietary_icon} {item['name']}")
        print(f"     🍽️  {item['restaurant']} | 📂 {item['category']}")
        print(f"     💰 ₹{item['price']} | 🖼️  {item['current_url']}")
        print()
    
    # Generate category-wise summary
    print("\n📊 Category-wise Summary:")
    print("-" * 30)
    
    category_count = {}
    for item in items_needing_images:
        category = item['category']
        category_count[category] = category_count.get(category, 0) + 1
    
    for category, count in sorted(category_count.items()):
        print(f"{category}: {count} items")

def generate_image_search_list():
    """Generate a simple list for searching images online."""
    menu_items = get_menu_items_with_image_status()
    
    print_separator("🔍 IMAGE SEARCH LIST")
    print("Copy this list to search for images online:")
    print("-" * 50)
    
    search_terms = set()
    
    for item in menu_items:
        image_status = check_image_status(item)
        
        # Only include items that need images
        if image_status['is_fallback'] or (not image_status['has_image_url'] and not image_status['has_uploaded_image']):
            # Create search terms
            base_name = item.name.lower()
            
            # Add basic search term
            search_terms.add(base_name)
            
            # Add cuisine-specific search term
            cuisine_term = f"{item.restaurant.get_cuisine_type_display().lower()} {base_name}"
            search_terms.add(cuisine_term)
            
            # Add food type specific term
            if item.dietary_type == 'veg':
                search_terms.add(f"vegetarian {base_name}")
            elif item.dietary_type == 'vegan':
                search_terms.add(f"vegan {base_name}")
    
    # Print search terms
    for i, term in enumerate(sorted(search_terms), 1):
        print(f"{i:2d}. {term.title()}")

def display_statistics(stats):
    """Display image statistics."""
    print_separator("📊 IMAGE STATISTICS SUMMARY")
    
    print(f"🍛 Total Menu Items: {stats['total_items']}")
    print(f"🌐 Items with External URLs: {stats['items_with_custom_images']}")
    print(f"📁 Items with Uploaded Images: {stats['items_with_uploaded_images']}")
    print(f"🔄 Items Using Fallbacks: {stats['items_using_fallbacks']}")
    print(f"❌ Items Needing Images: {stats['items_needing_images']}")
    
    # Calculate percentages
    if stats['total_items'] > 0:
        completion_rate = ((stats['items_with_custom_images'] + stats['items_with_uploaded_images']) / stats['total_items']) * 100
        print(f"\n✅ Image Completion Rate: {completion_rate:.1f}%")
        
        if stats['items_needing_images'] > 0:
            print(f"⚠️  {stats['items_needing_images']} items still need proper images")
        else:
            print("🎉 All items have proper images!")

def main():
    """Main function to generate image lists."""
    print("🖼️  MENU ITEMS IMAGE FINDER TOOL")
    print("=" * 80)
    print("This tool helps you identify menu items that need images.")
    print("=" * 80)
    
    # Generate comprehensive image status list
    stats = generate_image_list()
    
    # Generate focused list of items needing images
    generate_items_needing_images()
    
    # Generate search list for finding images
    generate_image_search_list()
    
    # Display statistics
    display_statistics(stats)
    
    print_separator("✅ IMAGE ANALYSIS COMPLETE")
    print("Use this information to find and add proper images for menu items!")

if __name__ == "__main__":
    main()
