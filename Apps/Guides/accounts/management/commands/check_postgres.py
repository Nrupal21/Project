"""
Management command to check PostgreSQL database connection and status.

This command verifies the PostgreSQL connection, checks database structure,
and provides information about tables, indexes, and database statistics.
"""
import os
import sys
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, connection, DatabaseError
from django.conf import settings
from accounts.db_indexes import get_table_stats, ensure_db_indexes

class Command(BaseCommand):
    """
    Command to check PostgreSQL database connection and status.
    
    This command performs several checks on the PostgreSQL database:
    1. Verifies connection to the database
    2. Checks if all required tables exist
    3. Verifies critical indexes are present
    4. Provides statistics about table sizes and row counts
    """
    help = 'Check PostgreSQL database connection and status'
    
    def add_arguments(self, parser):
        """
        Add command line arguments.
        
        Args:
            parser: ArgumentParser instance for adding command arguments
            
        This function defines the command-line options available when
        running the check_postgres command.
        """
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed information about tables and indexes'
        )
        parser.add_argument(
            '--check-indexes',
            action='store_true',
            help='Check if all expected indexes exist'
        )
    
    def handle(self, *args, **options):
        """
        Handle the command execution for checking PostgreSQL.
        
        Args:
            options: Dictionary containing command line arguments
            
        Returns:
            None
            
        This function performs the database checks and outputs the results
        to the console, highlighting any issues that need attention.
        """
        self.stdout.write('Checking PostgreSQL database connection and status...\n')
        
        # Check database settings
        self._check_settings()
        
        # Check database connection
        try:
            self._check_connection()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Connection failed: {str(e)}'))
            return
            
        # Check tables
        self._check_tables()
        
        # Check indexes if requested
        if options['check_indexes']:
            self._check_indexes()
        
        # Show detailed stats if requested
        if options['detailed']:
            self._show_detailed_stats()
            
        self.stdout.write(self.style.SUCCESS('\nPostgreSQL database check completed!'))
    
    def _check_settings(self):
        """
        Check PostgreSQL database settings.
        
        This function verifies that the database settings in Django configuration
        are properly set up for PostgreSQL connection.
        """
        db_settings = settings.DATABASES.get('default', {})
        
        self.stdout.write('Database settings:')
        self.stdout.write(f"  Engine: {db_settings.get('ENGINE', 'Not set')}")
        
        if db_settings.get('ENGINE') != 'django.db.backends.postgresql':
            self.stdout.write(self.style.WARNING('  Warning: Database engine is not PostgreSQL'))
            
        self.stdout.write(f"  Name: {db_settings.get('NAME', 'Not set')}")
        self.stdout.write(f"  Host: {db_settings.get('HOST', 'localhost')}")
        self.stdout.write(f"  Port: {db_settings.get('PORT', '5432')}")
        self.stdout.write(f"  User: {db_settings.get('USER', 'Not set')}")
        
        # Check if password is set (don't print the actual password)
        if 'PASSWORD' in db_settings and db_settings['PASSWORD']:
            self.stdout.write('  Password: [Set]')
        else:
            self.stdout.write(self.style.WARNING('  Password: [Not set]'))
        
        self.stdout.write('')
    
    def _check_connection(self):
        """
        Check database connection.
        
        This function attempts to connect to the database and verify
        that the connection is working properly.
        
        Raises:
            CommandError: If connection fails
        """
        self.stdout.write('Testing database connection...')
        
        try:
            # Check connection and get PostgreSQL version
            with connection.cursor() as cursor:
                cursor.execute('SELECT version();')
                version = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f'  Connection successful!'))
                self.stdout.write(f'  PostgreSQL version: {version}')
                
                # Check if connected as superuser
                cursor.execute('SELECT current_setting(\'is_superuser\');')
                is_superuser = cursor.fetchone()[0]
                if is_superuser == 'on':
                    self.stdout.write('  Connected as: Superuser')
                else:
                    self.stdout.write('  Connected as: Regular user')
                    
        except DatabaseError as e:
            raise CommandError(f'Database connection failed: {str(e)}')
        
        self.stdout.write('')
    
    def _check_tables(self):
        """
        Check if all required tables exist.
        
        This function queries the database to get a list of tables
        and verifies that all essential tables for the application exist.
        """
        self.stdout.write('Checking database tables...')
        
        # List of required tables
        required_tables = [
            'django_site', 
            'django_session',
            'django_migrations', 
            'django_content_type',
            'accounts_customuser',
            'accounts_userprofile',
            'auth_permission',
            'auth_group'
        ]
        
        try:
            with connection.cursor() as cursor:
                # Get all table names in the public schema
                cursor.execute("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public'
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                # Check for missing tables
                missing_tables = [table for table in required_tables if table not in tables]
                
                if missing_tables:
                    self.stdout.write(self.style.WARNING('  Missing tables:'))
                    for table in missing_tables:
                        self.stdout.write(self.style.WARNING(f'    - {table}'))
                    self.stdout.write(self.style.WARNING('  Run migrations to create missing tables'))
                else:
                    self.stdout.write(self.style.SUCCESS('  All required tables exist'))
                    self.stdout.write(f'  Total tables found: {len(tables)}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Error checking tables: {str(e)}'))
        
        self.stdout.write('')
    
    def _check_indexes(self):
        """
        Check if all expected indexes exist.
        
        This function calls the ensure_db_indexes function to verify
        that all expected indexes are present in the database.
        """
        self.stdout.write('Checking database indexes...')
        
        try:
            if ensure_db_indexes():
                self.stdout.write(self.style.SUCCESS('  All expected indexes exist'))
            else:
                self.stdout.write(self.style.WARNING('  Some expected indexes are missing'))
                self.stdout.write(self.style.WARNING('  Run migrations to create missing indexes'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Error checking indexes: {str(e)}'))
        
        self.stdout.write('')
    
    def _show_detailed_stats(self):
        """
        Show detailed database statistics.
        
        This function displays detailed information about tables,
        including row counts and sizes, useful for database monitoring.
        """
        self.stdout.write('Gathering database statistics...')
        
        try:
            stats = get_table_stats()
            
            # Display table statistics
            self.stdout.write('\nTable statistics:')
            self.stdout.write('-' * 80)
            self.stdout.write(f'{"Table Name":<30} {"Rows":<10} {"Table Size":<15} {"Index Size":<15}')
            self.stdout.write('-' * 80)
            
            for table_name, table_stats in sorted(stats.items()):
                row_count = table_stats.get('row_count', 'N/A')
                table_size = table_stats.get('table_size', 'N/A')
                index_size = table_stats.get('index_size', 'N/A')
                
                self.stdout.write(f'{table_name:<30} {row_count:<10} {table_size:<15} {index_size:<15}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Error getting table statistics: {str(e)}'))
        
        self.stdout.write('')
