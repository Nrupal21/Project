#!/usr/bin/env python
"""
Script to reset the database by dropping and recreating all tables.
This will delete all data in the database!
"""
import os
import sys
import django
from django.conf import settings
from django.core.management import call_command

def reset_database():
    """Reset the database by dropping and recreating all tables."""
    print("\n=== Resetting Database ===")
    
    # Drop and recreate the database
    print("Dropping and recreating the database...")
    call_command('reset_db', '--noinput')
    
    # Run migrations
    print("\nRunning migrations...")
    call_command('migrate')
    
    # Create superuser
    print("\nCreating superuser...")
    call_command('createsuperuser', '--noinput', '--username=admin', '--email=admin@example.com')
    
    # Load initial data if available
    print("\nLoading initial data...")
    try:
        call_command('loaddata', 'initial_data.json')
    except Exception as e:
        print(f"Warning: Could not load initial data: {e}")
    
    print("\n=== Database reset complete ===")

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guides.settings')
    django.setup()
    reset_database()
