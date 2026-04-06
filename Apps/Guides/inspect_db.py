"""
Database inspection script to examine table structures and relationships.

This script connects to the Django database and outputs information about
tables, columns, and relationships to help with debugging and development.
"""
import os
import sys
import django
from django.db import connection

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travelguide.settings')
django.setup()

def get_table_columns(table_name):
    """
    Get column information for a specific table.
    
    Args:
        table_name: Name of the table to inspect
        
    Returns:
        List of dictionaries with column information
    """
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT column_name, data_type, character_maximum_length, 
                   is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, [table_name])
        columns = [{
            'name': row[0],
            'type': row[1],
            'max_length': row[2],
            'nullable': row[3],
            'default': row[4]
        } for row in cursor.fetchall()]
    return columns

def get_all_tables():
    """
    Get a list of all tables in the database.
    
    Returns:
        List of table names
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
    return tables

def inspect_table(table_name):
    """
    Print detailed information about a specific table.
    
    Args:
        table_name: Name of the table to inspect
    """
    print(f"\n{'=' * 50}")
    print(f"TABLE: {table_name}")
    print(f"{'=' * 50}")
    
    columns = get_table_columns(table_name)
    print(f"\nCOLUMNS ({len(columns)}):")
    print(f"{'-' * 50}")
    for col in columns:
        nullable = "NULL" if col['nullable'] == "YES" else "NOT NULL"
        max_length = f"({col['max_length']})" if col['max_length'] else ""
        default = f" DEFAULT {col['default']}" if col['default'] else ""
        print(f"{col['name']}: {col['type']}{max_length} {nullable}{default}")
    
    # Get sample data
    with connection.cursor() as cursor:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM \"{table_name}\"")
            count = cursor.fetchone()[0]
            print(f"\nROW COUNT: {count}")
            
            if count > 0:
                cursor.execute(f"SELECT * FROM \"{table_name}\" LIMIT 5")
                sample_data = cursor.fetchall()
                if sample_data:
                    print(f"\nSAMPLE DATA (up to 5 rows):")
                    print(f"{'-' * 50}")
                    for row in sample_data:
                        print(row)
        except Exception as e:
            print(f"Error getting sample data: {e}")

def inspect_specific_tables(table_names):
    """
    Inspect specific tables by name.
    
    Args:
        table_names: List of table names to inspect
    """
    for table_name in table_names:
        inspect_table(table_name)

def main():
    """Main function to run the database inspection."""
    if len(sys.argv) > 1:
        # Inspect specific tables provided as arguments
        table_names = sys.argv[1:]
        inspect_specific_tables(table_names)
    else:
        # List all tables
        tables = get_all_tables()
        print(f"Found {len(tables)} tables in the database:")
        for i, table in enumerate(tables, 1):
            print(f"{i}. {table}")
        
        # Ask which tables to inspect
        print("\nEnter table numbers to inspect (comma-separated) or 'all' for all tables:")
        choice = input("> ")
        
        if choice.lower() == 'all':
            inspect_specific_tables(tables)
        else:
            try:
                indices = [int(idx.strip()) - 1 for idx in choice.split(',')]
                selected_tables = [tables[idx] for idx in indices if 0 <= idx < len(tables)]
                inspect_specific_tables(selected_tables)
            except (ValueError, IndexError):
                print("Invalid selection. Please run the script again.")

if __name__ == "__main__":
    main()
