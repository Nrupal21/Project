"""
Script to check Django app discovery and Python path.
This helps diagnose issues with Django not finding installed apps.
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
PROJECT_ROOT = str(Path(__file__).resolve().parent)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guides.settings')

import django
django.setup()

from django.apps import apps

def check_apps():
    """Check and print all installed apps and their configurations."""
    print("\n=== Installed Apps ===")
    for app_config in apps.get_app_configs():
        print(f"\nApp: {app_config.name}")
        print(f"  Path: {app_config.path}")
        print(f"  Label: {app_config.label}")
        print(f"  Module: {app_config.module.__name__}")
    
    print("\n=== Python Path ===")
    for path in sys.path:
        print(path)

if __name__ == "__main__":
    check_apps()
