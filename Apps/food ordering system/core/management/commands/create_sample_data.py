"""
Management command to create comprehensive sample data for the food ordering system.
Creates restaurants, menu items, categories, and users with proper role assignments.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.utils.text import slugify
from decimal import Decimal
from restaurant.models import Restaurant
from menu.models import Category, MenuItem
import random


class Command(BaseCommand):
    """
    Django management command to create sample data for testing.
    
    Creates:
    - Restaurant owners and customers with proper group assignments
    - Sample restaurants with detailed information
    - Menu categories
    - Menu items for each restaurant
    
    Usage:
        python manage.py create_sample_data
    """
    
    help = 'Create comprehensive sample data for the food ordering system'
    
    def handle(self, *args, **options):
        """
        Execute the command to create sample data.
        """
        self.stdout.write('Creating sample data for Food Ordering System...')
        
        # Create users and assign groups
        self.create_users()
        
        # Create restaurants
        self.create_restaurants()
        
        # Create menu categories
        self.create_categories()
        
        # Create menu items
        self.create_menu_items()
        
        self.stdout.write(
            self.style.SUCCESS('Sample data created successfully!')
        )
    
    def create_users(self):
        """
        Create sample users with appropriate group assignments.
        """
        self.stdout.write('Creating users...')
        
        # Get or create groups
        customer_group, _ = Group.objects.get_or_create(name='Customer')
        restaurant_owner_group, _ = Group.objects.get_or_create(name='Restaurant Owner')
        
        # Create restaurant owners
        restaurant_owners = [
            {
                'username': 'italian_bistro',
                'email': 'owner@italianbistro.com',
                'password': 'password123',
                'first_name': 'Marco',
                'last_name': 'Rossi'
            },
            {
                'username': 'spice_garden',
                'email': 'owner@spicegarden.com', 
                'password': 'password123',
                'first_name': 'Priya',
                'last_name': 'Sharma'
            },
            {
                'username': 'burger_palace',
                'email': 'owner@burgerpalace.com',
                'password': 'password123', 
                'first_name': 'John',
                'last_name': 'Smith'
            }
        ]
        
        for owner_data in restaurant_owners:
            user, created = User.objects.get_or_create(
                username=owner_data['username'],
                defaults={
                    'email': owner_data['email'],
                    'first_name': owner_data['first_name'],
                    'last_name': owner_data['last_name']
                }
            )
            if created:
                user.set_password(owner_data['password'])
                user.save()
                user.groups.add(restaurant_owner_group)
                self.stdout.write(f'  Created restaurant owner: {user.username}')
        
        # Create customers
        customers = [
            {
                'username': 'customer1',
                'email': 'customer1@email.com',
                'password': 'password123',
                'first_name': 'Alice',
                'last_name': 'Johnson'
            },
            {
                'username': 'customer2', 
                'email': 'customer2@email.com',
                'password': 'password123',
                'first_name': 'Bob',
                'last_name': 'Wilson'
            }
        ]
        
        for customer_data in customers:
            user, created = User.objects.get_or_create(
                username=customer_data['username'],
                defaults={
                    'email': customer_data['email'],
                    'first_name': customer_data['first_name'],
                    'last_name': customer_data['last_name']
                }
            )
            if created:
                user.set_password(customer_data['password'])
                user.save()
                user.groups.add(customer_group)
                self.stdout.write(f'  Created customer: {user.username}')
    
    def create_restaurants(self):
        """
        Create sample restaurants.
        """
        self.stdout.write('Creating restaurants...')
        
        restaurants_data = [
            {
                'owner': User.objects.get(username='italian_bistro'),
                'name': 'Italian Bistro',
                'description': 'Authentic Italian cuisine with a modern twist. Experience the flavors of Italy with our handmade pasta and wood-fired pizzas.',
                'address': '123 Main Street, Downtown',
                'phone': '+1-555-0123',
                'email': 'info@italianbistro.com',
                'minimum_order': Decimal('15.00'),
                'delivery_fee': Decimal('3.99'),
                'rating': 4.5,
                'opening_time': '11:00',
                'closing_time': '22:00'
            },
            {
                'owner': User.objects.get(username='spice_garden'),
                'name': 'Spice Garden',
                'description': 'Traditional Indian cuisine with aromatic spices and fresh ingredients. Discover the rich flavors of Indian cooking.',
                'address': '456 Curry Lane, Food District',
                'phone': '+1-555-0124',
                'email': 'hello@spicegarden.com',
                'minimum_order': Decimal('20.00'),
                'delivery_fee': Decimal('2.99'),
                'rating': 4.7,
                'opening_time': '11:30',
                'closing_time': '23:00'
            },
            {
                'owner': User.objects.get(username='burger_palace'),
                'name': 'Burger Palace',
                'description': 'Gourmet burgers and American classics. Premium quality beef, fresh vegetables, and homemade sauces.',
                'address': '789 Grill Avenue, Fast Food Zone',
                'phone': '+1-555-0125',
                'email': 'orders@burgerpalace.com',
                'minimum_order': Decimal('12.00'),
                'delivery_fee': Decimal('4.99'),
                'rating': 4.3,
                'opening_time': '10:00',
                'closing_time': '00:00'
            }
        ]
        
        for restaurant_data in restaurants_data:
            restaurant, created = Restaurant.objects.get_or_create(
                name=restaurant_data['name'],
                defaults=restaurant_data
            )
            if created:
                self.stdout.write(f'  Created restaurant: {restaurant.name}')
    
    def create_categories(self):
        """
        Create menu categories.
        """
        self.stdout.write('Creating categories...')
        
        categories = [
            'Appetizers',
            'Main Course',
            'Desserts',
            'Beverages',
            'Soups',
            'Salads',
            'Pasta',
            'Pizza',
            'Burgers',
            'Indian Specialties'
        ]
        
        for category_name in categories:
            category, created = Category.objects.get_or_create(
                name=category_name,
                defaults={'is_active': True}
            )
            if created:
                self.stdout.write(f'  Created category: {category.name}')
    
    def create_menu_items(self):
        """
        Create menu items for each restaurant.
        """
        self.stdout.write('Creating menu items...')
        
        # Get all restaurants and categories
        restaurants = Restaurant.objects.all()
        categories = {cat.name: cat for cat in Category.objects.all()}
        
        # Menu items for Italian Bistro
        italian_bistro = restaurants.get(name='Italian Bistro')
        italian_items = [
            {
                'name': 'Bruschetta',
                'description': 'Toasted bread with tomatoes, garlic, and fresh basil',
                'price': Decimal('8.99'),
                'category': categories['Appetizers'],
                'dietary_type': 'veg'
            },
            {
                'name': 'Caesar Salad',
                'description': 'Romaine lettuce, parmesan cheese, croutons, and Caesar dressing',
                'price': Decimal('9.99'),
                'category': categories['Salads'],
                'dietary_type': 'veg'
            },
            {
                'name': 'Spaghetti Carbonara',
                'description': 'Classic pasta with eggs, bacon, parmesan, and black pepper',
                'price': Decimal('14.99'),
                'category': categories['Pasta'],
                'dietary_type': 'non_veg'
            },
            {
                'name': 'Margherita Pizza',
                'description': 'Fresh mozzarella, tomatoes, and basil on wood-fired dough',
                'price': Decimal('12.99'),
                'category': categories['Pizza'],
                'dietary_type': 'veg'
            },
            {
                'name': 'Tiramisu',
                'description': 'Classic Italian dessert with coffee-soaked ladyfingers and mascarpone',
                'price': Decimal('6.99'),
                'category': categories['Desserts'],
                'dietary_type': 'veg'
            }
        ]
        
        for item_data in italian_items:
            item, created = MenuItem.objects.get_or_create(
                name=item_data['name'],
                restaurant=italian_bistro,
                defaults=item_data
            )
            if created:
                self.stdout.write(f'  Created menu item: {item.name} ({italian_bistro.name})')
        
        # Menu items for Spice Garden
        spice_garden = restaurants.get(name='Spice Garden')
        spice_items = [
            {
                'name': 'Samosa',
                'description': 'Crispy pastry filled with spiced potatoes and peas',
                'price': Decimal('7.99'),
                'category': categories['Appetizers'],
                'dietary_type': 'veg'
            },
            {
                'name': 'Chicken Tikka Masala',
                'description': 'Tender chicken in creamy tomato sauce with aromatic spices',
                'price': Decimal('16.99'),
                'category': categories['Indian Specialties'],
                'dietary_type': 'non_veg'
            },
            {
                'name': 'Palak Paneer',
                'description': 'Cottage cheese cubes in creamy spinach sauce',
                'price': Decimal('14.99'),
                'category': categories['Indian Specialties'],
                'dietary_type': 'veg'
            },
            {
                'name': 'Naan Bread',
                'description': 'Traditional Indian flatbread baked in tandoor',
                'price': Decimal('3.99'),
                'category': categories['Main Course'],
                'dietary_type': 'veg'
            },
            {
                'name': 'Mango Lassi',
                'description': 'Sweet yogurt drink with mango pulp',
                'price': Decimal('4.99'),
                'category': categories['Beverages'],
                'dietary_type': 'veg'
            }
        ]
        
        for item_data in spice_items:
            item, created = MenuItem.objects.get_or_create(
                name=item_data['name'],
                restaurant=spice_garden,
                defaults=item_data
            )
            if created:
                self.stdout.write(f'  Created menu item: {item.name} ({spice_garden.name})')
        
        # Menu items for Burger Palace
        burger_palace = restaurants.get(name='Burger Palace')
        burger_items = [
            {
                'name': 'Classic Cheeseburger',
                'description': 'Beef patty with cheese, lettuce, tomato, and special sauce',
                'price': Decimal('10.99'),
                'category': categories['Burgers'],
                'dietary_type': 'non_veg'
            },
            {
                'name': 'BBQ Bacon Burger',
                'description': 'Beef patty with bacon, BBQ sauce, onion rings, and cheese',
                'price': Decimal('12.99'),
                'category': categories['Burgers'],
                'dietary_type': 'non_veg'
            },
            {
                'name': 'Veggie Burger',
                'description': 'Plant-based patty with fresh vegetables and herbs',
                'price': Decimal('9.99'),
                'category': categories['Burgers'],
                'dietary_type': 'veg'
            },
            {
                'name': 'French Fries',
                'description': 'Crispy golden potato fries with sea salt',
                'price': Decimal('4.99'),
                'category': categories['Appetizers'],
                'dietary_type': 'veg'
            },
            {
                'name': 'Chocolate Milkshake',
                'description': 'Thick and creamy milkshake with premium chocolate',
                'price': Decimal('5.99'),
                'category': categories['Beverages'],
                'dietary_type': 'veg'
            }
        ]
        
        for item_data in burger_items:
            item, created = MenuItem.objects.get_or_create(
                name=item_data['name'],
                restaurant=burger_palace,
                defaults=item_data
            )
            if created:
                self.stdout.write(f'  Created menu item: {item.name} ({burger_palace.name})')
        
        self.stdout.write('Menu items creation completed!')
