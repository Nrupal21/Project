"""
Image links for restaurants and menu items in the food ordering system.
This file contains categorized image URLs that can be used to populate
restaurant and menu item image fields.
Updated to use local media files instead of external URLs.
"""

# Local restaurant images - Use placeholder images from media directory
RESTAURANT_IMAGES = {
    'italian': [
        '/media/placeholders/restaurant_italian.jpg',
        '/media/placeholders/restaurant_default.jpg',
    ],
    'american': [
        '/media/placeholders/restaurant_american.jpg',
        '/media/placeholders/restaurant_default.jpg',
    ],
    'indian': [
        '/media/placeholders/restaurant_indian.jpg',
        '/media/placeholders/restaurant_default.jpg',
    ],
    'japanese': [
        '/media/placeholders/restaurant_japanese.jpg',
        '/media/placeholders/restaurant_default.jpg',
    ],
    'mexican': [
        '/media/placeholders/restaurant_mexican.jpg',
        '/media/placeholders/restaurant_default.jpg',
    ],
    'chinese': [
        '/media/placeholders/restaurant_chinese.jpg',
        '/media/placeholders/restaurant_default.jpg',
    ],
    'thai': [
        '/media/placeholders/restaurant_thai.jpg',
        '/media/placeholders/restaurant_default.jpg',
    ],
    'mediterranean': [
        '/media/placeholders/restaurant_mediterranean.jpg',
        '/media/placeholders/restaurant_default.jpg',
    ],
}

# Local menu item images - Use placeholder images from media directory
MENU_ITEM_IMAGES = {
    'pizza': [
        '/media/placeholders/pizza.jpg',
        '/media/placeholders/food_default.jpg',
    ],
    'burger': [
        '/media/placeholders/burger.jpg',
        '/media/placeholders/food_default.jpg',
    ],
    'pasta': [
        '/media/placeholders/pasta.jpg',
        '/media/placeholders/food_default.jpg',
    ],
    'chicken': [
        '/media/placeholders/chicken.jpg',
        '/media/placeholders/food_default.jpg',
    ],
    'rice': [
        '/media/placeholders/rice.jpg',
        '/media/placeholders/food_default.jpg',
    ],
    'dessert': [
        '/media/placeholders/dessert.jpg',
        '/media/placeholders/food_default.jpg',
    ],
    'bread': [
        '/media/placeholders/bread.jpg',
        '/media/placeholders/food_default.jpg',
    ],
    'fries': [
        '/media/placeholders/fries.jpg',
        '/media/placeholders/food_default.jpg',
    ],
    'salad': [
        '/media/placeholders/salad.jpg',
        '/media/placeholders/food_default.jpg',
    ],
    'soup': [
        '/media/placeholders/soup.jpg',
        '/media/placeholders/food_default.jpg',
    ],
    'drink': [
        '/media/placeholders/drink.jpg',
        '/media/placeholders/food_default.jpg',
    ],
}

# Local fallback images for when specific category images are not available
FALLBACK_IMAGES = {
    'restaurant': [
        '/media/placeholders/restaurant_default.jpg',
        '/media/placeholders/restaurant_generic.jpg',
    ],
    'menu_item': [
        '/media/placeholders/food_default.jpg',
        '/media/placeholders/menu_item_generic.jpg',
    ],
}

# Helper function to get random image from category
import random

def get_restaurant_image(cuisine_type, index=0):
    """
    Get a restaurant image URL for a specific cuisine type.
    
    Args:
        cuisine_type (str): Type of cuisine (italian, american, etc.)
        index (int): Index of image to return (0-based)
    
    Returns:
        str: Image URL or fallback URL if cuisine not found
    """
    if cuisine_type in RESTAURANT_IMAGES:
        images = RESTAURANT_IMAGES[cuisine_type]
        return images[index % len(images)]
    else:
        return FALLBACK_IMAGES['restaurant'][index % len(FALLBACK_IMAGES['restaurant'])]

def get_menu_item_image(category, index=0):
    """
    Get a menu item image URL for a specific category.
    
    Args:
        category (str): Food category (pizza, burger, pasta, etc.)
        index (int): Index of image to return (0-based)
    
    Returns:
        str: Image URL or fallback URL if category not found
    """
    if category in MENU_ITEM_IMAGES:
        images = MENU_ITEM_IMAGES[category]
        return images[index % len(images)]
    else:
        return FALLBACK_IMAGES['menu_item'][index % len(FALLBACK_IMAGES['menu_item'])]

def get_random_restaurant_image(cuisine_type=None):
    """
    Get a random restaurant image URL.
    
    Args:
        cuisine_type (str): Optional cuisine type to filter by
    
    Returns:
        str: Random image URL
    """
    if cuisine_type and cuisine_type in RESTAURANT_IMAGES:
        return random.choice(RESTAURANT_IMAGES[cuisine_type])
    else:
        all_images = []
        for images in RESTAURANT_IMAGES.values():
            all_images.extend(images)
        all_images.extend(FALLBACK_IMAGES['restaurant'])
        return random.choice(all_images)

def get_random_menu_item_image(category=None):
    """
    Get a random menu item image URL.
    
    Args:
        category (str): Optional food category to filter by
    
    Returns:
        str: Random image URL
    """
    if category and category in MENU_ITEM_IMAGES:
        return random.choice(MENU_ITEM_IMAGES[category])
    else:
        all_images = []
        for images in MENU_ITEM_IMAGES.values():
            all_images.extend(images)
        all_images.extend(FALLBACK_IMAGES['menu_item'])
        return random.choice(all_images)

# Usage examples:
# restaurant_image = get_restaurant_image('italian', 0)
# menu_image = get_menu_item_image('pizza', 2)
# random_restaurant_image = get_random_restaurant_image('japanese')
# random_menu_image = get_random_menu_item_image('burger')
