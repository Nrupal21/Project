from django.db import connection

# Check database tables and content
def check_database():
    with connection.cursor() as cursor:
        # Get all table names
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")
            
        # Check row counts for key tables
        key_tables = [
            'destinations_destination',
            'destinations_destinationimage', 
            'destinations_region',
            'destinations_attraction',
            'tours_tour',
            'tours_tourcategory',
            'tours_tourimage'
        ]
        
        print("\nRow counts for key tables:")
        for table in key_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                print(f"  {table}: {count} rows")
            except Exception as e:
                print(f"  {table}: Error - {e}")

check_database()
