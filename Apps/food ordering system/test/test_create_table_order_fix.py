"""
Test script to verify the Create Table Order fix.

This script tests that only selected menu items are submitted when creating a table order.

Run this test after the fix to ensure the issue is resolved.
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from restaurant.models import Restaurant, RestaurantTable
from menu.models import Category, MenuItem
from orders.models import Order, OrderItem
from decimal import Decimal

User = get_user_model()


class CreateTableOrderFixTest(TestCase):
    """
    Test case to verify that only selected menu items are added to orders.
    
    Tests the fix for the bug where all menu items were being submitted
    regardless of user selection.
    """
    
    def setUp(self):
        """
        Set up test data including user, restaurant, table, and menu items.
        
        Creates:
            - Restaurant owner user
            - Restaurant
            - Table
            - Category
            - 5 menu items
        """
        # Create restaurant owner
        self.user = User.objects.create_user(
            username='testowner',
            email='owner@test.com',
            password='testpass123',
            role='restaurant_owner'
        )
        
        # Create restaurant
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            owner=self.user,
            cuisine_type='Italian',
            is_approved=True,
            approval_status='approved'
        )
        
        # Create table
        self.table = RestaurantTable.objects.create(
            restaurant=self.restaurant,
            table_number='T1',
            capacity=4,
            is_active=True
        )
        
        # Create category
        self.category = Category.objects.create(
            name='Main Course',
            is_active=True
        )
        
        # Create 5 menu items
        self.menu_items = []
        for i in range(1, 6):
            item = MenuItem.objects.create(
                restaurant=self.restaurant,
                category=self.category,
                name=f'Test Item {i}',
                description=f'Description for item {i}',
                price=Decimal(f'{i}0.00'),
                is_available=True
            )
            self.menu_items.append(item)
        
        # Set up client and login
        self.client = Client()
        self.client.login(username='testowner', password='testpass123')
    
    def test_only_selected_items_submitted(self):
        """
        Test that only selected menu items (items 1, 3, and 5) are added to the order.
        
        Simulates selecting 3 out of 5 menu items and verifies that only those
        3 items are included in the created order.
        """
        # Select only items 1, 3, and 5
        selected_items = [self.menu_items[0], self.menu_items[2], self.menu_items[4]]
        
        # Prepare POST data - only selected items
        post_data = {
            'customer_name': 'Test Customer',
            'customer_phone': '1234567890',
            'menu_items[]': [item.id for item in selected_items],
            'quantities[]': [2, 1, 3],  # Different quantities for each
            'notes': 'Test order',
            'print_kitchen': 'off'
        }
        
        # Submit the order
        response = self.client.post(
            f'/restaurant/table-order/{self.table.id}/',
            data=post_data
        )
        
        # Verify order was created
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        
        # Verify only 3 items were added (not all 5)
        self.assertEqual(order.items.count(), 3)
        
        # Verify correct items were added
        order_item_ids = set(order.items.values_list('menu_item_id', flat=True))
        expected_item_ids = set([item.id for item in selected_items])
        self.assertEqual(order_item_ids, expected_item_ids)
        
        # Verify quantities are correct
        item_quantities = {
            order.items.get(menu_item=selected_items[0]).quantity: 2,
            order.items.get(menu_item=selected_items[1]).quantity: 1,
            order.items.get(menu_item=selected_items[2]).quantity: 3,
        }
        
        # Verify total amount is correct
        expected_total = (
            selected_items[0].price * 2 +
            selected_items[1].price * 1 +
            selected_items[2].price * 3
        )
        self.assertEqual(order.total_amount, expected_total)
    
    def test_single_item_selection(self):
        """
        Test that selecting only one item works correctly.
        
        Verifies that when only 1 item is selected, only that item is added
        to the order (not all menu items).
        """
        # Select only the first item
        selected_item = self.menu_items[0]
        
        post_data = {
            'customer_name': 'Test Customer',
            'customer_phone': '1234567890',
            'menu_items[]': [selected_item.id],
            'quantities[]': [1],
            'notes': '',
            'print_kitchen': 'off'
        }
        
        response = self.client.post(
            f'/restaurant/table-order/{self.table.id}/',
            data=post_data
        )
        
        # Verify order was created with only 1 item
        order = Order.objects.first()
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().menu_item, selected_item)
    
    def test_no_items_selected_validation(self):
        """
        Test that submitting without selecting any items shows an error.
        
        Verifies that the validation prevents creating orders with no items.
        """
        post_data = {
            'customer_name': 'Test Customer',
            'customer_phone': '1234567890',
            'menu_items[]': [],  # No items selected
            'quantities[]': [],
            'notes': '',
            'print_kitchen': 'off'
        }
        
        response = self.client.post(
            f'/restaurant/table-order/{self.table.id}/',
            data=post_data
        )
        
        # Verify no order was created
        self.assertEqual(Order.objects.count(), 0)
        
        # Verify error message is shown
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('select at least one item' in str(m) for m in messages))
    
    def test_all_items_selected(self):
        """
        Test that selecting all items works correctly.
        
        Verifies that when all items are selected, all items are added
        (this should work both before and after the fix).
        """
        post_data = {
            'customer_name': 'Test Customer',
            'customer_phone': '1234567890',
            'menu_items[]': [item.id for item in self.menu_items],
            'quantities[]': [1] * len(self.menu_items),
            'notes': '',
            'print_kitchen': 'off'
        }
        
        response = self.client.post(
            f'/restaurant/table-order/{self.table.id}/',
            data=post_data
        )
        
        # Verify order was created with all 5 items
        order = Order.objects.first()
        self.assertEqual(order.items.count(), 5)


# Manual testing instructions
if __name__ == '__main__':
    print("""
    Manual Testing Instructions for Create Table Order Fix
    ======================================================
    
    1. Start the development server:
       python manage.py runserver
    
    2. Login as a restaurant owner
    
    3. Navigate to: Restaurant Dashboard > Active Tables > Create Order for Table
    
    4. Test Scenario 1: Select Single Item
       - Click on ONE menu item
       - Verify it shows in the cart
       - Submit the order
       - Check order details - should have only 1 item
    
    5. Test Scenario 2: Select Multiple Items
       - Click on 3-4 menu items
       - Verify only selected items show in cart
       - Submit the order
       - Check order details - should have only selected items
    
    6. Test Scenario 3: Deselect Items
       - Select 5 items
       - Deselect 2 items
       - Verify cart shows only 3 items
       - Submit the order
       - Check order details - should have only 3 items
    
    7. Test Scenario 4: Clear Cart
       - Select several items
       - Click "Clear Cart" button
       - Verify cart is empty
       - Try to submit - should show validation error
    
    8. Test Scenario 5: Change Quantities
       - Select 2-3 items
       - Change quantities to different values
       - Submit the order
       - Check order details - quantities should match
    
    Expected Results:
    ----------------
    - Only selected items appear in the order
    - Quantities are correct
    - Total amount is calculated correctly
    - No unselected items are added to the order
    
    If any test fails, the fix may not be working correctly.
    """)
