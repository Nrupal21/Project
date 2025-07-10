"""
Management command to create a backup of the MongoDB database.
"""
import os
import json
import datetime
import subprocess
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

class Command(BaseCommand):
    """
    Command to create a backup of the MongoDB database.
    """
    help = 'Create a backup of the MongoDB database'
    
    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--output-dir',
            dest='output_dir',
            default='./backups',
            help='Directory to store the backup (default: ./backups)'
        )
        parser.add_argument(
            '--compress',
            action='store_true',
            help='Compress the backup using gzip'
        )
    
    def handle(self, *args, **options):
        """Handle the command execution."""
        # Check if MongoDB is configured
        if not hasattr(settings, 'MONGO_URI'):
            raise CommandError('MongoDB is not configured. Please set MONGO_URI in settings.')
        
        # Create output directory if it doesn't exist
        output_dir = Path(options['output_dir']).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'mongodb_backup_{timestamp}'
        backup_path = output_dir / backup_name
        
        # Build the mongodump command
        cmd = [
            'mongodump',
            '--uri', settings.MONGO_URI,
            '--out', str(backup_path),
        ]
        
        # Add compression if requested
        if options['compress']:
            cmd.append('--gzip')
        
        self.stdout.write(f'Creating MongoDB backup in: {backup_path}')
        
        try:
            # Run the mongodump command
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            
            self.stdout.write(self.style.SUCCESS('Backup completed successfully!'))
            self.stdout.write(result.stdout)
            
            # Display backup size
            backup_size = self._get_directory_size(backup_path)
            self.stdout.write(f'Backup size: {self._format_size(backup_size)}')
            
            # Show path to backup
            self.stdout.write(f'Backup location: {backup_path}')
            
        except subprocess.CalledProcessError as e:
            raise CommandError(f'Backup failed: {e.stderr}')
        except Exception as e:
            raise CommandError(f'Error during backup: {str(e)}')
    
    def _get_directory_size(self, path):
        """Calculate the total size of a directory in bytes."""
        total_size = 0
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # Skip if it's a symbolic link
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        return total_size
    
    def _format_size(self, size_bytes):
        """Format size in bytes to a human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f'{size_bytes:.2f} {unit}'
            size_bytes /= 1024.0
        return f'{size_bytes:.2f} PB'
