#!/usr/bin/env python3
"""
Test QR code generation directly on the table that needs it
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

def test_direct_qr_generation():
    """Test QR code generation on the specific table"""
    print("🧪 Testing QR Code Generation Directly...")
    
    try:
        # Get Pizza Palace restaurant
        pizza_palace = Restaurant.objects.filter(name='Pizza Palace').first()
        if not pizza_palace:
            print("❌ Pizza Palace restaurant not found")
            return
        
        print(f"✅ Found restaurant: {pizza_palace.name}")
        
        # Get Table 1 from Pizza Palace
        table = RestaurantTable.objects.filter(restaurant=pizza_palace, table_number='1').first()
        if not table:
            print("❌ Table 1 not found in Pizza Palace")
            return
        
        print(f"✅ Found table: {table}")
        print(f"   Table ID: {table.id}")
        print(f"   QR Code: {table.qr_code}")
        print(f"   QR Code UUID: {table.qr_code_uuid}")
        
        # Check if generate_qr_code method exists
        if hasattr(table, 'generate_qr_code'):
            print("✅ generate_qr_code method exists")
            
            # Test dependencies
            try:
                import qrcode
                from PIL import Image, ImageDraw, ImageFont
                print("✅ Dependencies available")
            except ImportError as e:
                print(f"❌ Missing dependency: {e}")
                return
            
            # Try to generate QR code
            print("🔄 Generating QR code...")
            result = table.generate_qr_code()
            print(f"📋 Generation result: {result}")
            
            if result:
                print("✅ QR code generated successfully!")
                print(f"📁 QR code path: {table.qr_code.path if table.qr_code else 'None'}")
                print(f"📁 QR code URL: {table.qr_code.url if table.qr_code else 'None'}")
                
                # Test the menu URL
                menu_url = table.get_menu_url()
                print(f"🔗 Menu URL: {menu_url}")
                
            else:
                print("❌ QR code generation failed")
                
        else:
            print("❌ generate_qr_code method NOT found")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_qr_generation()
