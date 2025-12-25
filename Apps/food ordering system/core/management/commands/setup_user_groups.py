"""
Management command to create user groups for role-based authentication.
Creates Customer and Restaurant Owner groups with appropriate permissions.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from restaurant.models import Restaurant


class Command(BaseCommand):
    """
    Django management command to setup user groups for role-based authentication.
    
    This command creates two groups:
    1. Customer - for regular customers who can place orders
    2. Restaurant Owner - for restaurant owners who can manage their restaurants
    
    Usage:
        python manage.py setup_user_groups
    """
    
    help = 'Create user groups for role-based authentication'
    
    def handle(self, *args, **options):
        """
        Execute the command to create user groups.
        
        Creates Customer and Restaurant Owner groups with appropriate permissions.
        """
        # Create Customer group
        customer_group, created = Group.objects.get_or_create(name='Customer')
        if created:
            self.stdout.write(
                self.style.SUCCESS('Successfully created Customer group')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Customer group already exists')
            )
        
        # Create Restaurant Owner group
        restaurant_owner_group, created = Group.objects.get_or_create(name='Restaurant Owner')
        if created:
            self.stdout.write(
                self.style.SUCCESS('Successfully created Restaurant Owner group')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Restaurant Owner group already exists')
            )
        
        # Add permissions for Restaurant Owner group
        # Get permissions for Restaurant model
        restaurant_content_type = ContentType.objects.get_for_model(Restaurant)
        restaurant_permissions = Permission.objects.filter(
            content_type=restaurant_content_type
        )
        
        # Add all restaurant permissions to Restaurant Owner group
        for permission in restaurant_permissions:
            restaurant_owner_group.permissions.add(permission)
        
        self.stdout.write(
            self.style.SUCCESS('Added Restaurant permissions to Restaurant Owner group')
        )
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('GROUP SETUP SUMMARY')
        self.stdout.write('='*50)
        self.stdout.write(f'Customer group: {customer_group.name}')
        self.stdout.write(f'Restaurant Owner group: {restaurant_owner_group.name}')
        self.stdout.write(f'Restaurant Owner permissions: {restaurant_permissions.count()}')
        self.stdout.write('='*50)
        self.stdout.write(
            self.style.SUCCESS('User groups setup completed successfully!')
        )
