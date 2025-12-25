#!/usr/bin/env python3
"""
Quick check for tables that need QR codes
"""

import os
import sys
import django

# Add project path
sys.path.append(r'd:\Project\Python\Apps\food ordering system')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

from restaurant.models import RestaurantTable, Restaurant

def check_tables():
    """Check tables and QR code status"""
    print("🔍 Checking tables and QR codes...")
    
    try:
        # Get all restaurants
        restaurants = Restaurant.objects.all()
        print(f"📊 Total restaurants: {restaurants.count()}")
        
        for restaurant in restaurants:
            print(f"\n🏪 Restaurant: {restaurant.name}")
            
            # Get all tables for this restaurant
            all_tables = RestaurantTable.objects.filter(restaurant=restaurant)
            print(f"   Total tables: {all_tables.count()}")
            
            # Tables with QR codes
            tables_with_qr = all_tables.exclude(qr_code__isnull=True).exclude(qr_code='')
            print(f"   Tables WITH QR codes: {tables_with_qr.count()}")
            
            # Tables without QR codes
            tables_without_qr = all_tables.filter(
                qr_code__isnull=True
            ) | all_tables.filter(qr_code='')
            print(f"   Tables WITHOUT QR codes: {tables_without_qr.count()}")
            
            if tables_without_qr.exists():
                print("   Tables needing QR codes:")
                for table in tables_without_qr:
                    print(f"     - Table {table.table_number} (ID: {table.id})")
            
            if all_tables.count() == 0:
                print("   ⚠️ No tables found for this restaurant")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_tables()
