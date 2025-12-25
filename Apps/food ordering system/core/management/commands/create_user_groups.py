"""
Management command to create required user groups for the food ordering system.

This command creates the following Django groups if they don't exist:
- Customer: For regular food ordering customers
- Restaurant Owner: For restaurant owners/managers

Usage:
    python manage.py create_user_groups

This ensures that user registration can properly assign users to the correct groups
without failing due to missing groups.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    """
    Django management command to create required user groups.
    
    Creates the necessary groups for role-based user management in the food ordering system.
    """
    help = 'Create required user groups (Customer, Restaurant Owner) for the food ordering system'
    
    def handle(self, *args, **options):
        """
        Execute the command to create required user groups.
        
        Creates the Customer and Restaurant Owner groups if they don't already exist.
        Provides feedback on created or existing groups.
        
        Args:
            *args: Command line arguments
            **options: Command line options
        """
        # Define the required groups
        required_groups = [
            {
                'name': 'Customer',
                'description': 'Regular food ordering customers who browse restaurants and place orders'
            },
            {
                'name': 'Restaurant Owner',
                'description': 'Restaurant owners/managers who manage menus and view orders'
            }
        ]
        
        created_count = 0
        existing_count = 0
        
        for group_info in required_groups:
            group_name = group_info['name']
            description = group_info['description']
            
            # Check if group already exists
            group, created = Group.objects.get_or_create(
                name=group_name,
                defaults={'description': description} if hasattr(Group, 'description') else {}
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created group: {group_name}')
                )
            else:
                existing_count += 1
                self.stdout.write(
                    self.style.WARNING(f'• Group already exists: {group_name}')
                )
        
        # Summary
        total_groups = created_count + existing_count
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'Group Creation Summary:')
        self.stdout.write(f'  Total groups processed: {total_groups}')
        self.stdout.write(f'  New groups created: {created_count}')
        self.stdout.write(f'  Existing groups found: {existing_count}')
        self.stdout.write('='*50)
        
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS('\n✅ User groups setup complete! Registration system is ready.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\n✅ All required user groups already exist. Registration system is ready.')
            )
        
        # Additional setup information
        self.stdout.write('\n📋 Next Steps:')
        self.stdout.write('1. Test user registration at /register/')
        self.stdout.write('2. Verify users are assigned to correct groups')
        self.stdout.write('3. Test role-based login redirection')
        self.stdout.write('\n🔗 Registration Flow:')
        self.stdout.write('  • Customer → Home page after login')
        self.stdout.write('  • Restaurant Owner → Restaurant dashboard after login')
