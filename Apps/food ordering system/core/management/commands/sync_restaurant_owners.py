"""
Django management command to sync restaurant owner status in database.

This command ensures that:
- Users with approved restaurants are added to the Restaurant Owner group
- Users without restaurants are removed from the Restaurant Owner group
- Group membership accurately reflects actual restaurant ownership

Usage:
    python manage.py sync_restaurant_owners
    python manage.py sync_restaurant_owners --verbose
    python manage.py sync_restaurant_owners --dry-run
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from core.utils.user_roles import sync_restaurant_owner_groups, get_user_statistics


class Command(BaseCommand):
    """
    Management command to synchronize restaurant owner group membership.
    
    This command updates the Restaurant Owner group to match actual
    restaurant ownership in the database, ensuring consistency between
    user permissions and restaurant data.
    """
    
    help = 'Sync restaurant owner group membership with actual restaurant ownership'
    
    def add_arguments(self, parser):
        """
        Add command line arguments.
        
        Args:
            parser: Django argument parser
        """
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output of the sync operation',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making actual changes',
        )
    
    def handle(self, *args, **options):
        """
        Handle the command execution.
        
        Executes the restaurant owner sync operation and displays
        results based on the verbosity level.
        
        Args:
            *args: Additional positional arguments
            **options: Command line options
        """
        self.stdout.write(
            self.style.SUCCESS('🍽️  Starting restaurant owner status sync...')
        )
        
        # Show current statistics before sync
        if options['verbose']:
            self.stdout.write('\n' + self.style.WARNING('Current database status:'))
            stats = get_user_statistics()
            for key, value in stats.items():
                self.stdout.write(f'  {key.replace("_", " ").title()}: {value}')
            self.stdout.write('')
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('🔍 DRY RUN MODE - No changes will be made')
            )
            # For dry run, we would need to implement a preview function
            # For now, just show current status
            return
        
        try:
            # Execute the sync operation
            stats = sync_restaurant_owner_groups()
            
            # Display results
            self.stdout.write('\n' + self.style.SUCCESS('✅ Sync completed successfully!'))
            self.stdout.write(f'📊 Results:')
            self.stdout.write(f'  • Group created: {"Yes" if stats["group_created"] else "Already existed"}')
            self.stdout.write(f'  • Users added to Restaurant Owner group: {stats["added"]}')
            self.stdout.write(f'  • Users removed from Restaurant Owner group: {stats["removed"]}')
            self.stdout.write(f'  • Total restaurant owners: {stats["total_restaurant_owners"]}')
            
            # Show updated statistics if verbose
            if options['verbose']:
                self.stdout.write('\n' + self.style.WARNING('Updated database status:'))
                new_stats = get_user_statistics()
                for key, value in new_stats.items():
                    self.stdout.write(f'  {key.replace("_", " ").title()}: {value}')
            
            # Show warnings if there were significant changes
            if stats['added'] > 0 or stats['removed'] > 0:
                self.stdout.write('\n' + self.style.WARNING(
                    '⚠️  Group membership was updated. '
                    'Users may need to log out and log back in to see permission changes.'
                ))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error during sync: {str(e)}')
            )
            raise
        
        self.stdout.write(
            self.style.SUCCESS('\n🎉 Restaurant owner status sync completed!')
        )
