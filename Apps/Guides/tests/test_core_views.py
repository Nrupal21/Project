"""
Test cases for the core app views.

This module contains comprehensive test cases for all views
in the core app. Every test function is thoroughly documented
to make understanding the tests easier for programmers.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core import mail
import datetime
import json

from core.models import SiteSettings, FAQ, Testimonial, ContactMessage, Newsletter
from core.forms import ContactForm, NewsletterForm
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class HomeViewTests(TravelGuideBaseTestCase):
    """
    Tests for the home page view in the core app.
    
    These tests verify that the home page displays correctly,
    including featured destinations, tours, and testimonials.
    Each test focuses on a specific aspect of the home page's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for home page tests.
        
        Extends the base setUp method to include additional data for testing.
        """
        super().setUp()
        
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
            is_featured=True,
            is_published=True
        )
        
        # URL for testing
        self.home_url = reverse('core:home')
    
    def test_home_view_status(self):
        """
        Test that the home page loads successfully.
        
        Verifies that the home page returns a 200 OK status code.
        """
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/home.html')
        
    def test_home_view_context(self):
        """
        Test that the home page context contains the expected data.
        
        Verifies that the home page context includes featured destinations,
        tours, and testimonials.
        """
        response = self.client.get(self.home_url)
        
        # Check that the context contains the expected keys
        self.assertIn('featured_destinations', response.context)
        self.assertIn('featured_tours', response.context)
        self.assertIn('testimonials', response.context)
        
        # Check that our test destination is in the featured destinations
        self.assertIn(self.test_destination, response.context['featured_destinations'])
        
        # Check that our test tour is in the featured tours
        self.assertIn(self.test_tour, response.context['featured_tours'])
        
        # Check that our testimonials are in the testimonials
        self.assertIn(self.testimonial1, response.context['testimonials'])
        self.assertIn(self.testimonial2, response.context['testimonials'])
        
    def test_home_view_search_form(self):
        """
        Test that the home page includes a search form.
        
        Verifies that the home page context includes a search form
        for searching destinations and tours.
        """
        response = self.client.get(self.home_url)
        
        # Check that the context contains the search form
        self.assertIn('search_form', response.context)


class AboutViewTests(TravelGuideBaseTestCase):
    """
    Tests for the about page view in the core app.
    
    These tests verify that the about page displays correctly.
    Each test focuses on a specific aspect of the about page's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for about page tests.
        
        Extends the base setUp method to include additional data for testing.
        """
        super().setUp()
        
        # URL for testing
        self.about_url = reverse('core:about')
    
    def test_about_view_status(self):
        """
        Test that the about page loads successfully.
        
        Verifies that the about page returns a 200 OK status code.
        """
        response = self.client.get(self.about_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/about.html')
        
    def test_about_view_context(self):
        """
        Test that the about page context contains the expected data.
        
        Verifies that the about page context includes site settings
        and other relevant information.
        """
        # Create site settings
        site_settings = SiteSettings.objects.create(
            site_name="Travel Guide",
            site_description="Your ultimate travel companion",
            about_content="We are a travel company dedicated to providing the best travel experiences."
        )
        
        response = self.client.get(self.about_url)
        
        # Check that the context contains the site settings
        self.assertIn('site_settings', response.context)
        self.assertEqual(response.context['site_settings'], site_settings)


class ContactViewTests(TravelGuideBaseTestCase):
    """
    Tests for the contact page view in the core app.
    
    These tests verify that the contact page displays correctly,
    and that the contact form works as expected. Each test focuses on
    a specific aspect of the contact page's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for contact page tests.
        
        Extends the base setUp method to include additional data for testing.
        """
        super().setUp()
        
        # Create site settings with contact information
        self.site_settings = SiteSettings.objects.create(
            site_name="Travel Guide",
            contact_email="contact@travelguide.com",
            phone_number="+1234567890",
            address="123 Travel Street, Tourism City"
        )
        
        # URL for testing
        self.contact_url = reverse('core:contact')
    
    def test_contact_view_status(self):
        """
        Test that the contact page loads successfully.
        
        Verifies that the contact page returns a 200 OK status code.
        """
        response = self.client.get(self.contact_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/contact.html')
        
    def test_contact_view_context(self):
        """
        Test that the contact page context contains the expected data.
        
        Verifies that the contact page context includes the contact form
        and site settings with contact information.
        """
        response = self.client.get(self.contact_url)
        
        # Check that the context contains the contact form
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], ContactForm)
        
        # Check that the context contains the site settings
        self.assertIn('site_settings', response.context)
        self.assertEqual(response.context['site_settings'], self.site_settings)
        
    def test_contact_form_submission(self):
        """
        Test that the contact form can be submitted successfully.
        
        Verifies that submitting the contact form creates a new ContactMessage
        object and sends an email notification.
        """
        # Initial count of contact messages
        initial_count = ContactMessage.objects.count()
        
        # Form data
        form_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'subject': 'Test Subject',
            'message': 'This is a test message.'
        }
        
        # Submit the form
        response = self.client.post(self.contact_url, form_data)
        
        # Check that we're redirected to the success page
        self.assertRedirects(response, reverse('core:contact_success'))
        
        # Check that a new contact message was created
        self.assertEqual(ContactMessage.objects.count(), initial_count + 1)
        
        # Get the newly created message
        message = ContactMessage.objects.latest('created_at')
        
        # Check that the message has the correct attributes
        self.assertEqual(message.name, 'John Doe')
        self.assertEqual(message.email, 'john@example.com')
        self.assertEqual(message.subject, 'Test Subject')
        self.assertEqual(message.message, 'This is a test message.')
        self.assertFalse(message.is_read)
        
        # Check that an email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'New Contact Form Submission: Test Subject')
        self.assertEqual(mail.outbox[0].to, ['contact@travelguide.com'])
        
    def test_contact_form_invalid_submission(self):
        """
        Test that the contact form validation works correctly.
        
        Verifies that submitting an invalid form does not create a new
        ContactMessage object and displays error messages.
        """
        # Initial count of contact messages
        initial_count = ContactMessage.objects.count()
        
        # Invalid form data (missing required fields)
        form_data = {
            'name': '',  # Missing name
            'email': 'invalid-email',  # Invalid email
            'subject': 'Test Subject',
            'message': 'This is a test message.'
        }
        
        # Submit the form
        response = self.client.post(self.contact_url, form_data)
        
        # Check that we're not redirected
        self.assertEqual(response.status_code, 200)
        
        # Check that the form has errors
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)
        
        # Check that no new contact message was created
        self.assertEqual(ContactMessage.objects.count(), initial_count)
        
        # Check that no email was sent
        self.assertEqual(len(mail.outbox), 0)


class FAQViewTests(TravelGuideBaseTestCase):
    """
    Tests for the FAQ page view in the core app.
    
    These tests verify that the FAQ page displays correctly,
    showing only published FAQs in the correct order.
    Each test focuses on a specific aspect of the FAQ page's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for FAQ page tests.
        
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
        
        # URL for testing
        self.faq_url = reverse('core:faq')
    
    def test_faq_view_status(self):
        """
        Test that the FAQ page loads successfully.
        
        Verifies that the FAQ page returns a 200 OK status code.
        """
        response = self.client.get(self.faq_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/faq.html')
        
    def test_faq_view_context(self):
        """
        Test that the FAQ page context contains the expected data.
        
        Verifies that the FAQ page context includes only published FAQs
        in the correct order.
        """
        response = self.client.get(self.faq_url)
        
        # Check that the context contains the FAQs
        self.assertIn('faqs', response.context)
        
        # Check that only published FAQs are included
        faqs = response.context['faqs']
        self.assertEqual(len(faqs), 2)
        self.assertIn(self.faq1, faqs)
        self.assertIn(self.faq2, faqs)
        self.assertNotIn(self.faq3, faqs)  # This one is not published
        
        # Check that the FAQs are in the correct order
        self.assertEqual(faqs[0], self.faq1)  # order=1
        self.assertEqual(faqs[1], self.faq2)  # order=2


class NewsletterViewTests(TravelGuideBaseTestCase):
    """
    Tests for the newsletter subscription views in the core app.
    
    These tests verify that users can subscribe to and unsubscribe from
    the newsletter. Each test focuses on a specific aspect of the
    newsletter subscription functionality.
    """
    
    def setUp(self):
        """
        Set up test data for newsletter tests.
        
        Extends the base setUp method to include newsletter subscriptions for testing.
        """
        super().setUp()
        
        # Create some newsletter subscriptions
        self.subscription = Newsletter.objects.create(
            email="john@example.com",
            is_active=True
        )
        
        # URLs for testing
        self.subscribe_url = reverse('core:newsletter_subscribe')
        self.unsubscribe_url = reverse('core:newsletter_unsubscribe', kwargs={'email': 'john@example.com'})
    
    def test_newsletter_subscribe_get(self):
        """
        Test that the newsletter subscribe page loads successfully.
        
        Verifies that the subscribe page returns a 200 OK status code
        and contains the newsletter form.
        """
        response = self.client.get(self.subscribe_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/newsletter_subscribe.html')
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], NewsletterForm)
        
    def test_newsletter_subscribe_post(self):
        """
        Test that users can subscribe to the newsletter.
        
        Verifies that submitting the newsletter form creates a new
        Newsletter object and sends a confirmation email.
        """
        # Initial count of subscriptions
        initial_count = Newsletter.objects.count()
        
        # Form data
        form_data = {
            'email': 'new@example.com'
        }
        
        # Submit the form
        response = self.client.post(self.subscribe_url, form_data)
        
        # Check that we're redirected to the success page
        self.assertRedirects(response, reverse('core:newsletter_subscribe_success'))
        
        # Check that a new subscription was created
        self.assertEqual(Newsletter.objects.count(), initial_count + 1)
        
        # Get the newly created subscription
        subscription = Newsletter.objects.get(email='new@example.com')
        
        # Check that the subscription has the correct attributes
        self.assertEqual(subscription.email, 'new@example.com')
        self.assertTrue(subscription.is_active)
        
        # Check that a confirmation email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Newsletter Subscription Confirmation', mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ['new@example.com'])
        
    def test_newsletter_subscribe_duplicate(self):
        """
        Test that users cannot subscribe with an email that is already subscribed.
        
        Verifies that attempting to subscribe with an email that is already
        subscribed displays an error message.
        """
        # Initial count of subscriptions
        initial_count = Newsletter.objects.count()
        
        # Form data with an email that is already subscribed
        form_data = {
            'email': 'john@example.com'  # This email is already subscribed
        }
        
        # Submit the form
        response = self.client.post(self.subscribe_url, form_data)
        
        # Check that we're not redirected
        self.assertEqual(response.status_code, 200)
        
        # Check that the form has errors
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)
        
        # Check that no new subscription was created
        self.assertEqual(Newsletter.objects.count(), initial_count)
        
    def test_newsletter_unsubscribe(self):
        """
        Test that users can unsubscribe from the newsletter.
        
        Verifies that visiting the unsubscribe URL with a valid email
        marks the subscription as inactive.
        """
        # Initially, the subscription is active
        self.assertTrue(self.subscription.is_active)
        
        # Visit the unsubscribe URL
        response = self.client.get(self.unsubscribe_url)
        
        # Check that we're redirected to the success page
        self.assertRedirects(response, reverse('core:newsletter_unsubscribe_success'))
        
        # Refresh the subscription from the database
        self.subscription.refresh_from_db()
        
        # Check that the subscription is now inactive
        self.assertFalse(self.subscription.is_active)
        
    def test_newsletter_unsubscribe_invalid_email(self):
        """
        Test that the unsubscribe view handles invalid emails gracefully.
        
        Verifies that visiting the unsubscribe URL with an invalid email
        displays an error message.
        """
        # URL with an invalid email
        invalid_url = reverse('core:newsletter_unsubscribe', kwargs={'email': 'invalid@example.com'})
        
        # Visit the unsubscribe URL
        response = self.client.get(invalid_url)
        
        # Check that we're redirected to the error page
        self.assertRedirects(response, reverse('core:newsletter_unsubscribe_error'))


class SearchViewTests(TravelGuideBaseTestCase):
    """
    Tests for the search view in the core app.
    
    These tests verify that the search functionality works correctly,
    returning relevant destinations and tours based on the search query.
    Each test focuses on a specific aspect of the search functionality.
    """
    
    def setUp(self):
        """
        Set up test data for search tests.
        
        Extends the base setUp method to include additional data for testing.
        """
        super().setUp()
        
        # Create additional destinations and tours for testing search
        self.paris = self.create_destination("Paris", self.test_region)
        self.paris.description = "The City of Light in France"
        self.paris.save()
        
        self.rome = self.create_destination("Rome", self.test_region)
        self.rome.description = "The Eternal City in Italy"
        self.rome.save()
        
        self.paris_tour = self.create_tour("Paris Explorer", self.paris)
        self.paris_tour.description = "Explore the beautiful city of Paris"
        self.paris_tour.save()
        
        # URL for testing
        self.search_url = reverse('core:search')
    
    def test_search_view_get(self):
        """
        Test that the search page loads successfully.
        
        Verifies that the search page returns a 200 OK status code
        and contains the search form.
        """
        response = self.client.get(self.search_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/search.html')
        self.assertIn('form', response.context)
        
    def test_search_view_results(self):
        """
        Test that the search view returns relevant results.
        
        Verifies that searching for a term returns destinations and tours
        that match the search term in their name or description.
        """
        # Search for "Paris"
        response = self.client.get(self.search_url, {'q': 'Paris'})
        
        # Check that the search term is in the context
        self.assertIn('query', response.context)
        self.assertEqual(response.context['query'], 'Paris')
        
        # Check that the Paris destination and tour are in the results
        self.assertIn('destinations', response.context)
        self.assertIn('tours', response.context)
        self.assertIn(self.paris, response.context['destinations'])
        self.assertIn(self.paris_tour, response.context['tours'])
        
        # Check that the Tokyo destination and tour are not in the results
        self.assertNotIn(self.test_destination, response.context['destinations'])
        self.assertNotIn(self.test_tour, response.context['tours'])
        
    def test_search_view_no_results(self):
        """
        Test that the search view handles no results gracefully.
        
        Verifies that searching for a term that doesn't match any destinations
        or tours displays a message indicating no results were found.
        """
        # Search for a term that doesn't match anything
        response = self.client.get(self.search_url, {'q': 'XYZ123'})
        
        # Check that the search term is in the context
        self.assertIn('query', response.context)
        self.assertEqual(response.context['query'], 'XYZ123')
        
        # Check that there are no results
        self.assertIn('destinations', response.context)
        self.assertIn('tours', response.context)
        self.assertEqual(len(response.context['destinations']), 0)
        self.assertEqual(len(response.context['tours']), 0)
        
        # Check that the no results message is displayed
        self.assertContains(response, "No results found")
        
    def test_search_view_empty_query(self):
        """
        Test that the search view handles empty queries gracefully.
        
        Verifies that submitting an empty search query redirects back
        to the search page without performing a search.
        """
        # Submit an empty search query
        response = self.client.get(self.search_url, {'q': ''})
        
        # Check that we're redirected back to the search page
        self.assertRedirects(response, self.search_url)


class SitemapViewTests(TravelGuideBaseTestCase):
    """
    Tests for the sitemap view in the core app.
    
    These tests verify that the sitemap page displays correctly,
    showing links to all important pages on the site.
    Each test focuses on a specific aspect of the sitemap's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for sitemap tests.
        
        Extends the base setUp method to include additional data for testing.
        """
        super().setUp()
        
        # URL for testing
        self.sitemap_url = reverse('core:sitemap')
    
    def test_sitemap_view_status(self):
        """
        Test that the sitemap page loads successfully.
        
        Verifies that the sitemap page returns a 200 OK status code.
        """
        response = self.client.get(self.sitemap_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/sitemap.html')
        
    def test_sitemap_view_context(self):
        """
        Test that the sitemap page context contains the expected data.
        
        Verifies that the sitemap page context includes destinations,
        tours, and other important pages.
        """
        response = self.client.get(self.sitemap_url)
        
        # Check that the context contains the expected keys
        self.assertIn('destinations', response.context)
        self.assertIn('tours', response.context)
        self.assertIn('regions', response.context)
        
        # Check that our test destination and tour are included
        self.assertIn(self.test_destination, response.context['destinations'])
        self.assertIn(self.test_tour, response.context['tours'])
        self.assertIn(self.test_region, response.context['regions'])
