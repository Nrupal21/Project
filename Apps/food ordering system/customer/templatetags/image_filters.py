"""
Template filters for handling image URLs with intelligent fallbacks.
Centralizes image logic to avoid duplication across templates.
"""
from django import template
from django.conf import settings

register = template.Library()

@register.filter
def get_image_url(obj, size='full'):
    """
    Get image URL from any object with intelligent fallback.
    
    Args:
        obj: Model object with get_image_url() method
        size (str): Image size ('full' or 'thumbnail')
    
    Returns:
        str: Complete image URL with fallback
    """
    if not obj:
        return get_default_image_url(size)
    
    try:
        if size == 'thumbnail' and hasattr(obj, 'get_thumbnail_url'):
            return obj.get_thumbnail_url()
        elif hasattr(obj, 'get_image_url'):
            return obj.get_image_url()
    except (AttributeError, ValueError):
        pass
    
    return get_default_image_url(size)

@register.filter
def get_restaurant_image(restaurant, size='full'):
    """
    Get restaurant image URL with cuisine-specific fallback.
    
    Args:
        restaurant: Restaurant model instance
        size (str): Image size ('full' or 'thumbnail')
    
    Returns:
        str: Restaurant image URL
    """
    return get_image_url(restaurant, size)

@register.filter
def get_menu_item_image(menu_item, size='full'):
    """
    Get menu item image URL with category-specific fallback.
    
    Args:
        menu_item: MenuItem model instance
        size (str): Image size ('full' or 'thumbnail')
    
    Returns:
        str: Menu item image URL
    """
    return get_image_url(menu_item, size)

@register.filter
def get_profile_image(user, size='full'):
    """
    Get user profile image URL with intelligent fallback.
    
    Args:
        user: User model instance
        size (str): Image size ('full' or 'thumbnail')
    
    Returns:
        str: Profile image URL
    """
    if hasattr(user, 'profile'):
        return get_image_url(user.profile, size)
    else:
        return get_default_image_url(size, 'profile')

@register.filter
def is_in_wishlist(restaurant, user):
    """
    Check if a restaurant is in the user's wishlist.
    
    Args:
        restaurant: Restaurant model instance
        user: User model instance
    
    Returns:
        bool: True if restaurant is in user's wishlist, False otherwise
    """
    if not user or not user.is_authenticated:
        return False
    
    try:
        from customer.models import Wishlist
        return Wishlist.objects.filter(user=user, restaurant=restaurant).exists()
    except (AttributeError, ImportError):
        return False

@register.simple_tag
def get_default_image_url(size='full', image_type='general'):
    """
    Get default image URL based on type and size.
    Updated to use local media files instead of external URLs.
    
    Args:
        size (str): Image size ('full' or 'thumbnail')
        image_type (str): Type of image ('general', 'restaurant', 'menu_item', 'profile')
    
    Returns:
        str: Default image URL
    """
    from scripts.utils.image_links import FALLBACK_IMAGES
    
    if image_type == 'restaurant':
        images = FALLBACK_IMAGES['restaurant']
    elif image_type == 'menu_item':
        images = FALLBACK_IMAGES['menu_item']
    elif image_type == 'profile':
        return '/media/placeholders/user_default.jpg'
    else:
        # General fallback
        return '/media/placeholders/general_default.jpg'
    
    # Return first image from fallback list
    return images[0] if images else get_default_image_url(size, 'general')

@register.filter
def has_custom_image(obj):
    """
    Check if object has a custom uploaded image (not using fallback).
    
    Args:
        obj: Model object with image field
    
    Returns:
        bool: True if object has custom uploaded image
    """
    try:
        if hasattr(obj, 'image') and obj.image:
            return obj.image and hasattr(obj.image, 'url')
        elif hasattr(obj, 'profile_picture') and obj.profile_picture:
            return obj.profile_picture and hasattr(obj.profile_picture, 'url')
    except (AttributeError, ValueError):
        pass
    
    return False
