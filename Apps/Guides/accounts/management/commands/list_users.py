"""
Management command to list all users with their roles.
This version is optimized for MongoDB.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from bson.objectid import ObjectId

User = get_user_model()

class Command(BaseCommand):
    """
    Command to list all users with their roles.
    This version is optimized for MongoDB.
    """
    help = 'List all users with their roles (MongoDB version)'

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--active-only',
            action='store_true',
            dest='active_only',
            help='Show only active users',
        )
        parser.add_argument(
            '--role',
            dest='role',
            help='Filter users by role',
            choices=dict(User.UserRole.choices).keys(),
        )
        parser.add_argument(
            '--show-passwords',
            action='store_true',
            dest='show_passwords',
            help='Show password hashes (admin only)',
        )

    def handle(self, *args, **options):
        """Handle the command execution."""
        # Build the query
        query = {}
        
        if options['active_only']:
            query['is_active'] = True
            
        if options['role']:
            query['role'] = options['role']
        
        # Get users from MongoDB
        users = User.objects.filter(**query).order_by('date_joined')
        
        # Prepare the output
        self.stdout.write(self.style.MIGRATE_HEADING('List of users:'))
        self.stdout.write('-' * 100)
        
        # Table header
        headers = [
            ('ID', 24),
            ('Username', 20),
            ('Email', 30),
            ('Role', 15),
            ('Active', 8),
            ('Last Login', 20),
        ]
        
        if options['show_passwords']:
            headers.append(('Password', 30))
        
        # Print header
        header_line = ' '.join(f"{{:<{width}}}".format(text) for text, width in headers)
        self.stdout.write(header_line)
        self.stdout.write('-' * 100)
        
        # Print users
        for user in users:
            last_login = user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never'
            
            # Format user data
            user_data = [
                (str(user._id), 24),
                (user.username[:18] + '..' if len(user.username) > 20 else user.username, 20),
                (user.email[:28] + '..' if len(user.email) > 30 else user.email, 30),
                (user.get_role_display(), 15),
                ('Yes' if user.is_active else 'No', 8),
                (last_login, 20),
            ]
            
            if options['show_passwords']:
                user_data.append((user.password[:28] + '..' if user.password else 'None', 30))
            
            # Print user row
            user_line = ' '.join(f"{{:<{width}}}".format(text) for text, width in user_data)
            self.stdout.write(user_line)
        
        # Print summary
        self.stdout.write('-' * 100)
        self.stdout.write(f'Total users: {users.count()}')
        
        # Show role distribution if not filtered by role
        if not options['role']:
            self.stdout.write('\nRole distribution:')
            roles = User.objects.values_list('role', flat=True).distinct()
            for role in roles:
                count = User.objects.filter(role=role).count()
                self.stdout.write(f'  - {role}: {count} users')
