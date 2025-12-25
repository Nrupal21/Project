"""
Management command to sync user roles with the new role field.

This command updates the role field in UserProfile based on existing group membership,
ensuring backward compatibility and proper role synchronization.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from customer.models import UserProfile
from core.utils.user_roles import set_user_role


class Command(BaseCommand):
    """
    Django management command to synchronize user roles.
    
    This command updates the role field in UserProfile for all existing users
    based on their current group membership, ensuring the new role-based system
    works seamlessly with the existing group-based system.
    """
    
    help = 'Sync user roles with the new role field based on group membership'
    
    def add_arguments(self, parser):
        """
        Add command line arguments.
        
        Args:
            parser: Argument parser instance
        """
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Sync only specific user by username'
        )
    
    def handle(self, *args, **options):
        """
        Execute the command to sync user roles.
        
        Args:
            *args: Command line arguments
            **options: Command options
        """
        dry_run = options['dry_run']
        target_username = options.get('user')
        
        self.stdout.write(self.style.SUCCESS('🔄 Starting user role synchronization...'))
        
        # Get users to process
        if target_username:
            try:
                users = [User.objects.get(username=target_username)]
                self.stdout.write(f"Processing single user: {target_username}")
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"User '{target_username}' not found")
                )
                return
        else:
            users = User.objects.all()
            self.stdout.write(f"Processing all {users.count()} users...")
        
        # Statistics
        stats = {
            'total': users.count(),
            'updated': 0,
            'restaurant_owners': 0,
            'managers': 0,
            'customers': 0,
            'errors': 0
        }
        
        # Get groups
        restaurant_group = Group.objects.filter(name='Restaurant Owner').first()
        manager_group = Group.objects.filter(name='Manager').first()
        
        for user in users:
            try:
                # Get or create user profile
                profile, created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={'full_name': user.username, 'role': 'customer'}
                )
                
                if created:
                    self.stdout.write(f"Created profile for user: {user.username}")
                
                # Determine role based on group membership
                new_role = 'customer'  # Default role
                
                if user.is_superuser:
                    new_role = 'admin'
                elif manager_group and user.groups.filter(id=manager_group.id).exists():
                    new_role = 'manager'
                elif restaurant_group and user.groups.filter(id=restaurant_group.id).exists():
                    new_role = 'restaurant_owner'
                
                # Update role if needed
                if profile.role != new_role:
                    if dry_run:
                        self.stdout.write(
                            f"Would update {user.username}: {profile.role} -> {new_role}"
                        )
                    else:
                        old_role = profile.role
                        profile.role = new_role
                        profile.save(update_fields=['role'])
                        
                        # Also ensure proper group membership via utility function
                        set_user_role(user, new_role)
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Updated {user.username}: {old_role} -> {new_role}"
                            )
                        )
                        stats['updated'] += 1
                
                # Update statistics
                if new_role == 'restaurant_owner':
                    stats['restaurant_owners'] += 1
                elif new_role == 'manager':
                    stats['managers'] += 1
                else:
                    stats['customers'] += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing user {user.username}: {str(e)}")
                )
                stats['errors'] += 1
        
        # Display results
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("✅ Role synchronization completed!"))
        self.stdout.write(f"Total users processed: {stats['total']}")
        if not dry_run:
            self.stdout.write(f"Users updated: {stats['updated']}")
        self.stdout.write(f"Restaurant Owners: {stats['restaurant_owners']}")
        self.stdout.write(f"Managers: {stats['managers']}")
        self.stdout.write(f"Customers: {stats['customers']}")
        if stats['errors'] > 0:
            self.stdout.write(self.style.ERROR(f"Errors: {stats['errors']}"))
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING("\n🔍 This was a dry run. Use --no-dry-run to apply changes.")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("\n🎉 All user roles have been synchronized successfully!")
            )
