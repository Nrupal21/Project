"""
Management command to restore a MongoDB database from a backup.
"""
import os
import subprocess
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

class Command(BaseCommand):
    """
    Command to restore a MongoDB database from a backup.
    """
    help = 'Restore a MongoDB database from a backup'
    
    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            'backup_path',
            type=str,
            help='Path to the backup directory or file'
        )
        parser.add_argument(
            '--drop',
            action='store_true',
            help='Drop each collection before import'
        )
        parser.add_argument(
            '--noinput',
            '--no-input',
            action='store_true',
            help='Do not prompt for confirmation'
        )
    
    def handle(self, *args, **options):
        """Handle the command execution."""
        # Check if MongoDB is configured
        if not hasattr(settings, 'MONGO_URI'):
            raise CommandError('MongoDB is not configured. Please set MONGO_URI in settings.')
        
        backup_path = Path(options['backup_path']).resolve()
        
        # Check if backup exists
        if not backup_path.exists():
            raise CommandError(f'Backup not found: {backup_path}')
        
        # Check if it's a directory (for mongodump) or a file (for mongorestore with --archive)
        is_directory = backup_path.is_dir()
        
        # Confirm before proceeding
        if not options['noinput']:
            db_name = settings.MONGO_DB_NAME if hasattr(settings, 'MONGO_DB_NAME') else 'unknown'
            self.stdout.write(self.style.WARNING('WARNING: This will overwrite data in the database!'))
            self.stdout.write(f'Database: {db_name}')
            self.stdout.write(f'Backup: {backup_path}')
            
            confirm = input('Are you sure you want to proceed? (y/N): ')
            if confirm.lower() != 'y':
                self.stdout.write('Restore cancelled.')
                return
        
        # Build the mongorestore command
        cmd = ['mongorestore', '--uri', settings.MONGO_URI]
        
        # Add options based on backup type
        if is_directory:
            cmd.extend(['--dir', str(backup_path)])
        else:
            cmd.extend(['--archive=' + str(backup_path), '--gzip'])
        
        # Add drop option if specified
        if options['drop']:
            cmd.append('--drop')
        
        self.stdout.write(f'Restoring MongoDB from backup: {backup_path}')
        
        try:
            # Run the mongorestore command
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            
            self.stdout.write(self.style.SUCCESS('Restore completed successfully!'))
            self.stdout.write(result.stdout)
            
        except subprocess.CalledProcessError as e:
            raise CommandError(f'Restore failed: {e.stderr}')
        except Exception as e:
            raise CommandError(f'Error during restore: {str(e)}')
