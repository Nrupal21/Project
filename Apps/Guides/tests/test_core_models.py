"""
Test cases for the core app models.

This module contains comprehensive test cases for all models
in the core app. Every test function is thoroughly documented
to make understanding the tests easier for programmers.
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
import datetime
import os

from core.models import SiteSettings, FAQ, Testimonial, ContactMessage, Newsletter
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class SiteSettingsModelTests(TravelGuideBaseTestCase):
    """
    Tests for the SiteSettings model in the core app.
    
    These tests verify that SiteSettings objects can be created correctly,
    and that their methods work as expected. Each test focuses on a 
    specific aspect of the SiteSettings model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for SiteSettings tests.
        
        Extends the base setUp method to include site settings for testing.
        """
        super().setUp()
        
        # Create site settings
        self.site_settings = SiteSettings.objects.create(
            site_name="Travel Guide",
            site_description="Your ultimate travel companion",
            contact_email="contact@travelguide.com",
            phone_number="+1234567890",
            address="123 Travel Street, Tourism City",
            facebook_url="https://facebook.com/travelguide",
            twitter_url="https://twitter.com/travelguide",
            instagram_url="https://instagram.com/travelguide",
            google_analytics_id="UA-12345678-9",
            footer_text="© 2025 Travel Guide. All rights reserved."
        )
    
    def test_site_settings_creation(self):
        """
        Test that a SiteSettings object can be created with the expected attributes.
        
        Verifies that the SiteSettings model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Verify the site settings were created with the correct attributes
        self.assertEqual(self.site_settings.site_name, "Travel Guide")
        self.assertEqual(self.site_settings.site_description, "Your ultimate travel companion")
        self.assertEqual(self.site_settings.contact_email, "contact@travelguide.com")
        self.assertEqual(self.site_settings.phone_number, "+1234567890")
        self.assertEqual(self.site_settings.address, "123 Travel Street, Tourism City")
        self.assertEqual(self.site_settings.facebook_url, "https://facebook.com/travelguide")
        self.assertEqual(self.site_settings.twitter_url, "https://twitter.com/travelguide")
        self.assertEqual(self.site_settings.instagram_url, "https://instagram.com/travelguide")
        self.assertEqual(self.site_settings.google_analytics_id, "UA-12345678-9")
        self.assertEqual(self.site_settings.footer_text, "© 2025 Travel Guide. All rights reserved.")
        
    def test_site_settings_str_method(self):
        """
        Test the string representation of a SiteSettings object.
        
        Verifies that the __str__ method returns the expected string,
        which should be the site name.
        """
        self.assertEqual(str(self.site_settings), "Travel Guide")
        
    def test_site_settings_singleton(self):
        """
        Test that SiteSettings enforces a singleton pattern.
        
        Verifies that only one SiteSettings object can exist in the database,
        and that creating a new one updates the existing one.
        """
        # Count the number of SiteSettings objects
        initial_count = SiteSettings.objects.count()
        self.assertEqual(initial_count, 1)
        
        # Try to create another SiteSettings object
        new_settings = SiteSettings.objects.create(
            site_name="New Travel Guide",
            site_description="New description",
            contact_email="new@travelguide.com"
        )
        
        # The count should still be 1
        self.assertEqual(SiteSettings.objects.count(), 1)
        
        # The existing object should be updated
        updated_settings = SiteSettings.objects.first()
        self.assertEqual(updated_settings.site_name, "New Travel Guide")
        self.assertEqual(updated_settings.site_description, "New description")
        self.assertEqual(updated_settings.contact_email, "new@travelguide.com")
        
        # The other fields should remain unchanged
        self.assertEqual(updated_settings.phone_number, "+1234567890")
        self.assertEqual(updated_settings.address, "123 Travel Street, Tourism City")


class FAQModelTests(TravelGuideBaseTestCase):
    """
    Tests for the FAQ model in the core app.
    
    These tests verify that FAQ objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the FAQ model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for FAQ tests.
        
        Extends the base setUp method to include FAQs for testing.
        """
        super().setUp()
        
        # Create some FAQs
        self.faq1 = FAQ.objects.create(
            question="What payment methods do you accept?",
            answer="We accept all major credit cards, PayPal, and bank transfers.",
            order=1,
            is_published=True
        )
        
        self.faq2 = FAQ.objects.create(
            question="How can I cancel my booking?",
            answer="You can cancel your booking through your account dashboard up to 48 hours before the tour starts.",
            order=2,
            is_published=True
        )
        
        self.faq3 = FAQ.objects.create(
            question="Do you offer refunds?",
            answer="Yes, we offer full refunds for cancellations made at least 48 hours in advance.",
            order=3,
            is_published=False  # This one is not published
        )
    
    def test_faq_creation(self):
        """
        Test that an FAQ can be created with the expected attributes.
        
        Verifies that the FAQ model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new FAQ
        faq = FAQ.objects.create(
            question="Are meals included in the tours?",
            answer="It depends on the specific tour. Please check the tour details for meal information.",
            order=4,
            is_published=True
        )
        
        # Verify the FAQ was created with the correct attributes
        self.assertEqual(faq.question, "Are meals included in the tours?")
        self.assertEqual(faq.answer, "It depends on the specific tour. Please check the tour details for meal information.")
        self.assertEqual(faq.order, 4)
        self.assertTrue(faq.is_published)
        
    def test_faq_str_method(self):
        """
        Test the string representation of an FAQ object.
        
        Verifies that the __str__ method returns the expected string,
        which should be the question.
        """
        self.assertEqual(str(self.faq1), "What payment methods do you accept?")
        
    def test_faq_ordering(self):
        """
        Test that FAQs are ordered correctly.
        
        Verifies that FAQs are returned in the order specified by the order field.
        """
        # Get all FAQs
        faqs = FAQ.objects.all()
        
        # Check that they are in the correct order
        self.assertEqual(faqs[0], self.faq1)  # order=1
        self.assertEqual(faqs[1], self.faq2)  # order=2
        self.assertEqual(faqs[2], self.faq3)  # order=3
        
    def test_published_faqs(self):
        """
        Test the published manager method.
        
        Verifies that the published() manager method returns only published FAQs.
        """
        # Get published FAQs
        published_faqs = FAQ.objects.filter(is_published=True)
        
        # Check that only published FAQs are returned
        self.assertEqual(published_faqs.count(), 2)
        self.assertIn(self.faq1, published_faqs)
        self.assertIn(self.faq2, published_faqs)
        self.assertNotIn(self.faq3, published_faqs)  # This one is not published


class TestimonialModelTests(TravelGuideBaseTestCase):
    """
    Tests for the Testimonial model in the core app.
    
    These tests verify that Testimonial objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the Testimonial model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for Testimonial tests.
        
        Extends the base setUp method to include testimonials for testing.
        """
        super().setUp()
        
        # Create a test image file
        self.test_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'',  # Empty content for testing
            content_type='image/jpeg'
        )
        
        # Create some testimonials
        self.testimonial1 = Testimonial.objects.create(
            name="John Doe",
            title="Adventure Seeker",
            content="The best travel experience I've ever had!",
            rating=5,
            is_featured=True,
            is_published=True
        )
        
        self.testimonial2 = Testimonial.objects.create(
            name="Jane Smith",
            title="Family Traveler",
            content="Our family had an amazing time on the Tokyo tour.",
            rating=4,
            is_featured=False,
            is_published=True
        )
        
        self.testimonial3 = Testimonial.objects.create(
            name="Bob Johnson",
            title="Business Traveler",
            content="The tour was well-organized and informative.",
            rating=5,
            is_featured=True,
            is_published=False  # This one is not published
        )
    
    def test_testimonial_creation(self):
        """
        Test that a Testimonial can be created with the expected attributes.
        
        Verifies that the Testimonial model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new testimonial
        testimonial = Testimonial.objects.create(
            name="Alice Brown",
            title="Solo Traveler",
            content="I felt safe and had a great time exploring new places.",
            rating=4,
            is_featured=False,
            is_published=True,
            image=self.test_image
        )
        
        # Verify the testimonial was created with the correct attributes
        self.assertEqual(testimonial.name, "Alice Brown")
        self.assertEqual(testimonial.title, "Solo Traveler")
        self.assertEqual(testimonial.content, "I felt safe and had a great time exploring new places.")
        self.assertEqual(testimonial.rating, 4)
        self.assertFalse(testimonial.is_featured)
        self.assertTrue(testimonial.is_published)
        self.assertIsNotNone(testimonial.image)
        
        # Clean up the test image
        if testimonial.image:
            if os.path.isfile(testimonial.image.path):
                os.remove(testimonial.image.path)
        
    def test_testimonial_str_method(self):
        """
        Test the string representation of a Testimonial object.
        
        Verifies that the __str__ method returns the expected string,
        which should be the name of the person giving the testimonial.
        """
        self.assertEqual(str(self.testimonial1), "John Doe")
        
    def test_testimonial_published_manager(self):
        """
        Test the published manager method.
        
        Verifies that the published() manager method returns only published testimonials.
        """
        # Get published testimonials
        published_testimonials = Testimonial.objects.filter(is_published=True)
        
        # Check that only published testimonials are returned
        self.assertEqual(published_testimonials.count(), 2)
        self.assertIn(self.testimonial1, published_testimonials)
        self.assertIn(self.testimonial2, published_testimonials)
        self.assertNotIn(self.testimonial3, published_testimonials)  # This one is not published
        
    def test_testimonial_featured_manager(self):
        """
        Test the featured manager method.
        
        Verifies that the featured() manager method returns only featured testimonials.
        """
        # Get featured testimonials
        featured_testimonials = Testimonial.objects.filter(is_featured=True)
        
        # Check that only featured testimonials are returned
        self.assertEqual(featured_testimonials.count(), 2)
        self.assertIn(self.testimonial1, featured_testimonials)
        self.assertIn(self.testimonial3, featured_testimonials)
        self.assertNotIn(self.testimonial2, featured_testimonials)  # This one is not featured
        
    def test_testimonial_featured_and_published(self):
        """
        Test filtering for testimonials that are both featured and published.
        
        Verifies that we can correctly filter for testimonials that are both
        featured and published.
        """
        # Get testimonials that are both featured and published
        featured_published = Testimonial.objects.filter(is_featured=True, is_published=True)
        
        # Check that only testimonials that are both featured and published are returned
        self.assertEqual(featured_published.count(), 1)
        self.assertIn(self.testimonial1, featured_published)
        self.assertNotIn(self.testimonial2, featured_published)  # Not featured
        self.assertNotIn(self.testimonial3, featured_published)  # Not published


class ContactMessageModelTests(TravelGuideBaseTestCase):
    """
    Tests for the ContactMessage model in the core app.
    
    These tests verify that ContactMessage objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the ContactMessage model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for ContactMessage tests.
        
        Extends the base setUp method to include contact messages for testing.
        """
        super().setUp()
        
        # Create some contact messages
        self.message1 = ContactMessage.objects.create(
            name="John Doe",
            email="john@example.com",
            subject="Booking Inquiry",
            message="I'm interested in booking the Tokyo tour for next month.",
            is_read=True
        )
        
        self.message2 = ContactMessage.objects.create(
            name="Jane Smith",
            email="jane@example.com",
            subject="Refund Request",
            message="I need to request a refund for my booking.",
            is_read=False
        )
    
    def test_contact_message_creation(self):
        """
        Test that a ContactMessage can be created with the expected attributes.
        
        Verifies that the ContactMessage model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new contact message
        message = ContactMessage.objects.create(
            name="Alice Brown",
            email="alice@example.com",
            subject="Tour Information",
            message="Can you provide more information about the Paris tour?",
            is_read=False
        )
        
        # Verify the message was created with the correct attributes
        self.assertEqual(message.name, "Alice Brown")
        self.assertEqual(message.email, "alice@example.com")
        self.assertEqual(message.subject, "Tour Information")
        self.assertEqual(message.message, "Can you provide more information about the Paris tour?")
        self.assertFalse(message.is_read)
        self.assertIsNotNone(message.created_at)
        
    def test_contact_message_str_method(self):
        """
        Test the string representation of a ContactMessage object.
        
        Verifies that the __str__ method returns the expected string,
        which should include the subject and name.
        """
        expected_str = f"Booking Inquiry from John Doe"
        self.assertEqual(str(self.message1), expected_str)
        
    def test_contact_message_mark_as_read(self):
        """
        Test the mark_as_read method of the ContactMessage model.
        
        Verifies that the mark_as_read method correctly updates the is_read field.
        """
        # Initially, message2 is not read
        self.assertFalse(self.message2.is_read)
        
        # Mark the message as read
        self.message2.is_read = True
        self.message2.save()
        
        # Refresh from the database
        self.message2.refresh_from_db()
        
        # Now it should be marked as read
        self.assertTrue(self.message2.is_read)
        
    def test_contact_message_unread_count(self):
        """
        Test counting unread contact messages.
        
        Verifies that we can correctly count the number of unread messages.
        """
        # Initially, there should be 1 unread message
        unread_count = ContactMessage.objects.filter(is_read=False).count()
        self.assertEqual(unread_count, 1)
        
        # Create another unread message
        ContactMessage.objects.create(
            name="Bob Johnson",
            email="bob@example.com",
            subject="General Question",
            message="What's the best time to visit Tokyo?",
            is_read=False
        )
        
        # Now there should be 2 unread messages
        unread_count = ContactMessage.objects.filter(is_read=False).count()
        self.assertEqual(unread_count, 2)
        
        # Mark one as read
        message = ContactMessage.objects.filter(is_read=False).first()
        message.is_read = True
        message.save()
        
        # Now there should be 1 unread message again
        unread_count = ContactMessage.objects.filter(is_read=False).count()
        self.assertEqual(unread_count, 1)


class NewsletterModelTests(TravelGuideBaseTestCase):
    """
    Tests for the Newsletter model in the core app.
    
    These tests verify that Newsletter objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the Newsletter model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for Newsletter tests.
        
        Extends the base setUp method to include newsletter subscriptions for testing.
        """
        super().setUp()
        
        # Create some newsletter subscriptions
        self.subscription1 = Newsletter.objects.create(
            email="john@example.com",
            is_active=True
        )
        
        self.subscription2 = Newsletter.objects.create(
            email="jane@example.com",
            is_active=True
        )
        
        self.subscription3 = Newsletter.objects.create(
            email="bob@example.com",
            is_active=False  # This one is not active
        )
    
    def test_newsletter_creation(self):
        """
        Test that a Newsletter subscription can be created with the expected attributes.
        
        Verifies that the Newsletter model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new subscription
        subscription = Newsletter.objects.create(
            email="alice@example.com",
            is_active=True
        )
        
        # Verify the subscription was created with the correct attributes
        self.assertEqual(subscription.email, "alice@example.com")
        self.assertTrue(subscription.is_active)
        self.assertIsNotNone(subscription.subscribed_at)
        
    def test_newsletter_str_method(self):
        """
        Test the string representation of a Newsletter object.
        
        Verifies that the __str__ method returns the expected string,
        which should be the email address.
        """
        self.assertEqual(str(self.subscription1), "john@example.com")
        
    def test_newsletter_active_subscriptions(self):
        """
        Test filtering for active newsletter subscriptions.
        
        Verifies that we can correctly filter for subscriptions that are active.
        """
        # Get active subscriptions
        active_subscriptions = Newsletter.objects.filter(is_active=True)
        
        # Check that only active subscriptions are returned
        self.assertEqual(active_subscriptions.count(), 2)
        self.assertIn(self.subscription1, active_subscriptions)
        self.assertIn(self.subscription2, active_subscriptions)
        self.assertNotIn(self.subscription3, active_subscriptions)  # This one is not active
        
    def test_newsletter_unsubscribe(self):
        """
        Test unsubscribing from the newsletter.
        
        Verifies that we can correctly mark a subscription as inactive.
        """
        # Initially, subscription1 is active
        self.assertTrue(self.subscription1.is_active)
        
        # Unsubscribe
        self.subscription1.is_active = False
        self.subscription1.save()
        
        # Refresh from the database
        self.subscription1.refresh_from_db()
        
        # Now it should be inactive
        self.assertFalse(self.subscription1.is_active)
        
        # Check the active subscriptions again
        active_subscriptions = Newsletter.objects.filter(is_active=True)
        self.assertEqual(active_subscriptions.count(), 1)
        self.assertNotIn(self.subscription1, active_subscriptions)
        self.assertIn(self.subscription2, active_subscriptions)
        
    def test_newsletter_email_uniqueness(self):
        """
        Test that email addresses must be unique in the Newsletter model.
        
        Verifies that we cannot create two subscriptions with the same email address.
        """
        # Try to create a subscription with an email that already exists
        with self.assertRaises(Exception):  # Should raise an integrity error
            Newsletter.objects.create(
                email="john@example.com",  # This email already exists
                is_active=True
            )
