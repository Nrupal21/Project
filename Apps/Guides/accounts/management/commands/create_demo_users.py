from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
import json

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates demo users with different roles and permissions'

    def handle(self, *args, **options):
        # Define demo users with their roles and permissions
        demo_users = [
            {
                'username': 'admin',
                'first_name': 'System',
                'last_name': 'Administrator',
                'email': 'admin@travelguide.com',
                'password': 'admin123',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'role': 'ADMIN',
                'permissions': {
                    'destinations': {'create': True, 'read': True, 'update': True, 'delete': True},
                    'tours': {'create': True, 'read': True, 'update': True, 'delete': True},
                    'users': {'create': True, 'read': True, 'update': True, 'delete': True}
                }
            },
            {
                'username': 'manager1',
                'first_name': 'John',
                'last_name': 'Manager',
                'email': 'manager@travelguide.com',
                'password': 'manager123',
                'is_staff': True,
                'is_superuser': False,
                'is_active': True,
                'role': 'MANAGER',
                'permissions': {
                    'destinations': {'create': True, 'read': True, 'update': True, 'delete': False},
                    'tours': {'create': True, 'read': True, 'update': True, 'delete': False},
                    'users': {'create': False, 'read': True, 'update': False, 'delete': False}
                }
            },
            {
                'username': 'guide1',
                'first_name': 'Sarah',
                'last_name': 'Guide',
                'email': 'guide@travelguide.com',
                'password': 'guide123',
                'is_staff': False,
                'is_superuser': False,
                'is_active': True,
                'role': 'LOCAL_GUIDE',
                'permissions': {
                    'destinations': {'create': False, 'read': True, 'update': False, 'delete': False},
                    'tours': {'create': False, 'read': True, 'update': True, 'delete': False},
                    'users': {'create': False, 'read': False, 'update': False, 'delete': False}
                }
            },
            {
                'username': 'user1',
                'first_name': 'Mike',
                'last_name': 'Customer',
                'email': 'user@travelguide.com',
                'password': 'user123',
                'is_staff': False,
                'is_superuser': False,
                'is_active': True,
                'role': 'TRAVELER',
                'permissions': {
                    'destinations': {'create': False, 'read': True, 'update': False, 'delete': False},
                    'tours': {'create': False, 'read': True, 'update': False, 'delete': False},
                    'users': {'create': False, 'read': False, 'update': False, 'delete': False}
                }
            }
        ]

        # Get or create admin user to set as role_assigner
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@travelguide.com',
                password='admin123'
            )

        # Create or update demo users
        for user_data in demo_users:
            with transaction.atomic():
                # Remove role and permissions from user creation data
                role = user_data.pop('role')
                permissions = user_data.pop('permissions')
                
                # Create or update user
                user, created = User.objects.update_or_create(
                    username=user_data['username'],
                    defaults=user_data
                )
                
                # Set password separately to ensure it's hashed
                if user_data['password']:
                    user.set_password(user_data['password'])
                
                # Set role and permissions
                user.role = role
                user.permissions = permissions
                user.role_assigned_by = admin_user
                
                # Add model-level permissions for admin access
                if role == 'MANAGER':
                    from django.contrib.auth.models import Permission, Group
                    from django.contrib.contenttypes.models import ContentType
                    
                    # Create or get manager group
                    manager_group, created = Group.objects.get_or_create(name='Managers')
                    
                    # Get all available permissions for the manager
                    content_types = ContentType.objects.filter(
                        app_label__in=['accounts', 'destinations', 'tours']
                    )
                    
                    # Clear existing permissions to avoid duplicates
                    manager_group.permissions.clear()
                    
                    # Add all available permissions for the specified apps
                    for content_type in content_types:
                        permissions = Permission.objects.filter(content_type=content_type)
                        for permission in permissions:
                            manager_group.permissions.add(permission)
                    
                    # Add user to manager group
                    user.groups.add(manager_group)
                
                user.save()

                action = 'Created' if created else 'Updated'
                self.stdout.write(self.style.SUCCESS(f'{action} {user.role.lower()} user: {user.username}'))

        self.stdout.write(self.style.SUCCESS('\nDemo users created/updated successfully!'))
        self.stdout.write(self.style.SUCCESS('You can now log in with any of these accounts:'))
        for user in User.objects.all():
            self.stdout.write(self.style.SUCCESS(f'Username: {user.username} | Password: {user.username}123 | Role: {user.role}'))
