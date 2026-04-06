#!/usr/bin/env python
"""
Script to check and fix destinations-related tables in the database.
This script will:
1. Check if required tables exist
2. Create missing tables with proper schema
3. Fix any schema mismatches
4. Ensure all required columns and constraints are present
"""
import os
import sys
import django
from django.db import connection, transaction
from django.db.utils import ProgrammingError, DataError
from django.conf import settings

def setup_django():
    """Setup Django environment."""
    # Add the project root to the Python path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(project_root)
    
    # Set the Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guides.settings')
    
    # Setup Django
    django.setup()

def execute_sql(sql, params=None):
    """Execute raw SQL and return results."""
    with connection.cursor() as cursor:
        try:
            cursor.execute(sql, params or [])
            if cursor.description:
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            return []
        except (ProgrammingError, DataError) as e:
            print(f"Error executing SQL: {e}")
            return None

def table_exists(table_name):
    """Check if a table exists in the database."""
    sql = """
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE  table_schema = 'public' 
        AND    table_name   = %s
    );
    """
    result = execute_sql(sql, [table_name])
    return result and result[0].get('exists', False) if result else False

def column_exists(table_name, column_name):
    """Check if a column exists in a table."""
    sql = """
    SELECT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE  table_schema = 'public' 
        AND    table_name   = %s
        AND    column_name  = %s
    );
    """
    result = execute_sql(sql, [table_name, column_name])
    return result and result[0].get('exists', False) if result else False

def create_destinations_tables():
    """Create destinations-related tables if they don't exist."""
    tables = {
        'destinations_region': """
        CREATE TABLE IF NOT EXISTS destinations_region (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            slug VARCHAR(120) UNIQUE NOT NULL,
            description TEXT,
            country VARCHAR(100),
            is_active BOOLEAN NOT NULL DEFAULT true,
            is_featured BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """,
        'destinations_destination': """
        CREATE TABLE IF NOT EXISTS destinations_destination (
            id SERIAL PRIMARY KEY,
            region_id INTEGER NOT NULL REFERENCES destinations_region(id) ON DELETE CASCADE,
            name VARCHAR(100) NOT NULL,
            slug VARCHAR(120) UNIQUE NOT NULL,
            short_description VARCHAR(255),
            description TEXT,
            latitude DECIMAL(10, 6),
            longitude DECIMAL(10, 6),
            city VARCHAR(100),
            country VARCHAR(100),
            is_active BOOLEAN NOT NULL DEFAULT true,
            is_featured BOOLEAN NOT NULL DEFAULT false,
            price DECIMAL(10, 2),
            rating DECIMAL(3, 1),
            views INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """,
        'destinations_destinationimage': """
        CREATE TABLE IF NOT EXISTS destinations_destinationimage (
            id SERIAL PRIMARY KEY,
            destination_id INTEGER NOT NULL REFERENCES destinations_destination(id) ON DELETE CASCADE,
            image VARCHAR(100) NOT NULL,
            alt_text VARCHAR(255),
            is_primary BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """,
        'destinations_season': """
        CREATE TABLE IF NOT EXISTS destinations_season (
            id SERIAL PRIMARY KEY,
            destination_id INTEGER NOT NULL REFERENCES destinations_destination(id) ON DELETE CASCADE,
            name VARCHAR(100) NOT NULL,
            start_month INTEGER NOT NULL CHECK (start_month >= 1 AND start_month <= 12),
            end_month INTEGER NOT NULL CHECK (end_month >= 1 AND end_month <= 12),
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK (start_month <= end_month)
        );
        """,
        'destinations_attraction': """
        CREATE TABLE IF NOT EXISTS destinations_attraction (
            id SERIAL PRIMARY KEY,
            destination_id INTEGER NOT NULL REFERENCES destinations_destination(id) ON DELETE CASCADE,
            name VARCHAR(100) NOT NULL,
            slug VARCHAR(120) UNIQUE NOT NULL,
            description TEXT,
            category VARCHAR(50),
            address TEXT,
            city VARCHAR(100),
            country VARCHAR(100),
            latitude DECIMAL(10, 6),
            longitude DECIMAL(10, 6),
            is_featured BOOLEAN NOT NULL DEFAULT false,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    }

    # Create tables
    for table_name, create_sql in tables.items():
        if not table_exists(table_name):
            print(f"Creating table: {table_name}")
            execute_sql(create_sql)
        else:
            print(f"Table already exists: {table_name}")

def fix_columns():
    """Fix any column issues in the destinations tables."""
    # Check and fix columns for each table
    tables_columns = {
        'destinations_region': [
            ('is_active', 'BOOLEAN', 'DEFAULT true'),
            ('is_featured', 'BOOLEAN', 'DEFAULT false'),
            ('created_at', 'TIMESTAMP WITH TIME ZONE', 'DEFAULT CURRENT_TIMESTAMP'),
            ('updated_at', 'TIMESTAMP WITH TIME ZONE', 'DEFAULT CURRENT_TIMESTAMP')
        ],
        'destinations_destination': [
            ('is_active', 'BOOLEAN', 'DEFAULT true'),
            ('is_featured', 'BOOLEAN', 'DEFAULT false'),
            ('views', 'INTEGER', 'DEFAULT 0'),
            ('created_at', 'TIMESTAMP WITH TIME ZONE', 'DEFAULT CURRENT_TIMESTAMP'),
            ('updated_at', 'TIMESTAMP WITH TIME ZONE', 'DEFAULT CURRENT_TIMESTAMP')
        ],
        'destinations_attraction': [
            ('is_active', 'BOOLEAN', 'DEFAULT true'),
            ('is_featured', 'BOOLEAN', 'DEFAULT false'),
            ('created_at', 'TIMESTAMP WITH TIME ZONE', 'DEFAULT CURRENT_TIMESTAMP'),
            ('updated_at', 'TIMESTAMP WITH TIME ZONE', 'DEFAULT CURRENT_TIMESTAMP')
        ]
    }

    for table_name, columns in tables_columns.items():
        if not table_exists(table_name):
            print(f"Table {table_name} does not exist. Skipping column checks.")
            continue
            
        for column_name, data_type, default in columns:
            if not column_exists(table_name, column_name):
                print(f"Adding column {column_name} to {table_name}")
                sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {data_type} {default};"
                execute_sql(sql)

def create_indexes():
    """Create necessary indexes for better performance."""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_destination_region ON destinations_destination(region_id);",
        "CREATE INDEX IF NOT EXISTS idx_destination_active ON destinations_destination(is_active) WHERE is_active = true;",
        "CREATE INDEX IF NOT EXISTS idx_destination_featured ON destinations_destination(is_featured) WHERE is_featured = true;",
        "CREATE INDEX IF NOT EXISTS idx_attraction_destination ON destinations_attraction(destination_id);",
        "CREATE INDEX IF NOT EXISTS idx_attraction_active ON destinations_attraction(is_active) WHERE is_active = true;",
        "CREATE INDEX IF NOT EXISTS idx_attraction_featured ON destinations_attraction(is_featured) WHERE is_featured = true;"
    ]
    
    for index_sql in indexes:
        try:
            execute_sql(index_sql)
            print(f"Created index: {index_sql.split(' ON ')[1].split('(')[0]}")
        except Exception as e:
            print(f"Error creating index: {e}")

def create_triggers():
    """Create triggers for updated_at timestamps."""
    # Create the update_updated_at_column function if it doesn't exist
    execute_sql("""
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    """)
    
    # Create triggers for each table that needs it
    tables = ['destinations_region', 'destinations_destination', 'destinations_attraction', 
              'destinations_destinationimage', 'destinations_season']
    
    for table in tables:
        if not table_exists(table):
            continue
            
        trigger_name = f'trigger_update_{table}_updated_at'
        
        # Drop existing trigger if it exists
        execute_sql(f"""
        DROP TRIGGER IF EXISTS {trigger_name} ON {table};
        """)
        
        # Create new trigger
        execute_sql(f"""
        CREATE TRIGGER {trigger_name}
        BEFORE UPDATE ON {table}
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
        """)
        print(f"Created/updated trigger for {table}")

def main():
    """Main function to run the script."""
    print("=== Starting destinations tables check and fix ===")
    
    try:
        # Create tables if they don't exist
        print("\n=== Checking/Creating tables ===")
        create_destinations_tables()
        
        # Fix any column issues
        print("\n=== Fixing columns ===")
        fix_columns()
        
        # Create indexes
        print("\n=== Creating indexes ===")
        create_indexes()
        
        # Create triggers
        print("\n=== Creating/Updating triggers ===")
        create_triggers()
        
        print("\n=== Destinations tables check and fix completed successfully ===")
        
    except Exception as e:
        print(f"\nError: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    setup_django()
    sys.exit(main())
