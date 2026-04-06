"""
Management command to create missing security tables.

This command creates the security_failedloginattempt table directly using Django's
connection.schema_editor() to ensure the table exists regardless of migration state.
"""

from django.core.management.base import BaseCommand
from django.db import connection
from security.models import FailedLoginAttempt


class Command(BaseCommand):
    """
    Management command to create missing security tables.
    
    This command creates the security_failedloginattempt table directly using Django's
    connection.schema_editor() to ensure the table exists regardless of migration state.
    """
    
    help = 'Creates missing security tables like security_failedloginattempt'

    def handle(self, *args, **options):
        """
        Execute the command to create missing security tables.
        
        Args:
            *args: Variable length argument list.
            **options: Arbitrary keyword arguments.
            
        Returns:
            None
        """
        self.stdout.write(self.style.SUCCESS('Creating missing security tables...'))
        
        # Create the security_failedloginattempt table
        with connection.schema_editor() as schema_editor:
            try:
                # Check if the table already exists
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT EXISTS (SELECT FROM information_schema.tables "
                        "WHERE table_schema = 'public' AND table_name = 'security_failedloginattempt')"
                    )
                    table_exists = cursor.fetchone()[0]
                
                if not table_exists:
                    self.stdout.write(self.style.WARNING('Table security_failedloginattempt does not exist. Creating...'))
                    schema_editor.create_model(FailedLoginAttempt)
                    self.stdout.write(self.style.SUCCESS('Successfully created security_failedloginattempt table'))
                else:
                    self.stdout.write(self.style.SUCCESS('Table security_failedloginattempt already exists'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating table: {e}'))
                
        self.stdout.write(self.style.SUCCESS('Done!'))
