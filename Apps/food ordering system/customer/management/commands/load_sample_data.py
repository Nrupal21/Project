"""
Django management command to load sample data for the food ordering system.
Creates sample restaurants, menu items, categories, and users for development/testing.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from decimal import Decimal
from restaurant.models import Restaurant
from menu.models import MenuItem, Category
from django.utils import timezone
import random


class Command(BaseCommand):
    help = 'Load sample data for the food ordering system'

    def handle(self, *args, **options):
        """Load sample data into the database."""
        self.stdout.write(self.style.SUCCESS('Loading sample data...'))
        
        # Create sample categories
        categories = self.create_categories()
        
        # Create sample restaurants
        restaurants = self.create_restaurants()
        
        # Create sample menu items
        self.create_menu_items(restaurants, categories)
        
        self.stdout.write(self.style.SUCCESS('Sample data loaded successfully!'))

    def create_categories(self):
        """Create sample menu categories."""
        self.stdout.write('Creating categories...')
        
        categories_data = [
            {'name': 'Appetizers', 'description': 'Start your meal with these delicious appetizers'},
            {'name': 'Main Course', 'description': 'Hearty main dishes to satisfy your hunger'},
            {'name': 'Desserts', 'description': 'Sweet treats to end your meal'},
            {'name': 'Beverages', 'description': 'Refreshing drinks and beverages'},
            {'name': 'Fast Food', 'description': 'Quick and delicious fast food options'},
            {'name': 'Italian', 'description': 'Authentic Italian cuisine'},
            {'name': 'Chinese', 'description': 'Traditional Chinese dishes'},
            {'name': 'Indian', 'description': 'Spicy and flavorful Indian food'},
        ]
        
        categories = []
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description'], 'is_active': True}
            )
            categories.append(category)
            if created:
                self.stdout.write(f'  Created category: {category.name}')
        
        return categories

    def create_restaurants(self):
        """Create sample restaurants."""
        self.stdout.write('Creating restaurants...')
        
        restaurants_data = [
            {
                'name': 'Pizza Palace',
                'description': 'Authentic Italian pizzas with fresh ingredients and traditional recipes',
                'cuisine_type': 'italian',
                'address': '123 Main Street, Downtown',
                'phone': '+1234567890',
                'minimum_order': 150,
                'delivery_fee': 30,
                'rating': 4.5,
                'opening_time': '11:00:00',
                'closing_time': '23:00:00',
            },
            {
                'name': 'Burger Barn',
                'description': 'Juicy burgers and American comfort food',
                'cuisine_type': 'american',
                'address': '456 Oak Avenue, Westside',
                'phone': '+1234567891',
                'minimum_order': 200,
                'delivery_fee': 0,
                'rating': 4.2,
                'opening_time': '10:00:00',
                'closing_time': '22:00:00',
            },
            {
                'name': 'Spice Garden',
                'description': 'Authentic Indian cuisine with aromatic spices and traditional flavors',
                'cuisine_type': 'indian',
                'address': '789 Curry Lane, Eastside',
                'phone': '+1234567892',
                'minimum_order': 250,
                'delivery_fee': 40,
                'rating': 4.7,
                'opening_time': '11:30:00',
                'closing_time': '23:30:00',
            },
            {
                'name': 'Dragon Wok',
                'description': 'Fresh Chinese cuisine with modern twists',
                'cuisine_type': 'chinese',
                'address': '321 Noodle Street, Chinatown',
                'phone': '+1234567893',
                'minimum_order': 180,
                'delivery_fee': 25,
                'rating': 4.3,
                'opening_time': '11:00:00',
                'closing_time': '22:30:00',
            },
            {
                'name': 'Sweet Dreams Bakery',
                'description': 'Fresh baked goods, cakes, and pastries',
                'cuisine_type': 'american',
                'address': '555 Sugar Road, Sweet District',
                'phone': '+1234567894',
                'minimum_order': 100,
                'delivery_fee': 20,
                'rating': 4.6,
                'opening_time': '08:00:00',
                'closing_time': '20:00:00',
            },
        ]
        
        restaurants = []
        for rest_data in restaurants_data:
            restaurant, created = Restaurant.objects.get_or_create(
                name=rest_data['name'],
                defaults={
                    **rest_data,
                    'is_active': True,
                    'is_approved': True,
                    'created_at': timezone.now(),
                }
            )
            restaurants.append(restaurant)
            if created:
                self.stdout.write(f'  Created restaurant: {restaurant.name}')
        
        return restaurants

    def create_menu_items(self, restaurants, categories):
        """Create sample menu items for each restaurant."""
        self.stdout.write('Creating menu items...')
        
        # Menu items for Pizza Palace
        pizza_items = [
            {'name': 'Margherita Pizza', 'description': 'Classic pizza with tomato sauce, mozzarella, and fresh basil', 'price': 299, 'dietary_type': 'veg', 'prep_time': 20, 'category': 'Italian'},
            {'name': 'Pepperoni Pizza', 'description': 'Spicy pepperoni with mozzarella cheese', 'price': 349, 'dietary_type': 'non_veg', 'prep_time': 20, 'category': 'Italian'},
            {'name': 'Veggie Supreme', 'description': 'Loaded with bell peppers, mushrooms, olives, and onions', 'price': 329, 'dietary_type': 'veg', 'prep_time': 25, 'category': 'Italian'},
            {'name': 'Chicken Wings', 'description': 'Crispy chicken wings with your choice of sauce', 'price': 249, 'dietary_type': 'non_veg', 'prep_time': 15, 'category': 'Appetizers'},
        ]
        
        # Menu items for Burger Barn
        burger_items = [
            {'name': 'Classic Cheeseburger', 'description': 'Juicy beef patty with cheese, lettuce, tomato, and pickles', 'price': 189, 'dietary_type': 'non_veg', 'prep_time': 15, 'category': 'Main Course'},
            {'name': 'Veggie Burger', 'description': 'Plant-based patty with fresh vegetables', 'price': 169, 'dietary_type': 'veg', 'prep_time': 12, 'category': 'Main Course'},
            {'name': 'French Fries', 'description': 'Crispy golden fries with sea salt', 'price': 89, 'dietary_type': 'veg', 'prep_time': 10, 'category': 'Fast Food'},
            {'name': 'Onion Rings', 'description': 'Breaded and fried onion rings', 'price': 99, 'dietary_type': 'veg', 'prep_time': 12, 'category': 'Appetizers'},
        ]
        
        # Menu items for Spice Garden
        indian_items = [
            {'name': 'Butter Chicken', 'description': 'Tender chicken in creamy tomato curry', 'price': 289, 'dietary_type': 'non_veg', 'prep_time': 25, 'category': 'Main Course'},
            {'name': 'Palak Paneer', 'description': 'Cottage cheese in spinach gravy', 'price': 249, 'dietary_type': 'veg', 'prep_time': 20, 'category': 'Main Course'},
            {'name': 'Biryani', 'description': 'Fragrant rice with aromatic spices and your choice of meat', 'price': 319, 'dietary_type': 'non_veg', 'prep_time': 30, 'category': 'Main Course'},
            {'name': 'Samosas', 'description': 'Crispy pastry filled with spiced potatoes and peas', 'price': 79, 'dietary_type': 'veg', 'prep_time': 15, 'category': 'Appetizers'},
        ]
        
        # Menu items for Dragon Wok
        chinese_items = [
            {'name': 'Sweet and Sour Chicken', 'description': 'Crispy chicken in tangy sweet and sour sauce', 'price': 259, 'dietary_type': 'non_veg', 'prep_time': 20, 'category': 'Main Course'},
            {'name': 'Vegetable Fried Rice', 'description': 'Wok-tossed rice with fresh vegetables', 'price': 179, 'dietary_type': 'veg', 'prep_time': 15, 'category': 'Main Course'},
            {'name': 'Spring Rolls', 'description': 'Crispy rolls with vegetable filling', 'price': 119, 'dietary_type': 'veg', 'prep_time': 12, 'category': 'Appetizers'},
            {'name': 'Hot and Sour Soup', 'description': 'Spicy and tangy soup with vegetables', 'price': 99, 'dietary_type': 'veg', 'prep_time': 10, 'category': 'Beverages'},
        ]
        
        # Menu items for Sweet Dreams Bakery
        bakery_items = [
            {'name': 'Chocolate Cake', 'description': 'Rich chocolate cake with creamy frosting', 'price': 149, 'dietary_type': 'veg', 'prep_time': 5, 'category': 'Desserts'},
            {'name': 'Apple Pie', 'description': 'Traditional apple pie with cinnamon', 'price': 129, 'dietary_type': 'veg', 'prep_time': 5, 'category': 'Desserts'},
            {'name': 'Croissant', 'description': 'Buttery French croissant', 'price': 59, 'dietary_type': 'veg', 'prep_time': 3, 'category': 'Fast Food'},
            {'name': 'Coffee', 'description': 'Freshly brewed coffee', 'price': 49, 'dietary_type': 'veg', 'prep_time': 5, 'category': 'Beverages'},
        ]
        
        # Map restaurants to their menu items
        restaurant_items = {
            restaurants[0]: pizza_items,  # Pizza Palace
            restaurants[1]: burger_items,  # Burger Barn
            restaurants[2]: indian_items,  # Spice Garden
            restaurants[3]: chinese_items, # Dragon Wok
            restaurants[4]: bakery_items,  # Sweet Dreams Bakery
        }
        
        # Create menu items for each restaurant
        for restaurant, items_data in restaurant_items.items():
            for item_data in items_data:
                # Find the category
                category = next((cat for cat in categories if cat.name == item_data['category']), None)
                if not category:
                    category = categories[0]  # Default to first category
                
                menu_item, created = MenuItem.objects.get_or_create(
                    restaurant=restaurant,
                    name=item_data['name'],
                    defaults={
                        'description': item_data['description'],
                        'price': Decimal(str(item_data['price'])),
                        'category': category,
                        'dietary_type': item_data['dietary_type'],
                        'preparation_time': item_data['prep_time'],
                        'is_available': True,
                    }
                )
                
                if created:
                    self.stdout.write(f'  Created menu item: {menu_item.name} at {restaurant.name}')
