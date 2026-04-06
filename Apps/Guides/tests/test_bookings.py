"""
Test cases for the bookings app.

This module contains comprehensive test cases for all functionality
in the bookings app, including models, views, forms, and booking processes.
Every test function is thoroughly documented to make understanding
the tests easier for programmers.
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
import datetime

from bookings.models import Booking, BookingItem, Payment, Coupon, RefundRequest
from tours.models import Tour, TourDate
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class BookingModelTests(TravelGuideBaseTestCase):
    """
    Tests for the Booking model in the bookings app.
    
    These tests verify that Booking objects can be created correctly,
    and that their methods work as expected. Each test focuses on a 
    specific aspect of the Booking model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for Booking tests.
        
        Extends the base setUp method to include a booking for testing.
        Creates a tour, tour date, and booking for the test user.
        """
        super().setUp()
        
        # Create a tour date for the test tour
        self.tour_date = TourDate.objects.create(
            tour=self.test_tour,
            start_date=timezone.now().date() + datetime.timedelta(days=30),
            end_date=timezone.now().date() + datetime.timedelta(days=37),
            price=Decimal('1299.99'),
            available_seats=20
        )
        
        # Create a booking for the test user
        self.booking = Booking.objects.create(
            user=self.test_user,
            booking_number='BK12345',
            status='pending',
            total_price=Decimal('1299.99'),
            booking_date=timezone.now()
        )
        
        # Create a booking item for the booking
        self.booking_item = BookingItem.objects.create(
            booking=self.booking,
            tour_date=self.tour_date,
            quantity=1,
            price=Decimal('1299.99')
        )
    
    def test_booking_creation(self):
        """
        Test that a Booking can be created with the expected attributes.
        
        Verifies that the Booking model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new booking for the admin user
        booking = Booking.objects.create(
            user=self.admin_user,
            booking_number='BK67890',
            status='confirmed',
            total_price=Decimal('2599.98'),
            booking_date=timezone.now()
        )
        
        # Verify the booking was created with the correct attributes
        self.assertEqual(booking.user, self.admin_user)
        self.assertEqual(booking.booking_number, 'BK67890')
        self.assertEqual(booking.status, 'confirmed')
        self.assertEqual(booking.total_price, Decimal('2599.98'))
        self.assertIsNotNone(booking.booking_date)
        
    def test_booking_str_method(self):
        """
        Test the string representation of a Booking object.
        
        Verifies that the __str__ method returns the expected string,
        which should include the booking number.
        """
        expected_str = f"Booking #{self.booking.booking_number}"
        self.assertEqual(str(self.booking), expected_str)
        
    def test_booking_get_absolute_url(self):
        """
        Test the get_absolute_url method of the Booking model.
        
        Verifies that the URL generated for a booking detail page is correct
        and matches the expected URL pattern.
        """
        expected_url = reverse('bookings:booking_detail', kwargs={'booking_number': self.booking.booking_number})
        self.assertEqual(self.booking.get_absolute_url(), expected_url)
        
    def test_booking_total_items(self):
        """
        Test the total_items property of the Booking model.
        
        Verifies that the total_items property correctly calculates
        the total number of items in the booking.
        """
        # Add another booking item
        BookingItem.objects.create(
            booking=self.booking,
            tour_date=self.tour_date,
            quantity=2,
            price=Decimal('1299.99')
        )
        
        # The total should be 1 + 2 = 3
        self.assertEqual(self.booking.total_items, 3)
        
    def test_booking_calculate_total(self):
        """
        Test the calculate_total method of the Booking model.
        
        Verifies that the calculate_total method correctly calculates
        the total price of all items in the booking.
        """
        # Add another booking item
        BookingItem.objects.create(
            booking=self.booking,
            tour_date=self.tour_date,
            quantity=2,
            price=Decimal('1299.99')
        )
        
        # Calculate the total
        self.booking.calculate_total()
        
        # The total should be 1299.99 + (2 * 1299.99) = 3899.97
        self.assertEqual(self.booking.total_price, Decimal('3899.97'))


class BookingItemModelTests(TravelGuideBaseTestCase):
    """
    Tests for the BookingItem model in the bookings app.
    
    These tests verify that BookingItem objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the BookingItem model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for BookingItem tests.
        
        Extends the base setUp method to include a booking and booking item for testing.
        """
        super().setUp()
        
        # Create a tour date for the test tour
        self.tour_date = TourDate.objects.create(
            tour=self.test_tour,
            start_date=timezone.now().date() + datetime.timedelta(days=30),
            end_date=timezone.now().date() + datetime.timedelta(days=37),
            price=Decimal('1299.99'),
            available_seats=20
        )
        
        # Create a booking for the test user
        self.booking = Booking.objects.create(
            user=self.test_user,
            booking_number='BK12345',
            status='pending',
            total_price=Decimal('1299.99'),
            booking_date=timezone.now()
        )
        
        # Create a booking item for the booking
        self.booking_item = BookingItem.objects.create(
            booking=self.booking,
            tour_date=self.tour_date,
            quantity=1,
            price=Decimal('1299.99')
        )
    
    def test_booking_item_creation(self):
        """
        Test that a BookingItem can be created with the expected attributes.
        
        Verifies that the BookingItem model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new booking item
        booking_item = BookingItem.objects.create(
            booking=self.booking,
            tour_date=self.tour_date,
            quantity=2,
            price=Decimal('1299.99')
        )
        
        # Verify the booking item was created with the correct attributes
        self.assertEqual(booking_item.booking, self.booking)
        self.assertEqual(booking_item.tour_date, self.tour_date)
        self.assertEqual(booking_item.quantity, 2)
        self.assertEqual(booking_item.price, Decimal('1299.99'))
        
    def test_booking_item_str_method(self):
        """
        Test the string representation of a BookingItem object.
        
        Verifies that the __str__ method returns the expected string,
        which should include the tour name and quantity.
        """
        expected_str = f"{self.test_tour.title} x 1"
        self.assertEqual(str(self.booking_item), expected_str)
        
    def test_booking_item_subtotal(self):
        """
        Test the subtotal property of the BookingItem model.
        
        Verifies that the subtotal property correctly calculates
        the subtotal price of the booking item.
        """
        # Set the quantity to 2
        self.booking_item.quantity = 2
        self.booking_item.save()
        
        # The subtotal should be 2 * 1299.99 = 2599.98
        self.assertEqual(self.booking_item.subtotal, Decimal('2599.98'))


class PaymentModelTests(TravelGuideBaseTestCase):
    """
    Tests for the Payment model in the bookings app.
    
    These tests verify that Payment objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the Payment model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for Payment tests.
        
        Extends the base setUp method to include a booking and payment for testing.
        """
        super().setUp()
        
        # Create a booking for the test user
        self.booking = Booking.objects.create(
            user=self.test_user,
            booking_number='BK12345',
            status='pending',
            total_price=Decimal('1299.99'),
            booking_date=timezone.now()
        )
        
        # Create a payment for the booking
        self.payment = Payment.objects.create(
            booking=self.booking,
            payment_method='credit_card',
            transaction_id='TXN12345',
            amount=Decimal('1299.99'),
            status='completed',
            payment_date=timezone.now()
        )
    
    def test_payment_creation(self):
        """
        Test that a Payment can be created with the expected attributes.
        
        Verifies that the Payment model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new payment
        payment = Payment.objects.create(
            booking=self.booking,
            payment_method='paypal',
            transaction_id='TXN67890',
            amount=Decimal('500.00'),
            status='pending',
            payment_date=timezone.now()
        )
        
        # Verify the payment was created with the correct attributes
        self.assertEqual(payment.booking, self.booking)
        self.assertEqual(payment.payment_method, 'paypal')
        self.assertEqual(payment.transaction_id, 'TXN67890')
        self.assertEqual(payment.amount, Decimal('500.00'))
        self.assertEqual(payment.status, 'pending')
        self.assertIsNotNone(payment.payment_date)
        
    def test_payment_str_method(self):
        """
        Test the string representation of a Payment object.
        
        Verifies that the __str__ method returns the expected string,
        which should include the transaction ID and amount.
        """
        expected_str = f"Payment {self.payment.transaction_id} - ${self.payment.amount}"
        self.assertEqual(str(self.payment), expected_str)


class CouponModelTests(TravelGuideBaseTestCase):
    """
    Tests for the Coupon model in the bookings app.
    
    These tests verify that Coupon objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the Coupon model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for Coupon tests.
        
        Extends the base setUp method to include coupons for testing.
        """
        super().setUp()
        
        # Create a fixed amount coupon
        self.fixed_coupon = Coupon.objects.create(
            code='FIXED100',
            discount_type='fixed',
            discount_value=Decimal('100.00'),
            valid_from=timezone.now() - datetime.timedelta(days=10),
            valid_to=timezone.now() + datetime.timedelta(days=20),
            min_purchase=Decimal('500.00'),
            max_uses=100,
            current_uses=0,
            is_active=True
        )
        
        # Create a percentage coupon
        self.percent_coupon = Coupon.objects.create(
            code='PERCENT20',
            discount_type='percentage',
            discount_value=Decimal('20.00'),
            valid_from=timezone.now() - datetime.timedelta(days=10),
            valid_to=timezone.now() + datetime.timedelta(days=20),
            min_purchase=Decimal('0.00'),
            max_uses=50,
            current_uses=0,
            is_active=True
        )
    
    def test_coupon_creation(self):
        """
        Test that a Coupon can be created with the expected attributes.
        
        Verifies that the Coupon model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new coupon
        coupon = Coupon.objects.create(
            code='SUMMER30',
            discount_type='percentage',
            discount_value=Decimal('30.00'),
            valid_from=timezone.now(),
            valid_to=timezone.now() + datetime.timedelta(days=90),
            min_purchase=Decimal('200.00'),
            max_uses=200,
            current_uses=0,
            is_active=True
        )
        
        # Verify the coupon was created with the correct attributes
        self.assertEqual(coupon.code, 'SUMMER30')
        self.assertEqual(coupon.discount_type, 'percentage')
        self.assertEqual(coupon.discount_value, Decimal('30.00'))
        self.assertEqual(coupon.min_purchase, Decimal('200.00'))
        self.assertEqual(coupon.max_uses, 200)
        self.assertEqual(coupon.current_uses, 0)
        self.assertTrue(coupon.is_active)
        
    def test_coupon_str_method(self):
        """
        Test the string representation of a Coupon object.
        
        Verifies that the __str__ method returns the expected string,
        which should be the coupon code.
        """
        self.assertEqual(str(self.fixed_coupon), 'FIXED100')
        
    def test_coupon_is_valid(self):
        """
        Test the is_valid method of the Coupon model.
        
        Verifies that the is_valid method correctly determines if a coupon
        is valid based on its attributes and the given purchase amount.
        """
        # Test a valid fixed coupon
        self.assertTrue(self.fixed_coupon.is_valid(Decimal('600.00')))
        
        # Test a valid percentage coupon
        self.assertTrue(self.percent_coupon.is_valid(Decimal('100.00')))
        
        # Test with purchase amount below minimum
        self.assertFalse(self.fixed_coupon.is_valid(Decimal('400.00')))
        
        # Test with an inactive coupon
        self.fixed_coupon.is_active = False
        self.fixed_coupon.save()
        self.assertFalse(self.fixed_coupon.is_valid(Decimal('600.00')))
        
        # Test with a coupon that has reached max uses
        self.percent_coupon.current_uses = 50
        self.percent_coupon.save()
        self.assertFalse(self.percent_coupon.is_valid(Decimal('100.00')))
        
        # Test with an expired coupon
        self.percent_coupon.current_uses = 0
        self.percent_coupon.valid_to = timezone.now() - datetime.timedelta(days=1)
        self.percent_coupon.save()
        self.assertFalse(self.percent_coupon.is_valid(Decimal('100.00')))
        
    def test_coupon_calculate_discount(self):
        """
        Test the calculate_discount method of the Coupon model.
        
        Verifies that the calculate_discount method correctly calculates
        the discount amount based on the coupon type and purchase amount.
        """
        # Test fixed discount
        self.assertEqual(self.fixed_coupon.calculate_discount(Decimal('600.00')), Decimal('100.00'))
        
        # Test percentage discount (20% of 500 = 100)
        self.assertEqual(self.percent_coupon.calculate_discount(Decimal('500.00')), Decimal('100.00'))
        
        # Test percentage discount with rounding
        self.assertEqual(self.percent_coupon.calculate_discount(Decimal('333.33')), Decimal('66.67'))


class RefundRequestModelTests(TravelGuideBaseTestCase):
    """
    Tests for the RefundRequest model in the bookings app.
    
    These tests verify that RefundRequest objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the RefundRequest model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for RefundRequest tests.
        
        Extends the base setUp method to include a booking and refund request for testing.
        """
        super().setUp()
        
        # Create a booking for the test user
        self.booking = Booking.objects.create(
            user=self.test_user,
            booking_number='BK12345',
            status='confirmed',
            total_price=Decimal('1299.99'),
            booking_date=timezone.now()
        )
        
        # Create a payment for the booking
        self.payment = Payment.objects.create(
            booking=self.booking,
            payment_method='credit_card',
            transaction_id='TXN12345',
            amount=Decimal('1299.99'),
            status='completed',
            payment_date=timezone.now()
        )
        
        # Create a refund request for the booking
        self.refund_request = RefundRequest.objects.create(
            booking=self.booking,
            reason='Change of plans',
            status='pending',
            request_date=timezone.now(),
            amount=Decimal('1299.99')
        )
    
    def test_refund_request_creation(self):
        """
        Test that a RefundRequest can be created with the expected attributes.
        
        Verifies that the RefundRequest model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new refund request
        refund_request = RefundRequest.objects.create(
            booking=self.booking,
            reason='Emergency situation',
            status='approved',
            request_date=timezone.now(),
            amount=Decimal('1000.00'),
            processed_date=timezone.now()
        )
        
        # Verify the refund request was created with the correct attributes
        self.assertEqual(refund_request.booking, self.booking)
        self.assertEqual(refund_request.reason, 'Emergency situation')
        self.assertEqual(refund_request.status, 'approved')
        self.assertEqual(refund_request.amount, Decimal('1000.00'))
        self.assertIsNotNone(refund_request.processed_date)
        
    def test_refund_request_str_method(self):
        """
        Test the string representation of a RefundRequest object.
        
        Verifies that the __str__ method returns the expected string,
        which should include the booking number and status.
        """
        expected_str = f"Refund for {self.booking.booking_number} - {self.refund_request.status}"
        self.assertEqual(str(self.refund_request), expected_str)


class BookingViewTests(TravelGuideBaseTestCase):
    """
    Tests for the views in the bookings app.
    
    These tests verify that the views render the correct templates,
    contain the expected context data, and handle form submissions correctly.
    Each test focuses on a specific view or aspect of view functionality.
    """
    
    def setUp(self):
        """
        Set up test data for booking view tests.
        
        Extends the base setUp method to include necessary booking data.
        """
        super().setUp()
        
        # Create a tour date for the test tour
        self.tour_date = TourDate.objects.create(
            tour=self.test_tour,
            start_date=timezone.now().date() + datetime.timedelta(days=30),
            end_date=timezone.now().date() + datetime.timedelta(days=37),
            price=Decimal('1299.99'),
            available_seats=20
        )
        
        # Create a booking for the test user
        self.booking = Booking.objects.create(
            user=self.test_user,
            booking_number='BK12345',
            status='confirmed',
            total_price=Decimal('1299.99'),
            booking_date=timezone.now()
        )
        
        # Create a booking item for the booking
        self.booking_item = BookingItem.objects.create(
            booking=self.booking,
            tour_date=self.tour_date,
            quantity=1,
            price=Decimal('1299.99')
        )
        
        # Create a payment for the booking
        self.payment = Payment.objects.create(
            booking=self.booking,
            payment_method='credit_card',
            transaction_id='TXN12345',
            amount=Decimal('1299.99'),
            status='completed',
            payment_date=timezone.now()
        )
        
        # Log in the test user
        self.login_test_user()
    
    def test_booking_list_view(self):
        """
        Test the booking list view.
        
        Verifies that the booking list view returns a 200 status code,
        uses the correct template, and includes the user's bookings in the context.
        """
        response = self.client.get(reverse('bookings:booking_list'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'bookings/booking_list.html')
        
        # Check that the bookings are in the context
        self.assertIn('bookings', response.context)
        self.assertEqual(list(response.context['bookings']), [self.booking])
        
    def test_booking_detail_view(self):
        """
        Test the booking detail view.
        
        Verifies that the booking detail view returns a 200 status code,
        uses the correct template, and includes the booking in the context.
        """
        response = self.client.get(reverse('bookings:booking_detail', kwargs={'booking_number': self.booking.booking_number}))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'bookings/booking_detail.html')
        
        # Check that the booking is in the context
        self.assertEqual(response.context['booking'], self.booking)
        
    def test_create_booking_view(self):
        """
        Test the create booking view.
        
        Verifies that the create booking view returns a 200 status code,
        uses the correct template, and allows creating a booking.
        """
        # Get the create booking page for a specific tour date
        response = self.client.get(reverse('bookings:create_booking', kwargs={'tour_date_id': self.tour_date.id}))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'bookings/create_booking.html')
        
        # Check that the tour date is in the context
        self.assertEqual(response.context['tour_date'], self.tour_date)
        
        # Submit the booking form
        response = self.client.post(reverse('bookings:create_booking', kwargs={'tour_date_id': self.tour_date.id}), {
            'quantity': 2,
            'special_requests': 'Vegetarian meals please'
        })
        
        # Check that the booking was created and redirected to checkout
        self.assertEqual(response.status_code, 302)  # Redirect status code
        
        # Check that a new booking was created
        self.assertEqual(Booking.objects.count(), 2)
        
        # Get the newly created booking
        new_booking = Booking.objects.exclude(id=self.booking.id).first()
        
        # Check that the booking has the correct attributes
        self.assertEqual(new_booking.user, self.test_user)
        self.assertEqual(new_booking.status, 'pending')
        
        # Check that a booking item was created
        booking_item = BookingItem.objects.filter(booking=new_booking).first()
        self.assertEqual(booking_item.tour_date, self.tour_date)
        self.assertEqual(booking_item.quantity, 2)
        
    def test_checkout_view(self):
        """
        Test the checkout view.
        
        Verifies that the checkout view returns a 200 status code,
        uses the correct template, and includes the booking in the context.
        """
        # Create a pending booking for checkout
        pending_booking = Booking.objects.create(
            user=self.test_user,
            booking_number='BK67890',
            status='pending',
            total_price=Decimal('2599.98'),
            booking_date=timezone.now()
        )
        
        # Create a booking item for the pending booking
        BookingItem.objects.create(
            booking=pending_booking,
            tour_date=self.tour_date,
            quantity=2,
            price=Decimal('1299.99')
        )
        
        # Get the checkout page
        response = self.client.get(reverse('bookings:checkout', kwargs={'booking_number': pending_booking.booking_number}))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'bookings/checkout.html')
        
        # Check that the booking is in the context
        self.assertEqual(response.context['booking'], pending_booking)
        
    def test_apply_coupon_view(self):
        """
        Test the apply coupon view.
        
        Verifies that the apply coupon view correctly applies a valid coupon
        to a booking and returns the appropriate response.
        """
        # Create a coupon
        coupon = Coupon.objects.create(
            code='TEST20',
            discount_type='percentage',
            discount_value=Decimal('20.00'),
            valid_from=timezone.now() - datetime.timedelta(days=10),
            valid_to=timezone.now() + datetime.timedelta(days=20),
            min_purchase=Decimal('0.00'),
            max_uses=50,
            current_uses=0,
            is_active=True
        )
        
        # Create a pending booking for checkout
        pending_booking = Booking.objects.create(
            user=self.test_user,
            booking_number='BK67890',
            status='pending',
            total_price=Decimal('1299.99'),
            booking_date=timezone.now()
        )
        
        # Create a booking item for the pending booking
        BookingItem.objects.create(
            booking=pending_booking,
            tour_date=self.tour_date,
            quantity=1,
            price=Decimal('1299.99')
        )
        
        # Apply the coupon to the booking
        response = self.client.post(reverse('bookings:apply_coupon', kwargs={'booking_number': pending_booking.booking_number}), {
            'coupon_code': 'TEST20'
        })
        
        # Check that the coupon was applied and redirected back to checkout
        self.assertEqual(response.status_code, 302)  # Redirect status code
        
        # Refresh the booking from the database
        pending_booking.refresh_from_db()
        
        # Check that the coupon was applied (20% discount on 1299.99 = 259.998 ≈ 260.00)
        # The total price should be 1299.99 - 260.00 = 1039.99
        self.assertEqual(pending_booking.total_price, Decimal('1039.99'))
        
    def test_request_refund_view(self):
        """
        Test the request refund view.
        
        Verifies that the request refund view returns a 200 status code,
        uses the correct template, and allows requesting a refund.
        """
        # Get the request refund page
        response = self.client.get(reverse('bookings:request_refund', kwargs={'booking_number': self.booking.booking_number}))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'bookings/request_refund.html')
        
        # Submit the refund request form
        response = self.client.post(reverse('bookings:request_refund', kwargs={'booking_number': self.booking.booking_number}), {
            'reason': 'Change of plans',
            'amount': '1299.99'
        })
        
        # Check that the refund request was created and redirected
        self.assertEqual(response.status_code, 302)  # Redirect status code
        
        # Check that a refund request was created
        self.assertTrue(RefundRequest.objects.filter(booking=self.booking, reason='Change of plans').exists())
