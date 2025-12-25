"""
Quick test script to verify Razorpay API connection and configuration.
Run this to diagnose payment gateway issues.
"""
import os
import django
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

from django.conf import settings
from core.payment_utils import create_razorpay_order
import razorpay

def test_razorpay_connection():
    """
    Test Razorpay API connection and order creation functionality.
    This will help identify the exact cause of payment gateway errors.
    """
    print("=" * 60)
    print("RAZORPAY CONNECTION TEST")
    print("=" * 60)
    
    # Step 1: Check configuration
    print("\n1. Checking Razorpay Configuration...")
    print(f"   RAZORPAY_KEY_ID: {settings.RAZORPAY_KEY_ID}")
    print(f"   RAZORPAY_KEY_SECRET: {'*' * 10 if settings.RAZORPAY_KEY_SECRET else 'NOT SET'}")
    print(f"   RAZORPAY_CURRENCY: {settings.RAZORPAY_CURRENCY}")
    print(f"   RAZORPAY_PAYMENT_TIMEOUT: {settings.RAZORPAY_PAYMENT_TIMEOUT}")
    
    # Step 2: Test basic Razorpay client initialization
    print("\n2. Testing Razorpay Client Initialization...")
    try:
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        print("   ✅ Razorpay client initialized successfully")
    except Exception as e:
        print(f"   ❌ Razorpay client initialization failed: {e}")
        return False
    
    # Step 3: Test order creation (this is what fails in checkout)
    print("\n3. Testing Order Creation...")
    try:
    
    # Step 4: Test order creation (this is what fails in checkout)
    print("\n4. Testing Order Creation...")
    try:
        test_order = create_razorpay_order(
            amount=Decimal('99.99'),
            order_id='test-order-123',
            receipt_id='test-receipt-123'
        )
        print("   ✅ Order creation successful")
        print(f"   Order ID: {test_order['id']}")
        print(f"   Amount: {test_order['amount']} paise")
        print(f"   Currency: {test_order['currency']}")
        print(f"   Status: {test_order['status']}")
        
        # Step 5: Clean up - cancel the test order
        print("\n5. Cleaning up test order...")
        try:
            client.order.cancel(test_order['id'])
            print("   ✅ Test order cancelled successfully")
        except Exception as e:
            print(f"   ⚠️  Could not cancel test order (manual cleanup may be needed): {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Order creation failed: {e}")
        print(f"   This is the exact error causing your payment gateway issue!")
        return False

def test_environment_variables():
    """
    Test if environment variables are loaded correctly.
    """
    print("\n" + "=" * 60)
    print("ENVIRONMENT VARIABLES TEST")
    print("=" * 60)
    
    # Check .env file exists
    env_file = '.env'
    if os.path.exists(env_file):
        print(f"\n✅ {env_file} file exists")
        
        # Read and display Razorpay keys (masked)
        with open(env_file, 'r') as f:
            content = f.read()
            if 'RAZORPAY_KEY_ID=' in content:
                key_line = [line for line in content.split('\n') if 'RAZORPAY_KEY_ID=' in line][0]
                key_value = key_line.split('=')[1]
                print(f"   RAZORPAY_KEY_ID: {key_value}")
            else:
                print("   ❌ RAZORPAY_KEY_ID not found in .env")
                
            if 'RAZORPAY_KEY_SECRET=' in content:
                secret_line = [line for line in content.split('\n') if 'RAZORPAY_KEY_SECRET=' in line][0]
                secret_value = secret_line.split('=')[1]
                if secret_value == 'your_secret_key_here':
                    print("   ❌ RAZORPAY_KEY_SECRET is still placeholder value")
                else:
                    print(f"   RAZORPAY_KEY_SECRET: {'*' * 10}")
            else:
                print("   ❌ RAZORPAY_KEY_SECRET not found in .env")
    else:
        print(f"\n❌ {env_file} file not found in current directory")

if __name__ == "__main__":
    print("Starting Razorpay Connection Test...")
    print("This will help diagnose your payment gateway error.\n")
    
    # Test environment variables first
    test_environment_variables()
    
    # Test Razorpay connection
    success = test_razorpay_connection()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if success:
        print("✅ All tests passed! Razorpay integration is working correctly.")
        print("If you're still seeing errors, try restarting your Django server.")
    else:
        print("❌ Tests failed. Check the error messages above for the exact issue.")
        print("\nCommon solutions:")
        print("1. Verify your Razorpay API keys are correct")
        print("2. Check if your Razorpay account is active")
        print("3. Ensure you're using TEST mode keys for development")
        print("4. Restart your Django server after changing .env file")
    
    print("\nTo run this test: python test_razorpay_connection.py")
