"""
Management command to create a superuser with a specific role.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    """
    Command to create a superuser with a specific role.
    """
    help = 'Create a superuser with the specified role'

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument('--username', help="The username for the superuser")
        parser.add_argument('--email', help="The email for the superuser")
        parser.add_argument('--password', help="The password for the superuser")
        parser.add_argument('--noinput', '--no-input', action='store_false', 
                          dest='interactive',
                          help='Tells Django to NOT prompt the user for input of any kind.',)

    def handle(self, *args, **options):
        """Handle the command execution."""
        username = options.get('username')
        email = options.get('email')
        password = options.get('password')
        interactive = options.get('interactive')

        # Get user input if not provided
        if interactive:
            if not username:
                username = input('Username: ')
            if not email:
                email = input('Email: ')
            if not password:
                from getpass import getpass
                password = getpass('Password: ')
                password2 = getpass('Password (again): ')
                if password != password2:
                    self.stderr.write("Error: Your passwords didn't match.")
                    return
        elif not (username and email and password):
            self.stderr.write("Error: --username, --email, and --password are required with --noinput")
            return

        # Create the superuser
        try:
            with transaction.atomic():
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                # The role is already set to ADMIN in create_superuser method
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created superuser with username: {username} and role: {user.role}')
                )
        except Exception as e:
            self.stderr.write(f'Error creating superuser: {e}')
