#!/usr/bin/env python
"""
Fix database schema by adding missing guest_email and guest_phone columns
to the orders_order table.
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering_system.settings')

# Initialize Django
django.setup()

from django.db import connection

def add_missing_columns():
    """Add missing guest_email and guest_phone columns to orders_order table"""
    
    with connection.cursor() as cursor:
        try:
            # Check if guest_email column exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'orders_order' AND column_name = 'guest_email'
            """)
            guest_email_exists = cursor.fetchone()
            
            # Check if guest_phone column exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'orders_order' AND column_name = 'guest_phone'
            """)
            guest_phone_exists = cursor.fetchone()
            
            # Add guest_email column if it doesn't exist
            if not guest_email_exists:
                print("Adding guest_email column...")
                cursor.execute("""
                    ALTER TABLE orders_order 
                    ADD COLUMN guest_email VARCHAR(254) NULL
                """)
                print("✅ guest_email column added successfully")
            else:
                print("✅ guest_email column already exists")
            
            # Add guest_phone column if it doesn't exist
            if not guest_phone_exists:
                print("Adding guest_phone column...")
                cursor.execute("""
                    ALTER TABLE orders_order 
                    ADD COLUMN guest_phone VARCHAR(15) NULL
                """)
                print("✅ guest_phone column added successfully")
            else:
                print("✅ guest_phone column already exists")
            
            # Commit the changes
            connection.commit()
            print("\n🎉 Database schema fixed successfully!")
            
        except Exception as e:
            print(f"❌ Error fixing database schema: {e}")
            connection.rollback()
            return False
    
    return True

if __name__ == "__main__":
    print("🔧 Fixing database schema for missing guest columns...")
    success = add_missing_columns()
    if success:
        print("\n✅ Database fix completed. The dashboard should now work correctly.")
    else:
        print("\n❌ Database fix failed. Please check the error above.")
        sys.exit(1)
