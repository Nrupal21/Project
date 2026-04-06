"""
Script to check existing database tables and structure.

This script connects to the database and lists all existing tables,
helping to identify what tables already exist and what needs to be created.

Author: TravelGuide Development Team
Date: July 31, 2025
"""
import os
import sys
import django
from pathlib import Path

# Add the project root to the Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guides.settings')
django.setup()

# Import the necessary modules after Django is set up
from django.db import connection
from django.conf import settings

def check_database_connection():
    """
    Check if the database connection is working properly.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        connection.ensure_connection()
        print("✓ Database connection successful")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def list_all_tables():
    """
    List all tables in the database.
    
    This function queries the database's information schema to get a list
    of all tables in the public schema.
    """
    print("\n=== Existing Database Tables ===\n")
    
    with connection.cursor() as cursor:
        cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in the database.")
        else:
            for i, (table,) in enumerate(tables, 1):
                print(f"{i}. {table}")
                
            print(f"\nTotal tables: {len(tables)}")

def check_rewards_tables():
    """
    Check if rewards-related tables exist in the database.
    
    This function specifically checks for the rewards app tables and
    provides information about their existence.
    """
    print("\n=== Checking for Rewards Tables ===\n")
    
    rewards_tables = [
        'rewards_rewardtier',
        'rewards_rewardpoints',
        'rewards_rewardredemption'
    ]
    
    with connection.cursor() as cursor:
        for table in rewards_tables:
            cursor.execute(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name = '{table}'
            );
            """)
            exists = cursor.fetchone()[0]
            
            if exists:
                print(f"✓ Table '{table}' exists")
                
                # Check column structure for existing tables
                cursor.execute(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = '{table}'
                ORDER BY ordinal_position;
                """)
                columns = cursor.fetchall()
                
                print(f"  Columns in '{table}':")
                for col_name, col_type, nullable in columns:
                    nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
                    print(f"    - {col_name} ({col_type}, {nullable_str})")
            else:
                print(f"✗ Table '{table}' does not exist")

def check_auth_tables():
    """
    Check if Django authentication tables exist in the database.
    
    This function checks for the core Django auth tables that are
    required for the rewards system to function properly.
    """
    print("\n=== Checking for Django Auth Tables ===\n")
    
    auth_tables = [
        'auth_user',
        'auth_group',
        'auth_permission',
        'django_content_type'
    ]
    
    with connection.cursor() as cursor:
        for table in auth_tables:
            cursor.execute(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name = '{table}'
            );
            """)
            exists = cursor.fetchone()[0]
            
            if exists:
                print(f"✓ Table '{table}' exists")
            else:
                print(f"✗ Table '{table}' does not exist")

def main():
    """
    Main function to run the database check.
    
    This function coordinates the database connection check and
    the listing of tables.
    """
    print("\n" + "=" * 80)
    print("TRAVELGUIDE DATABASE STRUCTURE CHECK".center(80))
    print("=" * 80 + "\n")
    
    if not check_database_connection():
        print("\n✗ Cannot proceed due to database connection failure.")
        return
    
    list_all_tables()
    check_auth_tables()
    check_rewards_tables()
    
    print("\n" + "=" * 80)
    print("DATABASE CHECK COMPLETE".center(80))
    print("=" * 80)

if __name__ == "__main__":
    main()
