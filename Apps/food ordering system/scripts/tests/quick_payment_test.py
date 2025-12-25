"""
Quick test to identify the exact Razorpay payment error
"""
import os
import django
from decimal import Decimal

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

from django.conf import settings
import razorpay
import traceback

def quick_test():
    print("Testing Razorpay order creation...")
    
    try:
        # Initialize Razorpay client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        print(f"✅ Client initialized with key: {settings.RAZORPAY_KEY_ID}")
        
        # Create order directly (same as in payment_utils.py)
        amount_in_paise = int(float(Decimal('99.99')) * 100)
        order_data = {
            'amount': amount_in_paise,
            'currency': settings.RAZORPAY_CURRENCY,
            'receipt': 'test-receipt',
            'payment_capture': 1,
            'notes': {
                'order_id': 'test-order-123',
                'created_at': '2025-11-30T22:38:00',
            }
        }
        
        print("Creating order...")
        razorpay_order = client.order.create(data=order_data)
        print(f"✅ Order created successfully: {razorpay_order['id']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    quick_test()
