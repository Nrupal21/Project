"""
Menu app models.
Defines Category and MenuItem models for the restaurant menu.
"""
from django.db import models
from core.models import TimeStampedModel
from restaurant.models import Restaurant
from django.utils.functional import cached_property
from django.db.models import Avg, Count


class Category(TimeStampedModel):
    """
    Represents a food category (e.g., Appetizers, Main Course, Desserts).
    
    Fields:
        name: Category name (max 100 characters, unique)
        description: Optional description of the category
        is_active: Boolean to enable/disable category
        display_order: Integer for sorting categories in display
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['display_order', 'name']
    
    def __str__(self):
        """
        Returns string representation of the category.
        
        Returns:
            str: Category name
        """
        return self.name


class MenuItem(TimeStampedModel):
    """
    Represents a food item in the restaurant menu.
    
    Fields:
        restaurant: Foreign key to Restaurant model
        category: Foreign key to Category model
        name: Food item name (max 200 characters)
        description: Detailed description of the food item
        price: Decimal field for item price
        image: Image upload field for food photo
        is_available: Boolean for stock availability
        is_vegetarian: Boolean indicating vegetarian status
        is_vegan: Boolean indicating vegan status
        preparation_time: Estimated time in minutes to prepare
    """
    DIETARY_CHOICES = [
        ('veg', 'Vegetarian'),
        ('non_veg', 'Non-Vegetarian'),
        ('vegan', 'Vegan'),
    ]
    
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='menu_items',
        null=True,
        blank=True
    )
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)
    image_url = models.URLField(
        max_length=500, 
        blank=True, 
        null=True,
        help_text='External image URL (takes precedence over uploaded image)'
    )
    
    def get_image_url(self):
        """
        Get menu item image URL with intelligent 4-layer fallback system.
        
        Returns priority order:
        1. External image URL from image_url field
        2. Uploaded image file from image field
        3. Category-specific placeholder images from local media directory
        4. Local default food image
        
        Includes multiple layers of error handling for robustness.
        
        Returns:
            str: Complete image URL for display in templates
        """
        try:
            # First try external image URL (highest priority)
            if self.image_url and self.image_url.strip():
                return self.image_url.strip()
        except (ValueError, AttributeError):
            pass
        
        try:
            # Second try uploaded image from database
            if self.image and hasattr(self.image, 'url'):
                return self.image.url
        except (ValueError, AttributeError, OSError):
            # Handle cases where image file is missing, corrupted, or inaccessible
            pass
        
        try:
            # Third fallback to category-specific placeholder images
            from image_links import get_menu_item_image
            
            # Determine category based on menu item name for better fallback matching
            item_name_lower = self.name.lower()
            category_map = {
                'pizza': 'pizza',
                'burger': 'burger', 
                'pasta': 'pasta',
                'chicken': 'chicken',
                'rice': 'rice',
                'dessert': 'dessert',
                'bread': 'bread',
                'fries': 'fries',
                'salad': 'salad',
                'soup': 'soup',
                'drink': 'drink',
            }
            
            # Try to match category by name
            for keyword, category in category_map.items():
                if keyword in item_name_lower:
                    return get_menu_item_image(category, 0)
            
            # Fallback to using the actual category name
            return get_menu_item_image(self.category.name.lower(), 0)
        except (ImportError, IndexError, KeyError, AttributeError):
            # Handle cases where image_links.py fails or category not found
            pass
        
        # Ultimate fallback - local default food image
        return '/media/placeholders/food_default.jpg'
    
    def get_thumbnail_url(self):
        """
        Get thumbnail version of menu item image.
        
        Returns:
            str: Thumbnail image URL or fallback
        """
        # For now, return same as get_image_url()
        # TODO: Implement actual thumbnail generation
        return self.get_image_url()
    is_available = models.BooleanField(default=True)
    dietary_type = models.CharField(
        max_length=10, 
        choices=DIETARY_CHOICES, 
        default='veg'
    )
    preparation_time = models.IntegerField(
        default=15, 
        help_text='Preparation time in minutes'
    )
    
    class Meta:
        verbose_name = 'Menu Item'
        verbose_name_plural = 'Menu Items'
        ordering = ['category', 'name']
    
    def __str__(self):
        """
        Returns string representation of the menu item.
        
        Returns:
            str: Menu item name with price
        """
        return f"{self.name} - ₹{self.price}"
    
    @cached_property
    def average_rating(self):
        """
        Calculate average rating from non-hidden menu item reviews.
        
        Returns:
            float: Average rating (0-5) with one decimal place
        """
        from customer.models import MenuItemReview
        
        avg_rating = MenuItemReview.objects.filter(
            menu_item=self,
            is_hidden=False
        ).aggregate(
            average=Avg('rating')
        )['average']
        
        return round(avg_rating, 1) if avg_rating else 0.0
    
    @cached_property
    def review_count(self):
        """
        Count non-hidden menu item reviews for this menu item.
        
        Returns:
            int: Total count of visible reviews
        """
        from customer.models import MenuItemReview
        
        count = MenuItemReview.objects.filter(
            menu_item=self,
            is_hidden=False
        ).aggregate(
            total=Count('id')
        )['total']
        
        return count or 0
    
    def get_dietary_display(self):
        """
        Get user-friendly display name for dietary type.
        
        Returns:
            str: Formatted dietary type name
        """
        dietary_labels = {
            'veg': '🌱 Vegetarian',
            'non_veg': '🍖 Non-Vegetarian',
            'vegan': '🌿 Vegan',
        }
        return dietary_labels.get(self.dietary_type, self.dietary_type.title())
    
    def update_rating(self):
        """
        Update the cached rating field based on current reviews.
        
        This method should be called when reviews are added, updated, or hidden.
        Note: MenuItem doesn't have a rating field, but this method is needed for signal consistency.
        """
        # MenuItem doesn't have a cached rating field, but we keep this method
        # for signal consistency and future use if we add one
        pass
