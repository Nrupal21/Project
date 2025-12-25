#!/usr/bin/env python
"""
Backup script for existing data before encryption migration.
This script exports all sensitive data to a JSON file for verification.
"""

import os
import sys
import django
import json
from datetime import datetime

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

from customer.models import UserProfile
from restaurant.models import Restaurant, PendingRestaurant

def create_backup():
    """Create a comprehensive backup of existing data."""
    print('=== CREATING PRE-MIGRATION DATA BACKUP ===')
    
    backup_data = {
        'timestamp': datetime.now().isoformat(),
        'user_profiles': [],
        'restaurants': [],
        'pending_restaurants': []
    }
    
    # Export user profiles
    print('Exporting user profiles...')
    for profile in UserProfile.objects.all():
        backup_data['user_profiles'].append({
            'id': profile.id,
            'username': profile.user.username,
            'full_name': profile.full_name,
            'phone_number': profile.phone_number,
            'address': profile.address,
            'encrypted_fields': {
                'full_name_encrypted': profile._full_name_encrypted[:50] + '...' if profile._full_name_encrypted else None,
                'phone_encrypted': profile._phone_number_encrypted[:50] + '...' if profile._phone_number_encrypted else None,
                'address_encrypted': profile._address_encrypted[:50] + '...' if profile._address_encrypted else None,
            }
        })
    
    # Export restaurants
    print('Exporting restaurants...')
    for restaurant in Restaurant.objects.all():
        backup_data['restaurants'].append({
            'id': restaurant.id,
            'name': restaurant.name,
            'address': restaurant.address,
            'phone': restaurant.phone,
            'email': restaurant.email,
            'encrypted_fields': {
                'address_encrypted': restaurant._address_encrypted[:50] + '...' if restaurant._address_encrypted else None,
                'phone_encrypted': restaurant._phone_encrypted[:50] + '...' if restaurant._phone_encrypted else None,
                'email_encrypted': restaurant._email_encrypted[:50] + '...' if restaurant._email_encrypted else None,
            }
        })
    
    # Export pending restaurants
    print('Exporting pending restaurants...')
    for pending in PendingRestaurant.objects.all():
        backup_data['pending_restaurants'].append({
            'id': pending.id,
            'restaurant_name': pending.restaurant_name,
            'address': pending.address,
            'phone': pending.phone,
            'email': pending.email,
            'encrypted_fields': {
                'address_encrypted': pending._address_encrypted[:50] + '...' if pending._address_encrypted else None,
                'phone_encrypted': pending._phone_encrypted[:50] + '...' if pending._phone_encrypted else None,
                'email_encrypted': pending._email_encrypted[:50] + '...' if pending._email_encrypted else None,
            }
        })
    
    # Save backup to file
    backup_file = f'pre_encryption_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)
    
    print(f'✅ Backup saved to: {backup_file}')
    print(f'  User profiles: {len(backup_data["user_profiles"])}')
    print(f'  Restaurants: {len(backup_data["restaurants"])}')
    print(f'  Pending restaurants: {len(backup_data["pending_restaurants"])}')
    
    return backup_file

if __name__ == '__main__':
    backup_file = create_backup()
    print(f'\nBackup completed: {backup_file}')
    print('You can now proceed with encryption migrations.')
