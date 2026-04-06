"""
Custom management command to list all installed apps and their paths.
This helps diagnose issues with Django not finding installed apps.
"""
from django.core.management.base import BaseCommand
from django.apps import apps

class Command(BaseCommand):
    help = 'List all installed apps and their paths'

    def handle(self, *args, **options):
        """List all installed apps and their paths."""
        self.stdout.write("\n=== Installed Apps ===\n")
        for app_config in apps.get_app_configs():
            self.stdout.write(f"App: {app_config.name}")
            self.stdout.write(f"  Path: {app_config.path}")
            self.stdout.write(f"  Label: {app_config.label}")
            self.stdout.write(f"  Module: {app_config.module.__name__}")
            self.stdout.write("")
        
        self.stdout.write("\n=== Checking for rewards app ===")
        try:
            rewards_config = apps.get_app_config('rewards')
            self.stdout.write(self.style.SUCCESS("✓ Rewards app found!"))
            self.stdout.write(f"  Path: {rewards_config.path}")
            self.stdout.write(f"  Module: {rewards_config.module.__name__}")
        except LookupError:
            self.stdout.write(self.style.ERROR("✗ Rewards app not found in installed apps!"))
            
            # Try to import the app directly
            self.stdout.write("\nAttempting to import rewards app directly...")
            try:
                import rewards
                self.stdout.write(self.style.SUCCESS(f"✓ Successfully imported rewards app from: {rewards.__file__}"))
            except ImportError as e:
                self.stdout.write(self.style.ERROR(f"✗ Failed to import rewards app: {e}"))
        
        self.stdout.write("\n=== Checking Python path ===")
        import sys
        for path in sys.path:
            self.stdout.write(f"  {path}")
        
        self.stdout.write("\n=== Checking for rewards in Python path ===")
        import os
        for path in sys.path:
            rewards_path = os.path.join(path, 'rewards')
            if os.path.exists(rewards_path):
                self.stdout.write(f"  Found rewards at: {rewards_path}")
                if os.path.isfile(os.path.join(rewards_path, 'apps.py')):
                    self.stdout.write(self.style.SUCCESS("    ✓ Found apps.py in rewards directory"))
                if os.path.isfile(os.path.join(rewards_path, '__init__.py')):
                    self.stdout.write(self.style.SUCCESS("    ✓ Found __init__.py in rewards directory"))
