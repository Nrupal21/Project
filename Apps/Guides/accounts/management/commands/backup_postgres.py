"""
Management command to create a backup of the PostgreSQL database.

This command creates a backup of the PostgreSQL database using pg_dump utility.
It supports various options for customizing the backup process including
compression and output directory specification.
"""
import os
import subprocess
import datetime
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

class Command(BaseCommand):
    """
    Command to create a backup of the PostgreSQL database.
    
    This command uses pg_dump to create a SQL dump or custom format backup
    of the configured PostgreSQL database. It reads database connection
    details from Django settings.
    """
    help = 'Create a backup of the PostgreSQL database'
    
    def add_arguments(self, parser):
        """
        Add command line arguments for the backup command.
        
        Args:
            parser: ArgumentParser instance for adding command arguments
            
        This function defines what command-line options are available when
        running the backup_postgres command.
        """
        parser.add_argument(
            '--output-dir',
            dest='output_dir',
            default='./backups',
            help='Directory to store the backup (default: ./backups)'
        )
        parser.add_argument(
            '--format',
            choices=['plain', 'custom', 'directory', 'tar'],
            default='custom',
            help='Output format (default: custom)'
        )
        parser.add_argument(
            '--compress',
            choices=['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'],
            default='5',
            help='Compression level (0-9, default: 5)'
        )
        parser.add_argument(
            '--no-owner',
            action='store_true',
            help='Do not output commands to set object ownership'
        )
        parser.add_argument(
            '--schema-only',
            action='store_true',
            help='Dump only the schema, no data'
        )
    
    def handle(self, *args, **options):
        """
        Handle the command execution for PostgreSQL backup.
        
        Args:
            options: Dictionary containing command line arguments
            
        Returns:
            None
            
        This function reads database settings from Django configuration,
        builds and executes the pg_dump command with appropriate parameters,
        and handles any errors that occur during the backup process.
        """
        # Get database settings from Django settings
        db_settings = settings.DATABASES['default']
        
        # Ensure required settings are available
        if db_settings['ENGINE'] != 'django.db.backends.postgresql':
            raise CommandError('This command only works with PostgreSQL databases')
        
        # Create output directory if it doesn't exist
        output_dir = Path(options['output_dir']).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        
        # Set file extension based on format
        format_extensions = {
            'plain': 'sql',
            'custom': 'dump',
            'directory': 'dir',
            'tar': 'tar'
        }
        ext = format_extensions[options['format']]
        
        # Create backup filename
        backup_name = f'postgres_backup_{timestamp}.{ext}'
        backup_path = output_dir / backup_name
        
        # Build the pg_dump command
        cmd = [
            'pg_dump',
            '--host', db_settings.get('HOST', 'localhost'),
            '--port', str(db_settings.get('PORT', '5432')),
            '--username', db_settings.get('USER', ''),
            '--format', options['format'][0],  # Use first letter as format code
            '--compress', options['compress'],
            '--file', str(backup_path),
        ]
        
        # Add optional arguments
        if options['no_owner']:
            cmd.append('--no-owner')
        
        if options['schema_only']:
            cmd.append('--schema-only')
        
        # Add database name
        cmd.append(db_settings.get('NAME', ''))
        
        self.stdout.write(f'Creating PostgreSQL backup in: {backup_path}')
        
        # Set PGPASSWORD environment variable for password authentication
        env = os.environ.copy()
        if 'PASSWORD' in db_settings and db_settings['PASSWORD']:
            env['PGPASSWORD'] = db_settings['PASSWORD']
        
        try:
            # Run the pg_dump command
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                env=env
            )
            
            self.stdout.write(self.style.SUCCESS('Backup completed successfully!'))
            
            # Display backup info
            backup_size = self._get_file_size(backup_path)
            self.stdout.write(f'Backup size: {self._format_size(backup_size)}')
            self.stdout.write(f'Backup location: {backup_path}')
            
        except subprocess.CalledProcessError as e:
            raise CommandError(f'Backup failed: {e.stderr}')
        except Exception as e:
            raise CommandError(f'Error during backup: {str(e)}')
    
    def _get_file_size(self, path):
        """
        Calculate the size of a file or directory in bytes.
        
        Args:
            path: Path to the file or directory to measure
            
        Returns:
            int: Size in bytes
            
        This function handles both regular files and directories
        for calculating the total backup size.
        """
        path = Path(path)
        
        if path.is_file():
            return path.stat().st_size
        elif path.is_dir():
            return sum(f.stat().st_size for f in path.glob('**/*') if f.is_file())
        else:
            return 0
    
    def _format_size(self, size_bytes):
        """
        Format size in bytes to a human-readable format.
        
        Args:
            size_bytes: Size in bytes to format
            
        Returns:
            str: Formatted size with appropriate unit
            
        This function converts raw byte sizes to human-readable formats
        such as KB, MB, GB with appropriate precision.
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f'{size_bytes:.2f} {unit}'
            size_bytes /= 1024.0
        return f'{size_bytes:.2f} PB'
