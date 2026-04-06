"""
Test cases for the core app API endpoints.

This module contains comprehensive test cases for all API endpoints
in the core app. Every test function is thoroughly documented
to make understanding the tests easier for programmers.
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
import json

from core.models import SiteSettings, FAQ, Testimonial, ContactMessage, Newsletter
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class SiteSettingsAPITests(TravelGuideBaseTestCase):
    """
    Tests for the SiteSettings API endpoints.
    
    These tests verify that the API endpoints for site settings work correctly,
    including authentication, permissions, and data retrieval.
    """
    
    def setUp(self):
        """
        Set up test data for SiteSettings API tests.
        
        Extends the base setUp method to include site settings for testing.
        """
        super().setUp()
        
        # Create site settings
        self.site_settings = SiteSettings.objects.create(
            site_name="TravelGuide",
            tagline="Discover the world with us",
            description="A travel guide platform for adventurers",
            contact_email="contact@travelguide.com",
            contact_phone="+1234567890",
            address="123 Travel St, Adventure City, AC 12345",
            facebook_url="https://facebook.com/travelguide",
            twitter_url="https://twitter.com/travelguide",
            instagram_url="https://instagram.com/travelguide"
        )
        
        # URL for testing
        self.api_site_settings_url = reverse('api:site-settings')
    
    def test_site_settings_api_get(self):
        """
        Test retrieving site settings via the API.
        
        Verifies that the API returns the correct site settings data
        and that it is accessible to anonymous users.
        """
        response = self.client.get(self.api_site_settings_url)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['site_name'], "TravelGuide")
        self.assertEqual(data['tagline'], "Discover the world with us")
        self.assertEqual(data['contact_email'], "contact@travelguide.com")
        
    def test_site_settings_api_update_anonymous(self):
        """
        Test that anonymous users cannot update site settings.
        
        Verifies that attempting to update site settings as an anonymous user
        returns an authentication error.
        """
        update_data = {'site_name': 'Updated TravelGuide'}
        response = self.client.patch(
            self.api_site_settings_url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)  # Unauthorized
        
    def test_site_settings_api_update_non_admin(self):
        """
        Test that non-admin users cannot update site settings.
        
        Verifies that attempting to update site settings as a non-admin user
        returns a permission error.
        """
        self.client.login(username='testuser', password='password')
        
        update_data = {'site_name': 'Updated TravelGuide'}
        response = self.client.patch(
            self.api_site_settings_url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)  # Forbidden
        
    def test_site_settings_api_update_admin(self):
        """
        Test that admin users can update site settings.
        
        Verifies that an admin user can update site settings via the API
        and that the changes are saved to the database.
        """
        self.client.login(username='admin', password='password')
        
        update_data = {
            'site_name': 'Updated TravelGuide',
            'tagline': 'New tagline'
        }
        
        response = self.client.patch(
            self.api_site_settings_url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['site_name'], 'Updated TravelGuide')
        self.assertEqual(data['tagline'], 'New tagline')
        
        # Verify that the database was updated
        self.site_settings.refresh_from_db()
        self.assertEqual(self.site_settings.site_name, 'Updated TravelGuide')
        self.assertEqual(self.site_settings.tagline, 'New tagline')


class FAQAPITests(TravelGuideBaseTestCase):
    """
    Tests for the FAQ API endpoints.
    
    These tests verify that the API endpoints for FAQs work correctly,
    including authentication, permissions, and data manipulation.
    """
    
    def setUp(self):
        """
        Set up test data for FAQ API tests.
        
        Extends the base setUp method to include FAQs for testing.
        """
        super().setUp()
        
        # Create FAQs
        self.faq1 = FAQ.objects.create(
            question="What is TravelGuide?",
            answer="TravelGuide is a platform for travel enthusiasts.",
            order=1,
            is_published=True
        )
        
        self.faq2 = FAQ.objects.create(
            question="How do I book a tour?",
            answer="You can book a tour by visiting the tour page and clicking 'Book Now'.",
            order=2,
            is_published=True
        )
        
        self.faq3 = FAQ.objects.create(
            question="Unpublished FAQ",
            answer="This FAQ is not published.",
            order=3,
            is_published=False
        )
        
        # URLs for testing
        self.api_faq_list_url = reverse('api:faqs-list')
        self.api_faq_detail_url = reverse('api:faqs-detail', kwargs={'pk': self.faq1.pk})
    
    def test_faq_list_api(self):
        """
        Test the FAQ list API endpoint.
        
        Verifies that the endpoint returns a list of published FAQs
        in the correct order.
        """
        response = self.client.get(self.api_faq_list_url)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(len(data), 2)  # Only published FAQs
        self.assertEqual(data[0]['question'], "What is TravelGuide?")
        self.assertEqual(data[1]['question'], "How do I book a tour?")
        
    def test_faq_detail_api(self):
        """
        Test the FAQ detail API endpoint.
        
        Verifies that the endpoint returns the details of a specific FAQ.
        """
        response = self.client.get(self.api_faq_detail_url)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['question'], "What is TravelGuide?")
        self.assertEqual(data['answer'], "TravelGuide is a platform for travel enthusiasts.")
        
    def test_faq_create_api_anonymous(self):
        """
        Test that anonymous users cannot create FAQs.
        
        Verifies that attempting to create an FAQ as an anonymous user
        returns an authentication error.
        """
        new_faq_data = {
            'question': 'New FAQ Question',
            'answer': 'New FAQ Answer',
            'order': 4,
            'is_published': True
        }
        
        response = self.client.post(
            self.api_faq_list_url,
            data=json.dumps(new_faq_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)  # Unauthorized
        
    def test_faq_create_api_non_admin(self):
        """
        Test that non-admin users cannot create FAQs.
        
        Verifies that attempting to create an FAQ as a non-admin user
        returns a permission error.
        """
        self.client.login(username='testuser', password='password')
        
        new_faq_data = {
            'question': 'New FAQ Question',
            'answer': 'New FAQ Answer',
            'order': 4,
            'is_published': True
        }
        
        response = self.client.post(
            self.api_faq_list_url,
            data=json.dumps(new_faq_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)  # Forbidden
        
    def test_faq_create_api_admin(self):
        """
        Test that admin users can create FAQs.
        
        Verifies that an admin user can create a new FAQ via the API
        and that it is saved to the database.
        """
        self.client.login(username='admin', password='password')
        
        new_faq_data = {
            'question': 'New FAQ Question',
            'answer': 'New FAQ Answer',
            'order': 4,
            'is_published': True
        }
        
        response = self.client.post(
            self.api_faq_list_url,
            data=json.dumps(new_faq_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)  # Created
        
        data = json.loads(response.content)
        self.assertEqual(data['question'], 'New FAQ Question')
        self.assertEqual(data['answer'], 'New FAQ Answer')
        
        # Verify that the FAQ was created in the database
        self.assertTrue(FAQ.objects.filter(question='New FAQ Question').exists())
        
    def test_faq_update_api_admin(self):
        """
        Test that admin users can update FAQs.
        
        Verifies that an admin user can update an existing FAQ via the API
        and that the changes are saved to the database.
        """
        self.client.login(username='admin', password='password')
        
        update_data = {
            'question': 'Updated FAQ Question',
            'answer': 'Updated FAQ Answer'
        }
        
        response = self.client.patch(
            self.api_faq_detail_url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['question'], 'Updated FAQ Question')
        self.assertEqual(data['answer'], 'Updated FAQ Answer')
        
        # Verify that the database was updated
        self.faq1.refresh_from_db()
        self.assertEqual(self.faq1.question, 'Updated FAQ Question')
        self.assertEqual(self.faq1.answer, 'Updated FAQ Answer')
        
    def test_faq_delete_api_admin(self):
        """
        Test that admin users can delete FAQs.
        
        Verifies that an admin user can delete an FAQ via the API
        and that it is removed from the database.
        """
        self.client.login(username='admin', password='password')
        
        response = self.client.delete(self.api_faq_detail_url)
        self.assertEqual(response.status_code, 204)  # No Content
        
        # Verify that the FAQ was deleted from the database
        self.assertFalse(FAQ.objects.filter(pk=self.faq1.pk).exists())


class TestimonialAPITests(TravelGuideBaseTestCase):
    """
    Tests for the Testimonial API endpoints.
    
    These tests verify that the API endpoints for testimonials work correctly,
    including authentication, permissions, and data manipulation.
    """
    
    def setUp(self):
        """
        Set up test data for Testimonial API tests.
        
        Extends the base setUp method to include testimonials for testing.
        """
        super().setUp()
        
        # Create testimonials
        self.testimonial1 = Testimonial.objects.create(
            name="John Doe",
            content="TravelGuide made my vacation amazing!",
            rating=5,
            is_published=True,
            is_featured=True
        )
        
        self.testimonial2 = Testimonial.objects.create(
            name="Jane Smith",
            content="Great service and support.",
            rating=4,
            is_published=True,
            is_featured=False
        )
        
        self.testimonial3 = Testimonial.objects.create(
            name="Unpublished Testimonial",
            content="This testimonial is not published.",
            rating=3,
            is_published=False,
            is_featured=False
        )
        
        # URLs for testing
        self.api_testimonial_list_url = reverse('api:testimonials-list')
        self.api_testimonial_detail_url = reverse('api:testimonials-detail', kwargs={'pk': self.testimonial1.pk})
        self.api_testimonial_featured_url = reverse('api:testimonials-featured')
    
    def test_testimonial_list_api(self):
        """
        Test the testimonial list API endpoint.
        
        Verifies that the endpoint returns a list of published testimonials.
        """
        response = self.client.get(self.api_testimonial_list_url)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(len(data), 2)  # Only published testimonials
        testimonial_names = [item['name'] for item in data]
        self.assertIn("John Doe", testimonial_names)
        self.assertIn("Jane Smith", testimonial_names)
        
    def test_testimonial_featured_api(self):
        """
        Test the featured testimonials API endpoint.
        
        Verifies that the endpoint returns only featured and published testimonials.
        """
        response = self.client.get(self.api_testimonial_featured_url)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)  # Only featured and published testimonials
        self.assertEqual(data[0]['name'], "John Doe")
        
    def test_testimonial_detail_api(self):
        """
        Test the testimonial detail API endpoint.
        
        Verifies that the endpoint returns the details of a specific testimonial.
        """
        response = self.client.get(self.api_testimonial_detail_url)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['name'], "John Doe")
        self.assertEqual(data['content'], "TravelGuide made my vacation amazing!")
        self.assertEqual(data['rating'], 5)
        
    def test_testimonial_create_api_anonymous(self):
        """
        Test that anonymous users can create testimonials.
        
        Verifies that anonymous users can submit testimonials via the API,
        but they are marked as unpublished by default.
        """
        new_testimonial_data = {
            'name': 'Anonymous User',
            'content': 'Great experience with TravelGuide!',
            'rating': 5
        }
        
        response = self.client.post(
            self.api_testimonial_list_url,
            data=json.dumps(new_testimonial_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)  # Created
        
        data = json.loads(response.content)
        self.assertEqual(data['name'], 'Anonymous User')
        self.assertEqual(data['content'], 'Great experience with TravelGuide!')
        self.assertEqual(data['rating'], 5)
        self.assertFalse(data['is_published'])  # Should be unpublished by default
        self.assertFalse(data['is_featured'])   # Should not be featured by default
        
        # Verify that the testimonial was created in the database
        self.assertTrue(Testimonial.objects.filter(name='Anonymous User').exists())
        
    def test_testimonial_update_api_admin(self):
        """
        Test that admin users can update testimonials.
        
        Verifies that an admin user can update an existing testimonial via the API
        and that the changes are saved to the database.
        """
        self.client.login(username='admin', password='password')
        
        update_data = {
            'name': 'Updated Name',
            'content': 'Updated content',
            'is_published': True,
            'is_featured': True
        }
        
        response = self.client.patch(
            self.api_testimonial_detail_url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['name'], 'Updated Name')
        self.assertEqual(data['content'], 'Updated content')
        self.assertTrue(data['is_published'])
        self.assertTrue(data['is_featured'])
        
        # Verify that the database was updated
        self.testimonial1.refresh_from_db()
        self.assertEqual(self.testimonial1.name, 'Updated Name')
        self.assertEqual(self.testimonial1.content, 'Updated content')
        self.assertTrue(self.testimonial1.is_published)
        self.assertTrue(self.testimonial1.is_featured)
        
    def test_testimonial_delete_api_admin(self):
        """
        Test that admin users can delete testimonials.
        
        Verifies that an admin user can delete a testimonial via the API
        and that it is removed from the database.
        """
        self.client.login(username='admin', password='password')
        
        response = self.client.delete(self.api_testimonial_detail_url)
        self.assertEqual(response.status_code, 204)  # No Content
        
        # Verify that the testimonial was deleted from the database
        self.assertFalse(Testimonial.objects.filter(pk=self.testimonial1.pk).exists())


class ContactMessageAPITests(TravelGuideBaseTestCase):
    """
    Tests for the ContactMessage API endpoints.
    
    These tests verify that the API endpoints for contact messages work correctly,
    including authentication, permissions, and data manipulation.
    """
    
    def setUp(self):
        """
        Set up test data for ContactMessage API tests.
        
        Extends the base setUp method to include contact messages for testing.
        """
        super().setUp()
        
        # Create contact messages
        self.message1 = ContactMessage.objects.create(
            name="John Doe",
            email="john@example.com",
            subject="Inquiry",
            message="I have a question about tours.",
            is_read=False
        )
        
        self.message2 = ContactMessage.objects.create(
            name="Jane Smith",
            email="jane@example.com",
            subject="Feedback",
            message="Great website!",
            is_read=True
        )
        
        # URLs for testing
        self.api_contact_message_list_url = reverse('api:contact-messages-list')
        self.api_contact_message_detail_url = reverse('api:contact-messages-detail', kwargs={'pk': self.message1.pk})
        self.api_contact_message_create_url = reverse('api:contact-message-create')
    
    def test_contact_message_create_api(self):
        """
        Test creating a contact message via the API.
        
        Verifies that anonymous users can submit contact messages via the API
        and that they are saved to the database.
        """
        new_message_data = {
            'name': 'New User',
            'email': 'newuser@example.com',
            'subject': 'API Test',
            'message': 'Testing the contact message API.'
        }
        
        response = self.client.post(
            self.api_contact_message_create_url,
            data=json.dumps(new_message_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)  # Created
        
        data = json.loads(response.content)
        self.assertEqual(data['name'], 'New User')
        self.assertEqual(data['email'], 'newuser@example.com')
        self.assertEqual(data['subject'], 'API Test')
        self.assertEqual(data['message'], 'Testing the contact message API.')
        self.assertFalse(data['is_read'])  # Should be unread by default
        
        # Verify that the message was created in the database
        self.assertTrue(ContactMessage.objects.filter(email='newuser@example.com').exists())
        
    def test_contact_message_list_api_anonymous(self):
        """
        Test that anonymous users cannot access the contact message list.
        
        Verifies that attempting to access the contact message list as an anonymous user
        returns an authentication error.
        """
        response = self.client.get(self.api_contact_message_list_url)
        self.assertEqual(response.status_code, 401)  # Unauthorized
        
    def test_contact_message_list_api_non_admin(self):
        """
        Test that non-admin users cannot access the contact message list.
        
        Verifies that attempting to access the contact message list as a non-admin user
        returns a permission error.
        """
        self.client.login(username='testuser', password='password')
        
        response = self.client.get(self.api_contact_message_list_url)
        self.assertEqual(response.status_code, 403)  # Forbidden
        
    def test_contact_message_list_api_admin(self):
        """
        Test that admin users can access the contact message list.
        
        Verifies that an admin user can access the contact message list via the API
        and that it returns the correct data.
        """
        self.client.login(username='admin', password='password')
        
        response = self.client.get(self.api_contact_message_list_url)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(len(data), 2)
        message_subjects = [item['subject'] for item in data]
        self.assertIn("Inquiry", message_subjects)
        self.assertIn("Feedback", message_subjects)
        
    def test_contact_message_mark_as_read_api(self):
        """
        Test marking a contact message as read via the API.
        
        Verifies that an admin user can mark a contact message as read via the API
        and that the changes are saved to the database.
        """
        self.client.login(username='admin', password='password')
        
        mark_as_read_url = reverse('api:contact-messages-mark-read', kwargs={'pk': self.message1.pk})
        
        response = self.client.post(mark_as_read_url)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['is_read'])
        
        # Verify that the database was updated
        self.message1.refresh_from_db()
        self.assertTrue(self.message1.is_read)


class NewsletterAPITests(TravelGuideBaseTestCase):
    """
    Tests for the Newsletter API endpoints.
    
    These tests verify that the API endpoints for newsletter subscriptions work correctly,
    including authentication, permissions, and data manipulation.
    """
    
    def setUp(self):
        """
        Set up test data for Newsletter API tests.
        
        Extends the base setUp method to include newsletter subscriptions for testing.
        """
        super().setUp()
        
        # Create newsletter subscriptions
        self.subscription1 = Newsletter.objects.create(
            email="subscriber1@example.com",
            is_active=True
        )
        
        self.subscription2 = Newsletter.objects.create(
            email="subscriber2@example.com",
            is_active=True
        )
        
        self.inactive_subscription = Newsletter.objects.create(
            email="inactive@example.com",
            is_active=False
        )
        
        # URLs for testing
        self.api_newsletter_subscribe_url = reverse('api:newsletter-subscribe')
        self.api_newsletter_unsubscribe_url = reverse('api:newsletter-unsubscribe')
        self.api_newsletter_list_url = reverse('api:newsletter-list')
    
    def test_newsletter_subscribe_api(self):
        """
        Test subscribing to the newsletter via the API.
        
        Verifies that users can subscribe to the newsletter via the API
        and that the subscription is saved to the database.
        """
        subscribe_data = {
            'email': 'newsubscriber@example.com'
        }
        
        response = self.client.post(
            self.api_newsletter_subscribe_url,
            data=json.dumps(subscribe_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)  # Created
        
        data = json.loads(response.content)
        self.assertEqual(data['email'], 'newsubscriber@example.com')
        self.assertTrue(data['is_active'])
        
        # Verify that the subscription was created in the database
        self.assertTrue(Newsletter.objects.filter(email='newsubscriber@example.com').exists())
        
    def test_newsletter_subscribe_duplicate_api(self):
        """
        Test subscribing with an already subscribed email.
        
        Verifies that attempting to subscribe with an email that is already subscribed
        returns an appropriate error message.
        """
        subscribe_data = {
            'email': 'subscriber1@example.com'  # Already subscribed
        }
        
        response = self.client.post(
            self.api_newsletter_subscribe_url,
            data=json.dumps(subscribe_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)  # Bad Request
        
        data = json.loads(response.content)
        self.assertIn('error', data)
        
    def test_newsletter_unsubscribe_api(self):
        """
        Test unsubscribing from the newsletter via the API.
        
        Verifies that users can unsubscribe from the newsletter via the API
        and that the subscription is marked as inactive in the database.
        """
        unsubscribe_data = {
            'email': 'subscriber1@example.com'
        }
        
        response = self.client.post(
            self.api_newsletter_unsubscribe_url,
            data=json.dumps(unsubscribe_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['email'], 'subscriber1@example.com')
        self.assertFalse(data['is_active'])
        
        # Verify that the subscription was marked as inactive in the database
        self.subscription1.refresh_from_db()
        self.assertFalse(self.subscription1.is_active)
        
    def test_newsletter_unsubscribe_invalid_email_api(self):
        """
        Test unsubscribing with an invalid email.
        
        Verifies that attempting to unsubscribe with an email that is not subscribed
        returns an appropriate error message.
        """
        unsubscribe_data = {
            'email': 'notsubscribed@example.com'
        }
        
        response = self.client.post(
            self.api_newsletter_unsubscribe_url,
            data=json.dumps(unsubscribe_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)  # Not Found
        
        data = json.loads(response.content)
        self.assertIn('error', data)
        
    def test_newsletter_list_api_anonymous(self):
        """
        Test that anonymous users cannot access the newsletter list.
        
        Verifies that attempting to access the newsletter list as an anonymous user
        returns an authentication error.
        """
        response = self.client.get(self.api_newsletter_list_url)
        self.assertEqual(response.status_code, 401)  # Unauthorized
        
    def test_newsletter_list_api_non_admin(self):
        """
        Test that non-admin users cannot access the newsletter list.
        
        Verifies that attempting to access the newsletter list as a non-admin user
        returns a permission error.
        """
        self.client.login(username='testuser', password='password')
        
        response = self.client.get(self.api_newsletter_list_url)
        self.assertEqual(response.status_code, 403)  # Forbidden
        
    def test_newsletter_list_api_admin(self):
        """
        Test that admin users can access the newsletter list.
        
        Verifies that an admin user can access the newsletter list via the API
        and that it returns the correct data.
        """
        self.client.login(username='admin', password='password')
        
        response = self.client.get(self.api_newsletter_list_url)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(len(data), 3)  # All subscriptions, active and inactive
        
        # Verify that we can filter for active subscriptions
        response = self.client.get(f"{self.api_newsletter_list_url}?active=true")
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(len(data), 2)  # Only active subscriptions
        emails = [item['email'] for item in data]
        self.assertIn("subscriber1@example.com", emails)
        self.assertIn("subscriber2@example.com", emails)
        self.assertNotIn("inactive@example.com", emails)
