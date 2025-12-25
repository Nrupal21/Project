#!/usr/bin/env python3
"""
Debug script to test QR code generation functionality
Run this to test if the QR code generation works independently
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
from django.contrib.auth.models import User

def test_qr_generation():
    """Test QR code generation directly"""
    print("🔍 Testing QR Code Generation...")
    
    try:
        # Get a test restaurant
        restaurant = Restaurant.objects.first()
        if not restaurant:
            print("❌ No restaurant found")
            return
        
        print(f"✅ Found restaurant: {restaurant.name}")
        
        # Get tables without QR codes
        tables_without_qr = RestaurantTable.objects.filter(
            restaurant=restaurant,
            qr_code__isnull=True
        ) | RestaurantTable.objects.filter(
            restaurant=restaurant,
            qr_code=''
        )
        
        print(f"📊 Found {tables_without_qr.count()} tables without QR codes")
        
        if not tables_without_qr.exists():
            print("ℹ️ All tables already have QR codes")
            return
        
        # Test generating QR code for first table
        test_table = tables_without_qr.first()
        print(f"🧪 Testing QR generation for table: {test_table.table_number}")
        
        # Check if generate_qr_code method exists
        if hasattr(test_table, 'generate_qr_code'):
            print("✅ generate_qr_code method exists")
            
            # Try to generate QR code
            result = test_table.generate_qr_code()
            print(f"📋 Generation result: {result}")
            
            if result:
                print("✅ QR code generated successfully!")
                print(f"📁 QR code path: {test_table.qr_code.path if test_table.qr_code else 'None'}")
            else:
                print("❌ QR code generation failed")
                
        else:
            print("❌ generate_qr_code method NOT found")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

def test_dependencies():
    """Test if required libraries are installed"""
    print("\n🔍 Testing Dependencies...")
    
    try:
        import qrcode
        print("✅ qrcode library installed")
    except ImportError:
        print("❌ qrcode library NOT installed")
        print("   Run: pip install qrcode[pil]")
        return False
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        print("✅ PIL library installed")
    except ImportError:
        print("❌ PIL library NOT installed")
        print("   Run: pip install Pillow")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 QR Code Generation Debug Tool")
    print("=" * 50)
    
    # Test dependencies first
    if test_dependencies():
        # Test QR generation
        test_qr_generation()
    
    print("\n🏁 Debug complete")
