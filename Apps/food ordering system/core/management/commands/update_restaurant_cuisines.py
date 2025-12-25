"""
Management command to update restaurant cuisine types.
Updates existing restaurants with appropriate cuisine classifications.
"""
from django.core.management.base import BaseCommand
from restaurant.models import Restaurant


class Command(BaseCommand):
    """
    Django management command to update restaurant cuisine types.
    
    Updates existing restaurants with appropriate cuisine classifications
    to enable proper filtering and categorization in the UI.
    
    Usage:
        python manage.py update_restaurant_cuisines
    """
    
    help = 'Update restaurant cuisine types for existing restaurants'
    
    def handle(self, *args, **options):
        """
        Execute the command to update restaurant cuisine types.
        """
        self.stdout.write('Updating restaurant cuisine types...')
        
        # Define cuisine types for existing restaurants
        restaurant_cuisines = {
            'Italian Bistro': 'italian',
            'Spice Garden': 'indian', 
            'Burger Palace': 'american',
            'Tasty Bites': 'other'
        }
        
        updated_count = 0
        
        for restaurant_name, cuisine_type in restaurant_cuisines.items():
            try:
                restaurant = Restaurant.objects.get(name=restaurant_name)
                restaurant.cuisine_type = cuisine_type
                restaurant.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Updated {restaurant.name} -> {restaurant.get_cuisine_type_display()}'
                    )
                )
            except Restaurant.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'❌ Restaurant not found: {restaurant_name}')
                )
        
        self.stdout.write('\n=== SUMMARY ===')
        self.stdout.write(f'Restaurants updated: {updated_count}')
        self.stdout.write(
            self.style.SUCCESS('Restaurant cuisine types updated successfully!')
        )
        
        # Display final state
        self.stdout.write('\n=== CURRENT RESTAURANTS ===')
        for restaurant in Restaurant.objects.all():
            self.stdout.write(
                f'{restaurant.name}: {restaurant.get_cuisine_type_display()}'
            )
