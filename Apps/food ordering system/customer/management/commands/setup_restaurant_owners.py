"""
Management command to set up restaurant owners with proper permissions and sample data.
Creates Restaurant Owner group, sample users, and approved restaurants for testing.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db import transaction
from django.core.files.base import ContentFile
import requests
from io import BytesIO
from restaurant.models import Restaurant
from menu.models import Category, MenuItem


class Command(BaseCommand):
    """
    Django management command to set up restaurant owners for testing.
    
    This command creates:
    1. Restaurant Owner group with proper permissions
    2. Sample restaurant owner users
    3. Sample approved restaurants linked to owners
    4. Sample menu items for each restaurant
    """
    
    help = 'Set up restaurant owners with sample data for testing'
    
    def handle(self, *args, **options):
        """
        Execute the command to set up restaurant owners.
        
        Creates group, users, restaurants, and menu items.
        """
        self.stdout.write('Setting up restaurant owners...')
        
        try:
            with transaction.atomic():
                # Create Restaurant Owner group
                self.create_restaurant_owner_group()
                
                # Create sample restaurant owners
                self.create_sample_restaurant_owners()
                
            self.stdout.write(self.style.SUCCESS('Restaurant owners setup completed successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error setting up restaurant owners: {e}'))
    
    def create_restaurant_owner_group(self):
        """
        Create the Restaurant Owner group if it doesn't exist.
        """
        group, created = Group.objects.get_or_create(name='Restaurant Owner')
        
        if created:
            self.stdout.write('Created Restaurant Owner group')
        else:
            self.stdout.write('Restaurant Owner group already exists')
    
    def download_and_save_image(self, url, model_instance, field_name):
        """
        Download image from URL and save to model instance's image field.
        
        Args:
            url: Image URL to download (can be direct image URL or API URL)
            model_instance: Model instance to save image to
            field_name: Name of the image field
        """
        fallback_urls = {
            'chicken': ['https://foodish-api.com/api/images/burger', 'https://foodish-api.com/api/images/pizza'],
            'bread': ['https://foodish-api.com/api/images/pizza', 'https://foodish-api.com/api/images/burger'],
            'fries': ['https://foodish-api.com/api/images/burger', 'https://foodish-api.com/api/images/pizza'],
            'rice': ['https://foodish-api.com/api/images/pizza'],
            'dessert': ['https://foodish-api.com/api/images/pizza'],
        }
        
        urls_to_try = [url]
        
        # Add fallback URLs if this is a Foodish API URL
        if 'foodish-api.com/api/images/' in url:
            category = url.split('/')[-1]
            if category in fallback_urls:
                urls_to_try.extend(fallback_urls[category])
        
        for attempt_url in urls_to_try:
            try:
                response = requests.get(attempt_url, timeout=10)
                if response.status_code == 200:
                    # Check if response is JSON (Foodish API format)
                    if 'application/json' in response.headers.get('content-type', ''):
                        json_data = response.json()
                        if 'image' in json_data:
                            actual_image_url = json_data['image']
                            # Download the actual image
                            img_response = requests.get(actual_image_url, timeout=10)
                            if img_response.status_code == 200:
                                image_content = ContentFile(img_response.content)
                                filename = actual_image_url.split('/')[-1]
                                getattr(model_instance, field_name).save(filename, image_content, save=True)
                                if attempt_url != url:
                                    self.stdout.write(f'Downloaded image via fallback: {filename}')
                                else:
                                    self.stdout.write(f'Downloaded image: {filename}')
                                return  # Success, exit the loop
                            else:
                                self.stdout.write(f'Failed to download actual image from {actual_image_url}')
                        else:
                            self.stdout.write(f'No image URL found in API response from {attempt_url}')
                    else:
                        # Direct image download
                        image_content = ContentFile(response.content)
                        filename = attempt_url.split('/')[-1].split('?')[0]
                        if not filename.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                            filename = f"{filename}.jpg"
                        getattr(model_instance, field_name).save(filename, image_content, save=True)
                        if attempt_url != url:
                            self.stdout.write(f'Downloaded image via fallback: {filename}')
                        else:
                            self.stdout.write(f'Downloaded image: {filename}')
                        return  # Success, exit the loop
                else:
                    if attempt_url == url:
                        self.stdout.write(f'Failed to download from {url}: HTTP {response.status_code}, trying fallbacks...')
            except Exception as e:
                if attempt_url == url:
                    self.stdout.write(f'Failed to download image from {url}: {e}, trying fallbacks...')
        
        self.stdout.write(f'All download attempts failed for {url}')

    def create_sample_restaurant_owners(self):
        """
        Create sample restaurant owner users with approved restaurants.
        """
        restaurant_owners_data = [
            {
                'username': 'pizzapalace',
                'email': 'owner@pizzapalace.com',
                'password': 'restaurant123',
                'first_name': 'Mario',
                'last_name': 'Rossi',
                'restaurant': {
                    'name': 'Pizza Palace',
                    'description': 'Authentic Italian pizzas with fresh ingredients and traditional recipes',
                    'cuisine_type': 'italian',
                    'address': '123 Main Street, Downtown',
                    'phone': '+1234567890',
                    'minimum_order': 150,
                    'delivery_fee': 30,
                    'rating': 4.5,
                    'image_url': 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=800&h=600&fit=crop',
                }
            },
            {
                'username': 'burgerbarn',
                'email': 'owner@burgerbarn.com',
                'password': 'restaurant123',
                'first_name': 'John',
                'last_name': 'Smith',
                'restaurant': {
                    'name': 'Burger Barn',
                    'description': 'Juicy burgers and American comfort food',
                    'cuisine_type': 'american',
                    'address': '456 Oak Avenue, Westside',
                    'phone': '+1234567891',
                    'minimum_order': 200,
                    'delivery_fee': 0,
                    'rating': 4.2,
                    'image_url': 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800&h=600&fit=crop',
                }
            },
            {
                'username': 'spicegarden',
                'email': 'owner@spicegarden.com',
                'password': 'restaurant123',
                'first_name': 'Priya',
                'last_name': 'Sharma',
                'restaurant': {
                    'name': 'Spice Garden',
                    'description': 'Authentic Indian cuisine with aromatic spices and traditional flavors',
                    'cuisine_type': 'indian',
                    'address': '789 Curry Lane, Eastside',
                    'phone': '+1234567892',
                    'minimum_order': 250,
                    'delivery_fee': 40,
                    'rating': 4.7,
                    'image_url': 'https://images.unsplash.com/photo-1585032226651-759b368d7246?w=800&h=600&fit=crop',
                }
            },
            {
                'username': 'sushistation',
                'email': 'owner@sushistation.com',
                'password': 'restaurant123',
                'first_name': 'Takashi',
                'last_name': 'Yamamoto',
                'restaurant': {
                    'name': 'Sushi Station',
                    'description': 'Fresh Japanese sushi and traditional Asian cuisine',
                    'cuisine_type': 'japanese',
                    'address': '321 Sakura Boulevard, Northside',
                    'phone': '+1234567893',
                    'minimum_order': 300,
                    'delivery_fee': 50,
                    'rating': 4.8,
                    'image_url': 'https://images.unsplash.com/photo-1579584425555-c3ce17fd4351?w=800&h=600&fit=crop',
                }
            },
            {
                'username': 'tacosfiesta',
                'email': 'owner@tacosfiesta.com',
                'password': 'restaurant123',
                'first_name': 'Carlos',
                'last_name': 'Rodriguez',
                'restaurant': {
                    'name': 'Tacos Fiesta',
                    'description': 'Authentic Mexican street food with bold flavors',
                    'cuisine_type': 'mexican',
                    'address': '555 Fiesta Street, Southside',
                    'phone': '+1234567894',
                    'minimum_order': 180,
                    'delivery_fee': 25,
                    'rating': 4.6,
                    'image_url': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800&h=600&fit=crop',
                }
            },
            {
                'username': 'dragonwok',
                'email': 'owner@dragonwok.com',
                'password': 'restaurant123',
                'first_name': 'Wei',
                'last_name': 'Chen',
                'restaurant': {
                    'name': 'Dragon Wok',
                    'description': 'Traditional Chinese cuisine with wok-fired specialties',
                    'cuisine_type': 'chinese',
                    'address': '888 Dragon Plaza, Chinatown',
                    'phone': '+1234567895',
                    'minimum_order': 220,
                    'delivery_fee': 35,
                    'rating': 4.4,
                    'image_url': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800&h=600&fit=crop',
                }
            },
            {
                'username': 'thaibasil',
                'email': 'owner@thaibasil.com',
                'password': 'restaurant123',
                'first_name': 'Somchai',
                'last_name': 'Patel',
                'restaurant': {
                    'name': 'Thai Basil',
                    'description': 'Authentic Thai flavors with aromatic herbs and spices',
                    'cuisine_type': 'thai',
                    'address': '777 Bangkok Avenue, East District',
                    'phone': '+1234567896',
                    'minimum_order': 240,
                    'delivery_fee': 40,
                    'rating': 4.7,
                    'image_url': 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800&h=600&fit=crop',
                }
            },
            {
                'username': 'medgrill',
                'email': 'owner@medgrill.com',
                'password': 'restaurant123',
                'first_name': 'Ahmed',
                'last_name': 'Hassan',
                'restaurant': {
                    'name': 'Mediterranean Grill',
                    'description': 'Fresh Mediterranean cuisine with grilled specialties',
                    'cuisine_type': 'mediterranean',
                    'address': '444 Olive Street, Central',
                    'phone': '+1234567897',
                    'minimum_order': 260,
                    'delivery_fee': 45,
                    'rating': 4.5,
                    'image_url': 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=800&h=600&fit=crop',
                }
            }
        ]
        
        restaurant_owner_group = Group.objects.get(name='Restaurant Owner')
        
        for owner_data in restaurant_owners_data:
            # Create user
            user, created = User.objects.get_or_create(
                username=owner_data['username'],
                defaults={
                    'email': owner_data['email'],
                    'first_name': owner_data['first_name'],
                    'last_name': owner_data['last_name'],
                    'is_staff': False,
                    'is_active': True,
                }
            )
            
            if created:
                user.set_password(owner_data['password'])
                user.save()
                user.groups.add(restaurant_owner_group)
                self.stdout.write(f'Created restaurant owner: {owner_data["username"]}')
            else:
                # Ensure existing user is in the group
                user.groups.add(restaurant_owner_group)
                self.stdout.write(f'Updated existing user: {owner_data["username"]}')
            
            # Create restaurant
            restaurant_data = owner_data['restaurant']
            restaurant, created = Restaurant.objects.get_or_create(
                owner=user,
                name=restaurant_data['name'],
                defaults={
                    'description': restaurant_data['description'],
                    'cuisine_type': restaurant_data['cuisine_type'],
                    'address': restaurant_data['address'],
                    'phone': restaurant_data['phone'],
                    'minimum_order': restaurant_data['minimum_order'],
                    'delivery_fee': restaurant_data['delivery_fee'],
                    'rating': restaurant_data['rating'],
                    'is_active': True,
                    'is_approved': True,
                }
            )
            
            if created:
                # Download and save restaurant image
                if 'image_url' in restaurant_data:
                    self.download_and_save_image(restaurant_data['image_url'], restaurant, 'image')
                self.stdout.write(f'Created restaurant: {restaurant_data["name"]}')
            else:
                # Ensure existing restaurant is active and approved
                restaurant.is_active = True
                restaurant.is_approved = True
                restaurant.save()
                
                # Download image if it doesn't exist
                if 'image_url' in restaurant_data and not restaurant.image:
                    self.download_and_save_image(restaurant_data['image_url'], restaurant, 'image')
                self.stdout.write(f'Updated existing restaurant: {restaurant_data["name"]}')
            
            # Create sample menu items for the restaurant (runs for both new and existing restaurants)
            self.create_sample_menu_items(restaurant)
    
    def create_sample_menu_items(self, restaurant):
        """
        Create sample menu items for a restaurant.
        """
        # Get or create categories
        categories = {
            'italian': self.get_or_create_category('Italian'),
            'american': self.get_or_create_category('American'),
            'indian': self.get_or_create_category('Indian'),
            'japanese': self.get_or_create_category('Japanese'),
            'mexican': self.get_or_create_category('Mexican'),
            'chinese': self.get_or_create_category('Chinese'),
            'thai': self.get_or_create_category('Thai'),
            'mediterranean': self.get_or_create_category('Mediterranean'),
        }
        
        menu_items_data = {
            'italian': [
                {'name': 'Margherita Pizza', 'price': 299, 'description': 'Classic pizza with tomato sauce, mozzarella, and basil', 'prep_time': 20, 'image_url': 'https://foodish-api.com/api/images/pizza'},
                {'name': 'Pepperoni Pizza', 'price': 349, 'description': 'Pizza topped with pepperoni and mozzarella cheese', 'prep_time': 25, 'image_url': 'https://foodish-api.com/api/images/pizza'},
                {'name': 'Veggie Supreme', 'price': 319, 'description': 'Loaded with fresh vegetables and cheese', 'prep_time': 22, 'image_url': 'https://foodish-api.com/api/images/pizza'},
                {'name': 'Pasta Carbonara', 'price': 279, 'description': 'Creamy pasta with bacon and parmesan', 'prep_time': 18, 'image_url': 'https://foodish-api.com/api/images/pasta'},
                {'name': 'Lasagna', 'price': 339, 'description': 'Layered pasta with meat sauce and cheese', 'prep_time': 30, 'image_url': 'https://foodish-api.com/api/images/pasta'},
                {'name': 'Spaghetti Bolognese', 'price': 259, 'description': 'Classic meat sauce with spaghetti', 'prep_time': 22, 'image_url': 'https://foodish-api.com/api/images/pasta'},
                {'name': 'Fettuccine Alfredo', 'price': 269, 'description': 'Creamy white sauce with fettuccine pasta', 'prep_time': 18, 'image_url': 'https://foodish-api.com/api/images/pasta'},
                {'name': 'Garlic Bread', 'price': 99, 'description': 'Toasted bread with garlic butter and herbs', 'prep_time': 8, 'image_url': 'https://foodish-api.com/api/images/bread'},
                {'name': 'Bruschetta', 'price': 129, 'description': 'Toasted bread with tomatoes, garlic, and olive oil', 'prep_time': 10, 'image_url': 'https://foodish-api.com/api/images/bread'},
                {'name': 'Tiramisu', 'price': 159, 'description': 'Classic Italian coffee-flavored dessert', 'prep_time': 5, 'image_url': 'https://foodish-api.com/api/images/dessert'},
                {'name': 'Panna Cotta', 'price': 149, 'description': 'Creamy vanilla dessert with berry sauce', 'prep_time': 5, 'image_url': 'https://foodish-api.com/api/images/dessert'},
                {'name': 'Italian Soda', 'price': 79, 'description': 'Refreshing flavored soda with syrup', 'prep_time': 3, 'image_url': 'https://foodish-api.com/api/images/rice'},
            ],
            'american': [
                {'name': 'Classic Cheeseburger', 'price': 189, 'description': 'Juicy beef patty with cheese, lettuce, and tomato', 'prep_time': 15, 'image_url': 'https://foodish-api.com/api/images/burger'},
                {'name': 'BBQ Bacon Burger', 'price': 229, 'description': 'Beef patty with bacon, BBQ sauce, and onion rings', 'prep_time': 18, 'image_url': 'https://foodish-api.com/api/images/burger'},
                {'name': 'Chicken Wings', 'price': 159, 'description': 'Crispy wings with your choice of sauce', 'prep_time': 12, 'image_url': 'https://foodish-api.com/api/images/chicken'},
                {'name': 'French Fries', 'price': 89, 'description': 'Crispy golden fries with seasoning', 'prep_time': 10, 'image_url': 'https://foodish-api.com/api/images/fries'},
                {'name': 'Loaded Nachos', 'price': 199, 'description': 'Tortilla chips with cheese, jalapeños, and salsa', 'prep_time': 12, 'image_url': 'https://foodish-api.com/api/images/pizza'},
                {'name': 'Grilled Chicken Sandwich', 'price': 179, 'description': 'Grilled chicken breast with lettuce and mayo', 'prep_time': 14, 'image_url': 'https://foodish-api.com/api/images/chicken'},
                {'name': 'Veggie Burger', 'price': 169, 'description': 'Plant-based patty with fresh vegetables', 'prep_time': 15, 'image_url': 'https://foodish-api.com/api/images/burger'},
                {'name': 'Onion Rings', 'price': 99, 'description': 'Crispy battered onion rings', 'prep_time': 10, 'image_url': 'https://foodish-api.com/api/images/fries'},
                {'name': 'Mac and Cheese', 'price': 139, 'description': 'Creamy macaroni with cheese sauce', 'prep_time': 12, 'image_url': 'https://foodish-api.com/api/images/pasta'},
                {'name': 'Chicken Nuggets', 'price': 129, 'description': '10 piece crispy chicken nuggets', 'prep_time': 10, 'image_url': 'https://foodish-api.com/api/images/chicken'},
                {'name': 'Milkshake', 'price': 119, 'description': 'Thick and creamy milkshake (vanilla, chocolate, or strawberry)', 'prep_time': 5, 'image_url': 'https://foodish-api.com/api/images/dessert'},
                {'name': 'Brownie Sundae', 'price': 149, 'description': 'Warm brownie with ice cream and chocolate sauce', 'prep_time': 8, 'image_url': 'https://foodish-api.com/api/images/dessert'},
            ],
            'indian': [
                {'name': 'Butter Chicken', 'price': 289, 'description': 'Tender chicken in creamy tomato sauce', 'prep_time': 25, 'image_url': 'https://foodish-api.com/api/images/chicken'},
                {'name': 'Palak Paneer', 'price': 249, 'description': 'Cottage cheese in spinach gravy', 'prep_time': 20, 'image_url': 'https://foodish-api.com/api/images/rice'},
                {'name': 'Chicken Biryani', 'price': 319, 'description': 'Fragrant rice with spiced chicken', 'prep_time': 30, 'image_url': 'https://foodish-api.com/api/images/rice'},
                {'name': 'Dal Makhani', 'price': 219, 'description': 'Creamy black lentils with spices', 'prep_time': 25, 'image_url': 'https://foodish-api.com/api/images/rice'},
                {'name': 'Tandoori Chicken', 'price': 299, 'description': 'Grilled chicken marinated in yogurt and spices', 'prep_time': 35, 'image_url': 'https://foodish-api.com/api/images/chicken'},
                {'name': 'Chicken Tikka Masala', 'price': 279, 'description': 'Grilled chicken in spiced curry sauce', 'prep_time': 28, 'image_url': 'https://foodish-api.com/api/images/chicken'},
                {'name': 'Naan Bread', 'price': 49, 'description': 'Soft flatbread baked in tandoor', 'prep_time': 8, 'image_url': 'https://foodish-api.com/api/images/bread'},
                {'name': 'Garlic Naan', 'price': 59, 'description': 'Naan topped with garlic and butter', 'prep_time': 8, 'image_url': 'https://foodish-api.com/api/images/bread'},
                {'name': 'Samosa (2 pieces)', 'price': 89, 'description': 'Crispy pastry filled with spiced potatoes', 'prep_time': 10, 'image_url': 'https://foodish-api.com/api/images/pizza'},
                {'name': 'Paneer Tikka', 'price': 229, 'description': 'Grilled cottage cheese with spices', 'prep_time': 20, 'image_url': 'https://foodish-api.com/api/images/chicken'},
                {'name': 'Gulab Jamun', 'price': 99, 'description': 'Sweet milk dumplings in sugar syrup', 'prep_time': 5, 'image_url': 'https://foodish-api.com/api/images/dessert'},
                {'name': 'Mango Lassi', 'price': 89, 'description': 'Sweet yogurt drink with mango', 'prep_time': 5, 'image_url': 'https://foodish-api.com/api/images/dessert'},
            ],
            'japanese': [
                {'name': 'California Roll', 'price': 199, 'description': 'Crab, avocado, and cucumber sushi roll', 'prep_time': 15, 'image_url': 'https://foodish-api.com/api/images/rice'},
                {'name': 'Salmon Sashimi', 'price': 349, 'description': 'Fresh sliced salmon', 'prep_time': 10, 'image_url': 'https://foodish-api.com/api/images/chicken'},
                {'name': 'Tempura Udon', 'price': 279, 'description': 'Noodle soup with crispy tempura', 'prep_time': 20, 'image_url': 'https://foodish-api.com/api/images/rice'},
                {'name': 'Spicy Tuna Roll', 'price': 229, 'description': 'Tuna with spicy mayo and cucumber', 'prep_time': 15, 'image_url': 'https://foodish-api.com/api/images/rice'},
                {'name': 'Teriyaki Chicken', 'price': 259, 'description': 'Grilled chicken with teriyaki glaze', 'prep_time': 18, 'image_url': 'https://foodish-api.com/api/images/chicken'},
                {'name': 'Dragon Roll', 'price': 299, 'description': 'Eel and avocado with special sauce', 'prep_time': 18, 'image_url': 'https://foodish-api.com/api/images/rice'},
                {'name': 'Miso Soup', 'price': 79, 'description': 'Traditional soybean paste soup', 'prep_time': 8, 'image_url': 'https://foodish-api.com/api/images/rice'},
                {'name': 'Edamame', 'price': 99, 'description': 'Steamed soybeans with sea salt', 'prep_time': 6, 'image_url': 'https://foodish-api.com/api/images/rice'},
                {'name': 'Chicken Katsu', 'price': 269, 'description': 'Breaded and fried chicken cutlet', 'prep_time': 20, 'image_url': 'https://foodish-api.com/api/images/chicken'},
                {'name': 'Gyoza (6 pieces)', 'price': 159, 'description': 'Pan-fried dumplings with pork', 'prep_time': 12, 'image_url': 'https://foodish-api.com/api/images/pizza'},
                {'name': 'Yakisoba', 'price': 239, 'description': 'Stir-fried noodles with vegetables', 'prep_time': 16, 'image_url': 'https://foodish-api.com/api/images/rice'},
                {'name': 'Green Tea Ice Cream', 'price': 119, 'description': 'Traditional Japanese dessert', 'prep_time': 3, 'image_url': 'https://foodish-api.com/api/images/dessert'},
            ],
            'mexican': [
                {'name': 'Beef Tacos', 'price': 149, 'description': 'Three tacos with seasoned beef and toppings', 'prep_time': 12, 'image_url': 'https://foodish-api.com/api/images/pizza'},
                {'name': 'Chicken Burrito', 'price': 189, 'description': 'Large burrito with chicken, rice, and beans', 'prep_time': 15, 'image_url': 'https://foodish-api.com/api/images/pizza'},
                {'name': 'Quesadilla', 'price': 169, 'description': 'Grilled tortilla with cheese and fillings', 'prep_time': 10, 'image_url': 'https://foodish-api.com/api/images/pizza'},
                {'name': 'Nachos Supreme', 'price': 199, 'description': 'Loaded nachos with all the fixings', 'prep_time': 12, 'image_url': 'https://foodish-api.com/api/images/pizza'},
                {'name': 'Chicken Fajitas', 'price': 229, 'description': 'Sizzling chicken with peppers and onions', 'prep_time': 18, 'image_url': 'https://foodish-api.com/api/images/chicken'},
                {'name': 'Enchiladas', 'price': 199, 'description': 'Three rolled tortillas with sauce and cheese', 'prep_time': 20, 'image_url': 'https://foodish-api.com/api/images/pizza'},
                {'name': 'Taco Salad', 'price': 179, 'description': 'Crispy shell with beef, lettuce, and cheese', 'prep_time': 14, 'image_url': 'https://foodish-api.com/api/images/pizza'},
                {'name': 'Guacamole & Chips', 'price': 129, 'description': 'Fresh avocado dip with tortilla chips', 'prep_time': 8, 'image_url': 'https://foodish-api.com/api/images/bread'},
                {'name': 'Churros', 'price': 109, 'description': 'Fried dough pastry with cinnamon sugar', 'prep_time': 10, 'image_url': 'https://foodish-api.com/api/images/dessert'},
                {'name': 'Mexican Rice', 'price': 79, 'description': 'Seasoned rice with tomatoes', 'prep_time': 12, 'image_url': 'https://foodish-api.com/api/images/rice'},
                {'name': 'Refried Beans', 'price': 69, 'description': 'Traditional mashed beans', 'prep_time': 10, 'image_url': 'https://foodish-api.com/api/images/rice'},
                {'name': 'Horchata', 'price': 79, 'description': 'Sweet rice milk drink with cinnamon', 'prep_time': 3, 'image_url': 'https://foodish-api.com/api/images/dessert'},
            ],
            'chinese': [
                {'name': 'Kung Pao Chicken', 'price': 249, 'description': 'Spicy chicken with peanuts and vegetables', 'prep_time': 18, 'image_url': 'https://foodish-api.com/api/images/chicken'},
                {'name': 'Sweet and Sour Pork', 'price': 239, 'description': 'Crispy pork in tangy sauce', 'prep_time': 20, 'image_url': 'https://foodish-api.com/api/images/chicken'},
                {'name': 'Fried Rice', 'price': 159, 'description': 'Wok-fried rice with vegetables and egg', 'prep_time': 12, 'image_url': 'https://foodish-api.com/api/images/rice'},
                {'name': 'Spring Rolls', 'price': 129, 'description': 'Crispy vegetable spring rolls', 'prep_time': 10, 'image_url': 'https://foodish-api.com/api/images/pizza'},
                {'name': 'Chow Mein', 'price': 189, 'description': 'Stir-fried noodles with vegetables', 'prep_time': 15, 'image_url': 'https://foodish-api.com/api/images/rice'},
                {'name': 'General Tso Chicken', 'price': 259, 'description': 'Crispy chicken in sweet and spicy sauce', 'prep_time': 18, 'image_url': 'https://foodish-api.com/api/images/chicken'},
                {'name': 'Mapo Tofu', 'price': 219, 'description': 'Spicy tofu in Sichuan sauce', 'prep_time': 16, 'image_url': 'https://foodish-api.com/api/images/rice'},
                {'name': 'Dumplings (8 pieces)', 'price': 149, 'description': 'Steamed or fried pork dumplings', 'prep_time': 12, 'image_url': 'https://foodish-api.com/api/images/pizza'},
                {'name': 'Hot and Sour Soup', 'price': 119, 'description': 'Spicy and tangy Chinese soup', 'prep_time': 12, 'image_url': 'https://foodish-api.com/api/images/rice'},
                {'name': 'Mongolian Beef', 'price': 269, 'description': 'Tender beef with green onions', 'prep_time': 18, 'image_url': 'https://foodish-api.com/api/images/chicken'},
                {'name': 'Egg Drop Soup', 'price': 99, 'description': 'Classic soup with eggs and broth', 'prep_time': 10, 'image_url': 'https://foodish-api.com/api/images/rice'},
                {'name': 'Fortune Cookies', 'price': 39, 'description': 'Traditional Chinese cookies with fortune', 'prep_time': 2, 'image_url': 'https://foodish-api.com/api/images/bread'},
            ],
            'thai': [
                {'name': 'Pad Thai', 'price': 219, 'description': 'Stir-fried rice noodles with shrimp', 'prep_time': 18, 'image_url': 'https://foodish-api.com/api/images/rice'},
                {'name': 'Green Curry', 'price': 239, 'description': 'Spicy coconut curry with vegetables', 'prep_time': 22, 'image_url': 'https://foodish-api.com/api/images/rice'},
                {'name': 'Tom Yum Soup', 'price': 179, 'description': 'Hot and sour Thai soup', 'prep_time': 15, 'image_url': 'https://foodish-api.com/api/images/rice'},
                {'name': 'Massaman Curry', 'price': 249, 'description': 'Mild curry with peanuts and potatoes', 'prep_time': 25, 'image_url': 'https://foodish-api.com/api/images/rice'},
                {'name': 'Thai Basil Chicken', 'price': 229, 'description': 'Spicy chicken with holy basil', 'prep_time': 16, 'image_url': 'https://foodish-api.com/api/images/chicken'},
                {'name': 'Red Curry', 'price': 239, 'description': 'Spicy red curry with coconut milk', 'prep_time': 22, 'image_url': 'https://foodish-api.com/api/images/rice'},
                {'name': 'Pad See Ew', 'price': 209, 'description': 'Wide noodles with soy sauce and vegetables', 'prep_time': 16, 'image_url': 'https://foodish-api.com/api/images/rice'},
                {'name': 'Som Tam (Papaya Salad)', 'price': 159, 'description': 'Spicy green papaya salad', 'prep_time': 10, 'image_url': 'https://foodish-api.com/api/images/rice'},
                {'name': 'Spring Rolls (Fresh)', 'price': 139, 'description': 'Fresh vegetables wrapped in rice paper', 'prep_time': 12, 'image_url': 'https://foodish-api.com/api/images/pizza'},
                {'name': 'Satay Chicken', 'price': 199, 'description': 'Grilled chicken skewers with peanut sauce', 'prep_time': 18, 'image_url': 'https://foodish-api.com/api/images/chicken'},
                {'name': 'Mango Sticky Rice', 'price': 129, 'description': 'Sweet rice with fresh mango', 'prep_time': 8, 'image_url': 'https://foodish-api.com/api/images/dessert'},
                {'name': 'Thai Iced Tea', 'price': 89, 'description': 'Sweet milk tea over ice', 'prep_time': 5, 'image_url': 'https://foodish-api.com/api/images/dessert'},
            ],
            'mediterranean': [
                {'name': 'Chicken Shawarma', 'price': 219, 'description': 'Grilled chicken with tahini sauce', 'prep_time': 18, 'image_url': 'https://foodish-api.com/api/images/chicken'},
                {'name': 'Falafel Wrap', 'price': 189, 'description': 'Crispy chickpea balls in pita bread', 'prep_time': 15, 'image_url': 'https://foodish-api.com/api/images/pizza'},
                {'name': 'Hummus Platter', 'price': 149, 'description': 'Creamy hummus with pita bread', 'prep_time': 10, 'image_url': 'https://foodish-api.com/api/images/bread'},
                {'name': 'Greek Salad', 'price': 159, 'description': 'Fresh salad with feta and olives', 'prep_time': 8, 'image_url': 'https://foodish-api.com/api/images/rice'},
                {'name': 'Lamb Kebab', 'price': 299, 'description': 'Grilled lamb skewers with vegetables', 'prep_time': 20, 'image_url': 'https://foodish-api.com/api/images/chicken'},
                {'name': 'Baba Ganoush', 'price': 139, 'description': 'Roasted eggplant dip with tahini', 'prep_time': 10, 'image_url': 'https://foodish-api.com/api/images/rice'},
                {'name': 'Chicken Souvlaki', 'price': 229, 'description': 'Greek-style grilled chicken skewers', 'prep_time': 18, 'image_url': 'https://foodish-api.com/api/images/chicken'},
                {'name': 'Tabbouleh', 'price': 129, 'description': 'Fresh parsley salad with bulgur', 'prep_time': 8, 'image_url': 'https://foodish-api.com/api/images/rice'},
                {'name': 'Spanakopita', 'price': 169, 'description': 'Spinach and feta cheese pastry', 'prep_time': 15, 'image_url': 'https://foodish-api.com/api/images/pizza'},
                {'name': 'Mezze Platter', 'price': 279, 'description': 'Assorted Mediterranean appetizers', 'prep_time': 12, 'image_url': 'https://foodish-api.com/api/images/bread'},
                {'name': 'Baklava', 'price': 119, 'description': 'Sweet pastry with nuts and honey', 'prep_time': 5, 'image_url': 'https://foodish-api.com/api/images/dessert'},
                {'name': 'Turkish Coffee', 'price': 79, 'description': 'Strong traditional coffee', 'prep_time': 5, 'image_url': 'https://foodish-api.com/api/images/dessert'},
            ]
        }
        
        cuisine_type = restaurant.cuisine_type
        if cuisine_type in menu_items_data:
            category = categories[cuisine_type]
            
            for item_data in menu_items_data[cuisine_type]:
                menu_item, created = MenuItem.objects.get_or_create(
                    restaurant=restaurant,
                    category=category,
                    name=item_data['name'],
                    defaults={
                        'description': item_data['description'],
                        'price': item_data['price'],
                        'preparation_time': item_data['prep_time'],
                        'is_available': True,
                    }
                )
                
                if created:
                    # Download and save menu item image
                    if 'image_url' in item_data:
                        self.download_and_save_image(item_data['image_url'], menu_item, 'image')
                    self.stdout.write(f'Created menu item: {item_data["name"]}')
                else:
                    # Download image if it doesn't exist (check .name property for ImageField)
                    if 'image_url' in item_data and not menu_item.image.name:
                        self.download_and_save_image(item_data['image_url'], menu_item, 'image')
                        self.stdout.write(f'Updated image for existing menu item: {item_data["name"]}')
    
    def get_or_create_category(self, name):
        """
        Get or create a menu category.
        """
        category, created = Category.objects.get_or_create(
            name=name,
            defaults={'is_active': True}
        )
        return category
