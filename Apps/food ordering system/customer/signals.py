"""
Customer app signal handlers.
Handles automatic rating updates and other review-related signals.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import RestaurantReview, MenuItemReview


@receiver(post_save, sender=RestaurantReview)
@receiver(post_delete, sender=RestaurantReview)
def update_restaurant_rating(sender, instance, **kwargs):
    """
    Automatically update restaurant's cached rating when reviews are created, updated, or deleted.
    
    Args:
        sender: The model class that sent the signal
        instance: The actual instance being saved/deleted
        **kwargs: Additional keyword arguments from the signal
    """
    if instance.restaurant:
        instance.restaurant.update_rating()


@receiver(post_save, sender=MenuItemReview)
@receiver(post_delete, sender=MenuItemReview)
def update_menu_item_rating(sender, instance, **kwargs):
    """
    Automatically update menu item's cached rating when reviews are created, updated, or deleted.
    
    Args:
        sender: The model class that sent the signal
        instance: The actual instance being saved/deleted
        **kwargs: Additional keyword arguments from the signal
    """
    if instance.menu_item:
        # Update menu item rating
        instance.menu_item.update_rating()
        
        # Also update the restaurant's rating since it affects overall restaurant rating
        if instance.menu_item.restaurant:
            instance.menu_item.restaurant.update_rating()
