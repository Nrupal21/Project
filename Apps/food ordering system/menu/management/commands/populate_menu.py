"""
Django management command to populate menu with sample data.
Run with: python manage.py populate_menu
"""
from django.core.management.base import BaseCommand
from menu.models import Category, MenuItem


class Command(BaseCommand):
    """
    Custom management command to populate the menu with sample categories and items.
    This helps in quickly setting up the database with test data.
    
    Usage:
        python manage.py populate_menu
    """
    help = 'Populates the menu with sample categories and food items'

    def handle(self, *args, **kwargs):
        """
        Execute the command to create sample menu data.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        self.stdout.write(self.style.SUCCESS('Starting menu population...'))
        
        # Clear existing data (optional - comment out if you want to keep existing data)
        # Category.objects.all().delete()
        # self.stdout.write(self.style.WARNING('Cleared existing menu data'))
        
        # Create Categories
        categories_data = [
            {'name': 'Appetizers', 'description': 'Start your meal with our delicious starters', 'display_order': 1},
            {'name': 'Main Course', 'description': 'Our signature main dishes', 'display_order': 2},
            {'name': 'Desserts', 'description': 'Sweet treats to end your meal', 'display_order': 3},
            {'name': 'Beverages', 'description': 'Refreshing drinks and beverages', 'display_order': 4},
            {'name': 'Breads', 'description': 'Freshly baked breads', 'display_order': 5},
            {'name': 'Salads', 'description': 'Fresh and healthy salads', 'display_order': 6},
        ]
        
        categories = {}
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            categories[cat_data['name']] = category
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created category: {category.name}'))
            else:
                self.stdout.write(f'  Category already exists: {category.name}')
        
        # Create Menu Items
        menu_items_data = [
            # Appetizers
            {
                'category': 'Appetizers',
                'name': 'Vegetable Spring Rolls',
                'description': 'Crispy rolls filled with fresh vegetables, served with sweet chili sauce',
                'price': 120.00,
                'dietary_type': 'veg',
                'preparation_time': 15
            },
            {
                'category': 'Appetizers',
                'name': 'Chicken Wings',
                'description': 'Spicy buffalo wings with ranch dip',
                'price': 180.00,
                'dietary_type': 'non_veg',
                'preparation_time': 20
            },
            {
                'category': 'Appetizers',
                'name': 'Paneer Tikka',
                'description': 'Grilled cottage cheese marinated in Indian spices',
                'price': 160.00,
                'dietary_type': 'veg',
                'preparation_time': 20
            },
            
            # Main Course
            {
                'category': 'Main Course',
                'name': 'Butter Chicken',
                'description': 'Creamy tomato-based curry with tender chicken pieces',
                'price': 350.00,
                'dietary_type': 'non_veg',
                'preparation_time': 25
            },
            {
                'category': 'Main Course',
                'name': 'Paneer Tikka Masala',
                'description': 'Grilled cottage cheese in rich masala gravy',
                'price': 320.00,
                'dietary_type': 'veg',
                'preparation_time': 25
            },
            {
                'category': 'Main Course',
                'name': 'Vegetable Biryani',
                'description': 'Fragrant basmati rice cooked with mixed vegetables and aromatic spices',
                'price': 280.00,
                'dietary_type': 'veg',
                'preparation_time': 30
            },
            {
                'category': 'Main Course',
                'name': 'Chicken Biryani',
                'description': 'Classic biryani with tender chicken and aromatic spices',
                'price': 320.00,
                'dietary_type': 'non_veg',
                'preparation_time': 35
            },
            {
                'category': 'Main Course',
                'name': 'Dal Makhani',
                'description': 'Creamy black lentils slow-cooked to perfection',
                'price': 220.00,
                'dietary_type': 'veg',
                'preparation_time': 20
            },
            
            # Desserts
            {
                'category': 'Desserts',
                'name': 'Gulab Jamun',
                'description': 'Soft milk dumplings soaked in rose-flavored sugar syrup',
                'price': 80.00,
                'dietary_type': 'veg',
                'preparation_time': 5
            },
            {
                'category': 'Desserts',
                'name': 'Chocolate Brownie',
                'description': 'Warm chocolate brownie served with vanilla ice cream',
                'price': 120.00,
                'dietary_type': 'veg',
                'preparation_time': 10
            },
            {
                'category': 'Desserts',
                'name': 'Rasmalai',
                'description': 'Soft cottage cheese patties in sweetened milk',
                'price': 100.00,
                'dietary_type': 'veg',
                'preparation_time': 5
            },
            
            # Beverages
            {
                'category': 'Beverages',
                'name': 'Mango Lassi',
                'description': 'Sweet yogurt drink blended with fresh mangoes',
                'price': 80.00,
                'dietary_type': 'veg',
                'preparation_time': 5
            },
            {
                'category': 'Beverages',
                'name': 'Fresh Lime Soda',
                'description': 'Refreshing lime juice with soda water',
                'price': 60.00,
                'dietary_type': 'vegan',
                'preparation_time': 3
            },
            {
                'category': 'Beverages',
                'name': 'Masala Chai',
                'description': 'Traditional Indian tea with aromatic spices',
                'price': 40.00,
                'dietary_type': 'veg',
                'preparation_time': 5
            },
            
            # Breads
            {
                'category': 'Breads',
                'name': 'Butter Naan',
                'description': 'Soft leavened bread brushed with butter',
                'price': 40.00,
                'dietary_type': 'veg',
                'preparation_time': 10
            },
            {
                'category': 'Breads',
                'name': 'Garlic Naan',
                'description': 'Naan bread topped with garlic and coriander',
                'price': 50.00,
                'dietary_type': 'veg',
                'preparation_time': 10
            },
            {
                'category': 'Breads',
                'name': 'Tandoori Roti',
                'description': 'Whole wheat bread baked in tandoor',
                'price': 30.00,
                'dietary_type': 'veg',
                'preparation_time': 8
            },
            
            # Salads
            {
                'category': 'Salads',
                'name': 'Green Salad',
                'description': 'Fresh lettuce, cucumber, tomatoes with lemon dressing',
                'price': 100.00,
                'dietary_type': 'vegan',
                'preparation_time': 5
            },
            {
                'category': 'Salads',
                'name': 'Caesar Salad',
                'description': 'Crisp romaine lettuce with Caesar dressing and croutons',
                'price': 150.00,
                'dietary_type': 'veg',
                'preparation_time': 10
            },
        ]
        
        created_count = 0
        for item_data in menu_items_data:
            category_name = item_data.pop('category')
            item_data['category'] = categories[category_name]
            
            menu_item, created = MenuItem.objects.get_or_create(
                name=item_data['name'],
                defaults=item_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created menu item: {menu_item.name}'))
            else:
                self.stdout.write(f'  Menu item already exists: {menu_item.name}')
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS('Menu population completed successfully!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(f'Categories: {Category.objects.count()} total')
        self.stdout.write(f'Menu Items: {MenuItem.objects.count()} total')
        self.stdout.write(f'New items created: {created_count}')
        self.stdout.write('')
        self.stdout.write('Next steps:')
        self.stdout.write('  1. Start server: python manage.py runserver')
        self.stdout.write('  2. Visit: http://127.0.0.1:8000/')
        self.stdout.write('  3. Browse the menu and start ordering!')
        self.stdout.write('')
