#!/usr/bin/env python
"""
Script to check the PostgreSQL database and examine the data structure
"""
import os
import sys
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guides.settings')
django.setup()

from django.db import connection
from destinations.models import Destination, DestinationImage, Region, Attraction
from tours.models import Tour, TourCategory, TourImage

def check_database_connection():
    """Test database connection and return status"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            result = cursor.fetchone()
            print(f"✓ Database connection successful!")
            print(f"PostgreSQL Version: {result[0]}")
            return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def get_table_info():
    """Get information about database tables"""
    print("\n=== Database Tables Information ===")
    
    with connection.cursor() as cursor:
        # Get all table names
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        print(f"Total tables found: {len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")
            
        print("\n=== Table Row Counts ===")
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]};")
                count = cursor.fetchone()[0]
                print(f"  {table[0]}: {count} rows")
            except Exception as e:
                print(f"  {table[0]}: Error - {e}")

def check_model_data():
    """Check data in Django models"""
    print("\n=== Django Model Data ===")
    
    # Check Regions
    try:
        regions = Region.objects.all()
        print(f"Regions: {regions.count()} records")
        for region in regions[:5]:  # Show first 5
            print(f"  - {region.name}")
    except Exception as e:
        print(f"Regions error: {e}")
    
    # Check Destinations
    try:
        destinations = Destination.objects.all()
        print(f"Destinations: {destinations.count()} records")
        for dest in destinations[:5]:  # Show first 5
            print(f"  - {dest.name} ({dest.region.name if dest.region else 'No region'})")
    except Exception as e:
        print(f"Destinations error: {e}")
    
    # Check Tours
    try:
        tours = Tour.objects.all()
        print(f"Tours: {tours.count()} records")
        for tour in tours[:5]:  # Show first 5
            print(f"  - {tour.name} (${tour.price})")
    except Exception as e:
        print(f"Tours error: {e}")
    
    # Check Tour Categories
    try:
        categories = TourCategory.objects.all()
        print(f"Tour Categories: {categories.count()} records")
        for cat in categories[:5]:  # Show first 5
            print(f"  - {cat.name}")
    except Exception as e:
        print(f"Tour Categories error: {e}")
    
    # Check Attractions
    try:
        attractions = Attraction.objects.all()
        print(f"Attractions: {attractions.count()} records")
        for attr in attractions[:5]:  # Show first 5
            print(f"  - {attr.name} ({attr.destination.name if attr.destination else 'No destination'})")
    except Exception as e:
        print(f"Attractions error: {e}")

def check_featured_data():
    """Check specifically for featured/popular data"""
    print("\n=== Featured/Popular Data ===")
    
    try:
        featured_destinations = Destination.objects.filter(is_featured=True, is_active=True)
        print(f"Featured Destinations: {featured_destinations.count()} records")
        for dest in featured_destinations:
            print(f"  - {dest.name} (Rating: {dest.rating}, Price: ${dest.price})")
    except Exception as e:
        print(f"Featured Destinations error: {e}")
    
    try:
        popular_tours = Tour.objects.filter(is_active=True, is_popular=True)
        print(f"Popular Tours: {popular_tours.count()} records")
        for tour in popular_tours:
            print(f"  - {tour.name} (${tour.price})")
    except Exception as e:
        print(f"Popular Tours error: {e}")
    
    try:
        featured_attractions = Attraction.objects.filter(is_active=True, is_featured=True)
        print(f"Featured Attractions: {featured_attractions.count()} records")
        for attr in featured_attractions:
            print(f"  - {attr.name}")
    except Exception as e:
        print(f"Featured Attractions error: {e}")

def main():
    """Main function to run all checks"""
    print("🔍 Checking PostgreSQL Database for TravelGuide Project")
    print("=" * 60)
    
    # Check database connection
    if not check_database_connection():
        return
    
    # Get table information
    get_table_info()
    
    # Check model data
    check_model_data()
    
    # Check featured data specifically
    check_featured_data()
    
    print("\n" + "=" * 60)
    print("✅ Database inspection completed!")

if __name__ == "__main__":
    main()
