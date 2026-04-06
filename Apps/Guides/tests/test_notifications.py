"""
Test cases for the notifications app.

This module contains comprehensive test cases for all functionality
in the notifications app, including models, views, and notification delivery.
Every test function is thoroughly documented to make understanding
the tests easier for programmers.
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
import datetime

from notifications.models import Notification, NotificationPreference, NotificationType
from bookings.models import Booking
from tours.models import Tour
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class NotificationModelTests(TravelGuideBaseTestCase):
    """
    Tests for the Notification model in the notifications app.
    
    These tests verify that Notification objects can be created correctly,
    and that their methods work as expected. Each test focuses on a 
    specific aspect of the Notification model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for Notification tests.
        
        Extends the base setUp method to include a notification for testing.
        """
        super().setUp()
        
        # Create a notification for the test user
        self.notification = Notification.objects.create(
            user=self.test_user,
            title="Tour Booking Confirmed",
            message="Your tour booking has been confirmed.",
            notification_type="booking_confirmation",
            is_read=False,
            created_at=timezone.now()
        )
        
        # Create a notification with a related object
        self.booking = Booking.objects.create(
            user=self.test_user,
            booking_number='BK12345',
            status='confirmed',
            total_price=1299.99,
            booking_date=timezone.now()
        )
        
        # Get content type for the booking
        booking_content_type = ContentType.objects.get_for_model(Booking)
        
        self.notification_with_object = Notification.objects.create(
            user=self.test_user,
            title="Payment Received",
            message="We have received your payment for booking #BK12345.",
            notification_type="payment_confirmation",
            is_read=False,
            created_at=timezone.now(),
            content_type=booking_content_type,
            object_id=self.booking.id
        )
    
    def test_notification_creation(self):
        """
        Test that a Notification can be created with the expected attributes.
        
        Verifies that the Notification model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new notification
        notification = Notification.objects.create(
            user=self.admin_user,
            title="Welcome to TravelGuide",
            message="Thank you for joining our platform.",
            notification_type="welcome",
            is_read=False,
            created_at=timezone.now()
        )
        
        # Verify the notification was created with the correct attributes
        self.assertEqual(notification.user, self.admin_user)
        self.assertEqual(notification.title, "Welcome to TravelGuide")
        self.assertEqual(notification.message, "Thank you for joining our platform.")
        self.assertEqual(notification.notification_type, "welcome")
        self.assertFalse(notification.is_read)
        self.assertIsNotNone(notification.created_at)
        
    def test_notification_str_method(self):
        """
        Test the string representation of a Notification object.
        
        Verifies that the __str__ method returns the expected string,
        which should include the notification title and username.
        """
        expected_str = f"Tour Booking Confirmed for testuser"
        self.assertEqual(str(self.notification), expected_str)
        
    def test_notification_mark_as_read(self):
        """
        Test the mark_as_read method of the Notification model.
        
        Verifies that the mark_as_read method correctly updates the is_read
        attribute and sets the read_at timestamp.
        """
        # Initially the notification is unread
        self.assertFalse(self.notification.is_read)
        self.assertIsNone(self.notification.read_at)
        
        # Mark the notification as read
        self.notification.mark_as_read()
        
        # Verify the notification is now marked as read
        self.assertTrue(self.notification.is_read)
        self.assertIsNotNone(self.notification.read_at)
        
    def test_notification_with_related_object(self):
        """
        Test a Notification with a related object.
        
        Verifies that a Notification can be created with a generic relation
        to another model, and that the related object can be accessed.
        """
        # Verify the notification has the correct related object
        self.assertEqual(self.notification_with_object.content_object, self.booking)
        
        # Verify the notification type
        self.assertEqual(self.notification_with_object.notification_type, "payment_confirmation")
        
    def test_notification_get_absolute_url(self):
        """
        Test the get_absolute_url method of the Notification model.
        
        Verifies that the URL generated for a notification detail page is correct
        and matches the expected URL pattern.
        """
        expected_url = reverse('notifications:notification_detail', kwargs={'pk': self.notification.pk})
        self.assertEqual(self.notification.get_absolute_url(), expected_url)


class NotificationTypeModelTests(TravelGuideBaseTestCase):
    """
    Tests for the NotificationType model in the notifications app.
    
    These tests verify that NotificationType objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the NotificationType model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for NotificationType tests.
        
        Extends the base setUp method to include notification types for testing.
        """
        super().setUp()
        
        # Create notification types
        self.booking_type = NotificationType.objects.create(
            code="booking_confirmation",
            name="Booking Confirmation",
            description="Sent when a booking is confirmed",
            email_template="emails/booking_confirmation.html",
            sms_template="Your booking #{booking_number} has been confirmed."
        )
        
        self.payment_type = NotificationType.objects.create(
            code="payment_confirmation",
            name="Payment Confirmation",
            description="Sent when a payment is received",
            email_template="emails/payment_confirmation.html",
            sms_template="Your payment of ${amount} for booking #{booking_number} has been received."
        )
    
    def test_notification_type_creation(self):
        """
        Test that a NotificationType can be created with the expected attributes.
        
        Verifies that the NotificationType model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new notification type
        notification_type = NotificationType.objects.create(
            code="tour_reminder",
            name="Tour Reminder",
            description="Sent as a reminder before a tour starts",
            email_template="emails/tour_reminder.html",
            sms_template="Reminder: Your tour starts in {days} days."
        )
        
        # Verify the notification type was created with the correct attributes
        self.assertEqual(notification_type.code, "tour_reminder")
        self.assertEqual(notification_type.name, "Tour Reminder")
        self.assertEqual(notification_type.description, "Sent as a reminder before a tour starts")
        self.assertEqual(notification_type.email_template, "emails/tour_reminder.html")
        self.assertEqual(notification_type.sms_template, "Reminder: Your tour starts in {days} days.")
        
    def test_notification_type_str_method(self):
        """
        Test the string representation of a NotificationType object.
        
        Verifies that the __str__ method returns the expected string,
        which should be the notification type name.
        """
        self.assertEqual(str(self.booking_type), "Booking Confirmation")
        
    def test_notification_type_get_template(self):
        """
        Test the get_template method of the NotificationType model.
        
        Verifies that the get_template method returns the correct template
        for the specified channel.
        """
        # Test getting the email template
        self.assertEqual(self.booking_type.get_template('email'), "emails/booking_confirmation.html")
        
        # Test getting the SMS template
        self.assertEqual(self.booking_type.get_template('sms'), "Your booking #{booking_number} has been confirmed.")
        
        # Test with an unsupported channel
        with self.assertRaises(ValueError):
            self.booking_type.get_template('unsupported_channel')


class NotificationPreferenceModelTests(TravelGuideBaseTestCase):
    """
    Tests for the NotificationPreference model in the notifications app.
    
    These tests verify that NotificationPreference objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the NotificationPreference model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for NotificationPreference tests.
        
        Extends the base setUp method to include notification types and preferences for testing.
        """
        super().setUp()
        
        # Create notification types
        self.booking_type = NotificationType.objects.create(
            code="booking_confirmation",
            name="Booking Confirmation",
            description="Sent when a booking is confirmed",
            email_template="emails/booking_confirmation.html",
            sms_template="Your booking #{booking_number} has been confirmed."
        )
        
        self.payment_type = NotificationType.objects.create(
            code="payment_confirmation",
            name="Payment Confirmation",
            description="Sent when a payment is received",
            email_template="emails/payment_confirmation.html",
            sms_template="Your payment of ${amount} for booking #{booking_number} has been received."
        )
        
        # Create notification preferences for the test user
        self.booking_preference = NotificationPreference.objects.create(
            user=self.test_user,
            notification_type=self.booking_type,
            email_enabled=True,
            sms_enabled=False,
            push_enabled=True
        )
        
        self.payment_preference = NotificationPreference.objects.create(
            user=self.test_user,
            notification_type=self.payment_type,
            email_enabled=True,
            sms_enabled=True,
            push_enabled=True
        )
    
    def test_notification_preference_creation(self):
        """
        Test that a NotificationPreference can be created with the expected attributes.
        
        Verifies that the NotificationPreference model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new notification type
        reminder_type = NotificationType.objects.create(
            code="tour_reminder",
            name="Tour Reminder",
            description="Sent as a reminder before a tour starts",
            email_template="emails/tour_reminder.html",
            sms_template="Reminder: Your tour starts in {days} days."
        )
        
        # Create a notification preference for the admin user
        preference = NotificationPreference.objects.create(
            user=self.admin_user,
            notification_type=reminder_type,
            email_enabled=True,
            sms_enabled=True,
            push_enabled=False
        )
        
        # Verify the preference was created with the correct attributes
        self.assertEqual(preference.user, self.admin_user)
        self.assertEqual(preference.notification_type, reminder_type)
        self.assertTrue(preference.email_enabled)
        self.assertTrue(preference.sms_enabled)
        self.assertFalse(preference.push_enabled)
        
    def test_notification_preference_str_method(self):
        """
        Test the string representation of a NotificationPreference object.
        
        Verifies that the __str__ method returns the expected string,
        which should include the username and notification type.
        """
        expected_str = f"Preferences for testuser - Booking Confirmation"
        self.assertEqual(str(self.booking_preference), expected_str)
        
    def test_notification_preference_is_channel_enabled(self):
        """
        Test the is_channel_enabled method of the NotificationPreference model.
        
        Verifies that the is_channel_enabled method correctly determines if a
        notification channel is enabled for a user.
        """
        # Test channels for booking preference
        self.assertTrue(self.booking_preference.is_channel_enabled('email'))
        self.assertFalse(self.booking_preference.is_channel_enabled('sms'))
        self.assertTrue(self.booking_preference.is_channel_enabled('push'))
        
        # Test channels for payment preference
        self.assertTrue(self.payment_preference.is_channel_enabled('email'))
        self.assertTrue(self.payment_preference.is_channel_enabled('sms'))
        self.assertTrue(self.payment_preference.is_channel_enabled('push'))
        
        # Test with an unsupported channel
        with self.assertRaises(ValueError):
            self.booking_preference.is_channel_enabled('unsupported_channel')


class NotificationViewTests(TravelGuideBaseTestCase):
    """
    Tests for the views in the notifications app.
    
    These tests verify that the views render the correct templates,
    contain the expected context data, and handle user interactions correctly.
    Each test focuses on a specific view or aspect of view functionality.
    """
    
    def setUp(self):
        """
        Set up test data for notification view tests.
        
        Extends the base setUp method to include notifications for testing.
        """
        super().setUp()
        
        # Create notifications for the test user
        self.notification1 = Notification.objects.create(
            user=self.test_user,
            title="Tour Booking Confirmed",
            message="Your tour booking has been confirmed.",
            notification_type="booking_confirmation",
            is_read=False,
            created_at=timezone.now() - datetime.timedelta(days=1)
        )
        
        self.notification2 = Notification.objects.create(
            user=self.test_user,
            title="Payment Received",
            message="We have received your payment.",
            notification_type="payment_confirmation",
            is_read=False,
            created_at=timezone.now()
        )
        
        # Create a read notification
        self.read_notification = Notification.objects.create(
            user=self.test_user,
            title="Welcome to TravelGuide",
            message="Thank you for joining our platform.",
            notification_type="welcome",
            is_read=True,
            created_at=timezone.now() - datetime.timedelta(days=7),
            read_at=timezone.now() - datetime.timedelta(days=6)
        )
        
        # Log in the test user
        self.login_test_user()
    
    def test_notification_list_view(self):
        """
        Test the notification list view.
        
        Verifies that the notification list view returns a 200 status code,
        uses the correct template, and includes the user's notifications in the context.
        """
        response = self.client.get(reverse('notifications:notification_list'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'notifications/notification_list.html')
        
        # Check that the notifications are in the context
        self.assertIn('notifications', response.context)
        self.assertEqual(len(response.context['notifications']), 3)
        
        # Check that the unread count is correct
        self.assertIn('unread_count', response.context)
        self.assertEqual(response.context['unread_count'], 2)
        
    def test_notification_detail_view(self):
        """
        Test the notification detail view.
        
        Verifies that the notification detail view returns a 200 status code,
        uses the correct template, includes the notification in the context,
        and marks the notification as read.
        """
        response = self.client.get(reverse('notifications:notification_detail', kwargs={'pk': self.notification1.pk}))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'notifications/notification_detail.html')
        
        # Check that the notification is in the context
        self.assertEqual(response.context['notification'], self.notification1)
        
        # Check that the notification is marked as read
        self.notification1.refresh_from_db()
        self.assertTrue(self.notification1.is_read)
        self.assertIsNotNone(self.notification1.read_at)
        
    def test_mark_notification_as_read_view(self):
        """
        Test the mark notification as read view.
        
        Verifies that the mark notification as read view correctly marks
        a notification as read and redirects appropriately.
        """
        response = self.client.post(reverse('notifications:mark_as_read', kwargs={'pk': self.notification2.pk}))
        
        # Check that the response is a redirect
        self.assertEqual(response.status_code, 302)
        
        # Check that the notification is marked as read
        self.notification2.refresh_from_db()
        self.assertTrue(self.notification2.is_read)
        self.assertIsNotNone(self.notification2.read_at)
        
    def test_mark_all_as_read_view(self):
        """
        Test the mark all notifications as read view.
        
        Verifies that the mark all as read view correctly marks all
        of a user's unread notifications as read and redirects appropriately.
        """
        # Create another unread notification
        Notification.objects.create(
            user=self.test_user,
            title="New Tour Available",
            message="A new tour is now available for booking.",
            notification_type="new_tour",
            is_read=False,
            created_at=timezone.now()
        )
        
        # Count unread notifications before
        unread_count_before = Notification.objects.filter(user=self.test_user, is_read=False).count()
        self.assertEqual(unread_count_before, 3)
        
        # Mark all as read
        response = self.client.post(reverse('notifications:mark_all_as_read'))
        
        # Check that the response is a redirect
        self.assertEqual(response.status_code, 302)
        
        # Count unread notifications after
        unread_count_after = Notification.objects.filter(user=self.test_user, is_read=False).count()
        self.assertEqual(unread_count_after, 0)
        
    def test_notification_preferences_view(self):
        """
        Test the notification preferences view.
        
        Verifies that the notification preferences view returns a 200 status code,
        uses the correct template, and includes the user's notification preferences
        in the context.
        """
        # Create notification types
        booking_type = NotificationType.objects.create(
            code="booking_confirmation",
            name="Booking Confirmation",
            description="Sent when a booking is confirmed",
            email_template="emails/booking_confirmation.html",
            sms_template="Your booking #{booking_number} has been confirmed."
        )
        
        payment_type = NotificationType.objects.create(
            code="payment_confirmation",
            name="Payment Confirmation",
            description="Sent when a payment is received",
            email_template="emails/payment_confirmation.html",
            sms_template="Your payment of ${amount} for booking #{booking_number} has been received."
        )
        
        # Create notification preferences for the test user
        NotificationPreference.objects.create(
            user=self.test_user,
            notification_type=booking_type,
            email_enabled=True,
            sms_enabled=False,
            push_enabled=True
        )
        
        NotificationPreference.objects.create(
            user=self.test_user,
            notification_type=payment_type,
            email_enabled=True,
            sms_enabled=True,
            push_enabled=True
        )
        
        # Get the notification preferences page
        response = self.client.get(reverse('notifications:preferences'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'notifications/preferences.html')
        
        # Check that the preferences are in the context
        self.assertIn('preferences', response.context)
        self.assertEqual(len(response.context['preferences']), 2)
        
    def test_update_notification_preferences_view(self):
        """
        Test the update notification preferences view.
        
        Verifies that the update notification preferences view correctly updates
        a user's notification preferences and redirects appropriately.
        """
        # Create notification types
        booking_type = NotificationType.objects.create(
            code="booking_confirmation",
            name="Booking Confirmation",
            description="Sent when a booking is confirmed",
            email_template="emails/booking_confirmation.html",
            sms_template="Your booking #{booking_number} has been confirmed."
        )
        
        # Create notification preference for the test user
        preference = NotificationPreference.objects.create(
            user=self.test_user,
            notification_type=booking_type,
            email_enabled=True,
            sms_enabled=False,
            push_enabled=True
        )
        
        # Update the preference
        response = self.client.post(reverse('notifications:update_preference', kwargs={'pk': preference.pk}), {
            'email_enabled': 'false',
            'sms_enabled': 'true',
            'push_enabled': 'false'
        })
        
        # Check that the response is a redirect
        self.assertEqual(response.status_code, 302)
        
        # Check that the preference was updated
        preference.refresh_from_db()
        self.assertFalse(preference.email_enabled)
        self.assertTrue(preference.sms_enabled)
        self.assertFalse(preference.push_enabled)
