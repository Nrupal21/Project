"""
Test cases for custom template tags and filters in the TravelGuide application.

This module contains comprehensive test cases for all custom template tags
and filters used in the application templates. Every test function is thoroughly
documented to make understanding the tests easier for programmers.
"""

from django.test import TestCase
from django.template import Context, Template
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
import datetime
from decimal import Decimal

from core.templatetags.core_tags import (
    format_price,
    get_setting,
    active_link,
    markdown_to_html,
    truncate_chars,
    time_since,
    get_rating_stars,
    add_query_params
)
from core.models import SiteSettings
from destinations.models import Destination, Region
from tours.models import Tour, TourCategory
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class TemplateTagsTests(TravelGuideBaseTestCase):
    """
    Tests for custom template tags and filters used in the TravelGuide application.
    
    These tests verify that template tags and filters work correctly under various
    conditions and with different inputs.
    """
    
    def setUp(self):
        """
        Set up test data for template tags tests.
        
        Extends the base setUp method to include additional test data.
        """
        super().setUp()
        
        # Create site settings
        self.site_settings = SiteSettings.objects.create(
            site_name="TravelGuide",
            site_description="Your guide to amazing destinations",
            contact_email="contact@travelguide.com",
            facebook_url="https://facebook.com/travelguide",
            twitter_url="https://twitter.com/travelguide",
            instagram_url="https://instagram.com/travelguide",
            footer_text="© 2023 TravelGuide. All rights reserved."
        )
        
        # Create additional test data for template tags
        self.europe_region = Region.objects.create(
            name="Europe",
            description="Explore the diverse cultures and landscapes of Europe.",
            image="regions/europe.jpg"
        )
        
        self.paris_destination = Destination.objects.create(
            name="Paris",
            description="Explore the romantic city of Paris with its iconic Eiffel Tower.",
            region=self.europe_region,
            image="destinations/paris.jpg",
            is_featured=True,
            latitude=48.8566,
            longitude=2.3522
        )
        
        self.cultural_category = TourCategory.objects.create(
            name="Cultural",
            description="Immersive cultural experiences and historical tours."
        )
        
        self.paris_tour = Tour.objects.create(
            name="Paris Cultural Experience",
            description="Explore the rich cultural heritage of Paris.",
            destination=self.paris_destination,
            category=self.cultural_category,
            duration=5,
            price=1200.00,
            image="tours/paris_culture.jpg",
            is_featured=True
        )
    
    def test_format_price_tag(self):
        """
        Test the format_price template tag.
        
        Verifies that the template tag correctly formats price values
        with the specified currency symbol and decimal places.
        """
        # Test with integer value
        result = format_price(1000)
        self.assertEqual(result, "$1,000.00")
        
        # Test with float value
        result = format_price(1234.56)
        self.assertEqual(result, "$1,234.56")
        
        # Test with Decimal value
        result = format_price(Decimal("1234.56"))
        self.assertEqual(result, "$1,234.56")
        
        # Test with different currency
        result = format_price(1234.56, currency="EUR")
        self.assertEqual(result, "€1,234.56")
        
        # Test with zero value
        result = format_price(0)
        self.assertEqual(result, "$0.00")
        
        # Test with negative value
        result = format_price(-1234.56)
        self.assertEqual(result, "-$1,234.56")
        
        # Test in a template context
        template = Template("{% load core_tags %}{{ price|format_price:currency }}")
        context = Context({"price": 1234.56, "currency": "GBP"})
        rendered = template.render(context)
        self.assertEqual(rendered, "£1,234.56")
        
    def test_get_setting_tag(self):
        """
        Test the get_setting template tag.
        
        Verifies that the template tag correctly retrieves settings
        from the SiteSettings model.
        """
        # Test retrieving existing settings
        result = get_setting("site_name")
        self.assertEqual(result, "TravelGuide")
        
        result = get_setting("contact_email")
        self.assertEqual(result, "contact@travelguide.com")
        
        # Test retrieving non-existent setting (should return empty string)
        result = get_setting("non_existent_setting")
        self.assertEqual(result, "")
        
        # Test in a template context
        template = Template("{% load core_tags %}{% get_setting 'site_name' %}")
        rendered = template.render(Context({}))
        self.assertEqual(rendered, "TravelGuide")
        
        # Test with variable in a template context
        template = Template("{% load core_tags %}{% get_setting setting_name %}")
        context = Context({"setting_name": "footer_text"})
        rendered = template.render(context)
        self.assertEqual(rendered, "© 2023 TravelGuide. All rights reserved.")
        
    def test_active_link_tag(self):
        """
        Test the active_link template tag.
        
        Verifies that the template tag correctly determines if a link
        is active based on the current URL path.
        """
        # Create a mock request with a specific path
        class MockRequest:
            def __init__(self, path):
                self.path = path
        
        # Test with exact match
        request = MockRequest("/destinations/")
        result = active_link(request, "/destinations/")
        self.assertEqual(result, "active")
        
        # Test with non-matching path
        request = MockRequest("/destinations/")
        result = active_link(request, "/tours/")
        self.assertEqual(result, "")
        
        # Test with partial match (should not be active)
        request = MockRequest("/destinations/paris/")
        result = active_link(request, "/destinations/")
        self.assertEqual(result, "")
        
        # Test with startswith=True (should be active)
        request = MockRequest("/destinations/paris/")
        result = active_link(request, "/destinations/", startswith=True)
        self.assertEqual(result, "active")
        
        # Test with custom active class
        request = MockRequest("/destinations/")
        result = active_link(request, "/destinations/", active_class="current")
        self.assertEqual(result, "current")
        
        # Test in a template context
        template = Template("{% load core_tags %}<li class=\"{% active_link request '/destinations/' %}\">Destinations</li>")
        context = Context({"request": MockRequest("/destinations/")})
        rendered = template.render(context)
        self.assertEqual(rendered, "<li class=\"active\">Destinations</li>")
        
    def test_markdown_to_html_filter(self):
        """
        Test the markdown_to_html template filter.
        
        Verifies that the template filter correctly converts Markdown
        syntax to HTML.
        """
        # Test with basic Markdown
        markdown_text = "# Heading\n\nThis is a **bold** text with a [link](https://example.com)."
        html = markdown_to_html(markdown_text)
        self.assertIn("<h1>Heading</h1>", html)
        self.assertIn("<strong>bold</strong>", html)
        self.assertIn("<a href=\"https://example.com\">link</a>", html)
        
        # Test with lists
        markdown_text = "- Item 1\n- Item 2\n- Item 3"
        html = markdown_to_html(markdown_text)
        self.assertIn("<ul>", html)
        self.assertIn("<li>Item 1</li>", html)
        self.assertIn("<li>Item 2</li>", html)
        self.assertIn("<li>Item 3</li>", html)
        self.assertIn("</ul>", html)
        
        # Test with code blocks
        markdown_text = "```python\ndef hello():\n    print('Hello, world!')\n```"
        html = markdown_to_html(markdown_text)
        self.assertIn("<code>", html)
        self.assertIn("def hello():", html)
        self.assertIn("print('Hello, world!')", html)
        
        # Test in a template context
        template = Template("{% load core_tags %}{{ markdown_content|markdown_to_html }}")
        context = Context({"markdown_content": "# Heading\n\nThis is a **bold** text."})
        rendered = template.render(context)
        self.assertIn("<h1>Heading</h1>", rendered)
        self.assertIn("<strong>bold</strong>", rendered)
        
    def test_truncate_chars_filter(self):
        """
        Test the truncate_chars template filter.
        
        Verifies that the template filter correctly truncates text
        to the specified number of characters and adds an ellipsis.
        """
        # Test with short text (no truncation needed)
        text = "Short text"
        result = truncate_chars(text, 20)
        self.assertEqual(result, "Short text")
        
        # Test with long text (truncation needed)
        text = "This is a very long text that needs to be truncated to a shorter length."
        result = truncate_chars(text, 20)
        self.assertEqual(result, "This is a very long...")
        
        # Test with custom suffix
        result = truncate_chars(text, 20, suffix="[more]")
        self.assertEqual(result, "This is a very long[more]")
        
        # Test with exact length
        text = "Exactly twenty chars."
        result = truncate_chars(text, 20)
        self.assertEqual(result, "Exactly twenty chars.")
        
        # Test in a template context
        template = Template("{% load core_tags %}{{ content|truncate_chars:10 }}")
        context = Context({"content": "This is a long text."})
        rendered = template.render(context)
        self.assertEqual(rendered, "This is a...")
        
    def test_time_since_filter(self):
        """
        Test the time_since template filter.
        
        Verifies that the template filter correctly calculates the time
        elapsed since a given datetime and formats it in a human-readable way.
        """
        # Test with recent time (seconds ago)
        now = timezone.now()
        recent_time = now - datetime.timedelta(seconds=30)
        result = time_since(recent_time)
        self.assertIn("seconds ago", result)
        
        # Test with minutes ago
        minutes_ago = now - datetime.timedelta(minutes=5)
        result = time_since(minutes_ago)
        self.assertIn("5 minutes ago", result)
        
        # Test with hours ago
        hours_ago = now - datetime.timedelta(hours=3)
        result = time_since(hours_ago)
        self.assertIn("3 hours ago", result)
        
        # Test with days ago
        days_ago = now - datetime.timedelta(days=2)
        result = time_since(days_ago)
        self.assertIn("2 days ago", result)
        
        # Test with weeks ago
        weeks_ago = now - datetime.timedelta(days=14)
        result = time_since(weeks_ago)
        self.assertIn("2 weeks ago", result)
        
        # Test with months ago
        months_ago = now - datetime.timedelta(days=60)
        result = time_since(months_ago)
        self.assertIn("2 months ago", result)
        
        # Test with years ago
        years_ago = now - datetime.timedelta(days=730)
        result = time_since(years_ago)
        self.assertIn("2 years ago", result)
        
        # Test in a template context
        template = Template("{% load core_tags %}{{ date|time_since }}")
        context = Context({"date": now - datetime.timedelta(hours=5)})
        rendered = template.render(context)
        self.assertIn("5 hours ago", rendered)
        
    def test_get_rating_stars_filter(self):
        """
        Test the get_rating_stars template filter.
        
        Verifies that the template filter correctly generates HTML
        for displaying star ratings.
        """
        # Test with integer rating
        result = get_rating_stars(5)
        self.assertEqual(result.count('<i class="fas fa-star"></i>'), 5)
        self.assertEqual(result.count('<i class="far fa-star"></i>'), 0)
        self.assertEqual(result.count('<i class="fas fa-star-half-alt"></i>'), 0)
        
        # Test with half-star rating
        result = get_rating_stars(3.5)
        self.assertEqual(result.count('<i class="fas fa-star"></i>'), 3)
        self.assertEqual(result.count('<i class="far fa-star"></i>'), 1)
        self.assertEqual(result.count('<i class="fas fa-star-half-alt"></i>'), 1)
        
        # Test with decimal rating (rounded down)
        result = get_rating_stars(3.2)
        self.assertEqual(result.count('<i class="fas fa-star"></i>'), 3)
        self.assertEqual(result.count('<i class="far fa-star"></i>'), 2)
        self.assertEqual(result.count('<i class="fas fa-star-half-alt"></i>'), 0)
        
        # Test with decimal rating (rounded up to half-star)
        result = get_rating_stars(3.3)
        self.assertEqual(result.count('<i class="fas fa-star"></i>'), 3)
        self.assertEqual(result.count('<i class="far fa-star"></i>'), 1)
        self.assertEqual(result.count('<i class="fas fa-star-half-alt"></i>'), 1)
        
        # Test with out-of-range rating (too high)
        result = get_rating_stars(6)
        self.assertEqual(result.count('<i class="fas fa-star"></i>'), 5)  # Should cap at 5
        
        # Test with out-of-range rating (too low)
        result = get_rating_stars(-1)
        self.assertEqual(result.count('<i class="far fa-star"></i>'), 5)  # Should show all empty
        
        # Test in a template context
        template = Template("{% load core_tags %}{{ rating|get_rating_stars }}")
        context = Context({"rating": 4.5})
        rendered = template.render(context)
        self.assertEqual(rendered.count('<i class="fas fa-star"></i>'), 4)
        self.assertEqual(rendered.count('<i class="fas fa-star-half-alt"></i>'), 1)
        
    def test_add_query_params_filter(self):
        """
        Test the add_query_params template filter.
        
        Verifies that the template filter correctly adds or updates
        query parameters in a URL.
        """
        # Test adding a parameter to a URL without query string
        url = "/search/"
        result = add_query_params(url, param="value")
        self.assertEqual(result, "/search/?param=value")
        
        # Test adding a parameter to a URL with existing query string
        url = "/search/?q=test"
        result = add_query_params(url, param="value")
        self.assertEqual(result, "/search/?q=test&param=value")
        
        # Test updating an existing parameter
        url = "/search/?param=old&q=test"
        result = add_query_params(url, param="new")
        self.assertEqual(result, "/search/?param=new&q=test")
        
        # Test adding multiple parameters
        url = "/search/"
        result = add_query_params(url, param1="value1", param2="value2")
        self.assertTrue("param1=value1" in result)
        self.assertTrue("param2=value2" in result)
        
        # Test with URL-encoded values
        url = "/search/"
        result = add_query_params(url, q="test query")
        self.assertEqual(result, "/search/?q=test+query")
        
        # Test in a template context
        template = Template("{% load core_tags %}{{ url|add_query_params:params }}")
        context = Context({
            "url": "/search/?q=test",
            "params": {"sort": "price", "order": "asc"}
        })
        rendered = template.render(context)
        self.assertTrue("q=test" in rendered)
        self.assertTrue("sort=price" in rendered)
        self.assertTrue("order=asc" in rendered)


class InclusionTagsTests(TravelGuideBaseTestCase):
    """
    Tests for inclusion template tags used in the TravelGuide application.
    
    These tests verify that inclusion tags correctly render templates
    with the appropriate context.
    """
    
    def setUp(self):
        """
        Set up test data for inclusion tags tests.
        
        Extends the base setUp method to include additional test data.
        """
        super().setUp()
        
        # Import inclusion tags here to avoid circular imports
        from core.templatetags.inclusion_tags import (
            featured_destinations,
            recent_tours,
            sidebar_categories,
            social_links,
            newsletter_form
        )
        
        self.featured_destinations = featured_destinations
        self.recent_tours = recent_tours
        self.sidebar_categories = sidebar_categories
        self.social_links = social_links
        self.newsletter_form = newsletter_form
        
        # Create site settings
        self.site_settings = SiteSettings.objects.create(
            site_name="TravelGuide",
            site_description="Your guide to amazing destinations",
            contact_email="contact@travelguide.com",
            facebook_url="https://facebook.com/travelguide",
            twitter_url="https://twitter.com/travelguide",
            instagram_url="https://instagram.com/travelguide",
            footer_text="© 2023 TravelGuide. All rights reserved."
        )
        
        # Create additional test data for inclusion tags
        self.europe_region = Region.objects.create(
            name="Europe",
            description="Explore the diverse cultures and landscapes of Europe.",
            image="regions/europe.jpg"
        )
        
        self.asia_region = Region.objects.create(
            name="Asia",
            description="Discover the rich cultures and ancient traditions of Asia.",
            image="regions/asia.jpg"
        )
        
        self.paris_destination = Destination.objects.create(
            name="Paris",
            description="Explore the romantic city of Paris with its iconic Eiffel Tower.",
            region=self.europe_region,
            image="destinations/paris.jpg",
            is_featured=True,
            latitude=48.8566,
            longitude=2.3522
        )
        
        self.tokyo_destination = Destination.objects.create(
            name="Tokyo",
            description="Experience the vibrant city life of Tokyo, Japan's capital.",
            region=self.asia_region,
            image="destinations/tokyo.jpg",
            is_featured=True,
            latitude=35.6762,
            longitude=139.6503
        )
        
        self.rome_destination = Destination.objects.create(
            name="Rome",
            description="Discover the ancient history and delicious cuisine of Rome.",
            region=self.europe_region,
            image="destinations/rome.jpg",
            is_featured=True,
            latitude=41.9028,
            longitude=12.4964
        )
        
        self.cultural_category = TourCategory.objects.create(
            name="Cultural",
            description="Immersive cultural experiences and historical tours."
        )
        
        self.adventure_category = TourCategory.objects.create(
            name="Adventure",
            description="Exciting adventure tours for thrill-seekers."
        )
        
        self.food_category = TourCategory.objects.create(
            name="Food & Culinary",
            description="Delicious food tours and culinary experiences."
        )
        
        self.paris_tour = Tour.objects.create(
            name="Paris Cultural Experience",
            description="Explore the rich cultural heritage of Paris.",
            destination=self.paris_destination,
            category=self.cultural_category,
            duration=5,
            price=1200.00,
            image="tours/paris_culture.jpg",
            is_featured=True,
            created_at=timezone.now() - datetime.timedelta(days=10)
        )
        
        self.tokyo_tour = Tour.objects.create(
            name="Tokyo Adventure",
            description="An exciting adventure through Tokyo's vibrant neighborhoods.",
            destination=self.tokyo_destination,
            category=self.adventure_category,
            duration=7,
            price=1500.00,
            image="tours/tokyo_adventure.jpg",
            is_featured=True,
            created_at=timezone.now() - datetime.timedelta(days=5)
        )
        
        self.rome_tour = Tour.objects.create(
            name="Rome Food Tour",
            description="Taste the delicious cuisine of Rome.",
            destination=self.rome_destination,
            category=self.food_category,
            duration=3,
            price=800.00,
            image="tours/rome_food.jpg",
            is_featured=True,
            created_at=timezone.now() - datetime.timedelta(days=2)
        )
    
    def test_featured_destinations_tag(self):
        """
        Test the featured_destinations inclusion tag.
        
        Verifies that the tag correctly renders the template with
        featured destinations in the context.
        """
        # Get the context from the inclusion tag
        context = self.featured_destinations(limit=3)
        
        # Check that the context contains the expected data
        self.assertIn('destinations', context)
        self.assertEqual(len(context['destinations']), 3)
        
        # Check that only featured destinations are included
        for destination in context['destinations']:
            self.assertTrue(destination.is_featured)
        
        # Check that destinations are in the expected order
        destination_names = [d.name for d in context['destinations']]
        self.assertIn('Paris', destination_names)
        self.assertIn('Tokyo', destination_names)
        self.assertIn('Rome', destination_names)
        
        # Test with a different limit
        context = self.featured_destinations(limit=2)
        self.assertEqual(len(context['destinations']), 2)
        
        # Test in a template context
        template = Template("{% load inclusion_tags %}{% featured_destinations 2 %}")
        rendered = template.render(Context({}))
        self.assertIn('featured-destinations', rendered)
        self.assertIn('Paris', rendered)
        
    def test_recent_tours_tag(self):
        """
        Test the recent_tours inclusion tag.
        
        Verifies that the tag correctly renders the template with
        recent tours in the context.
        """
        # Get the context from the inclusion tag
        context = self.recent_tours(limit=3)
        
        # Check that the context contains the expected data
        self.assertIn('tours', context)
        self.assertEqual(len(context['tours']), 3)
        
        # Check that tours are in the expected order (most recent first)
        tour_names = [t.name for t in context['tours']]
        self.assertEqual(tour_names[0], 'Rome Food Tour')
        self.assertEqual(tour_names[1], 'Tokyo Adventure')
        self.assertEqual(tour_names[2], 'Paris Cultural Experience')
        
        # Test with a different limit
        context = self.recent_tours(limit=2)
        self.assertEqual(len(context['tours']), 2)
        tour_names = [t.name for t in context['tours']]
        self.assertEqual(tour_names[0], 'Rome Food Tour')
        self.assertEqual(tour_names[1], 'Tokyo Adventure')
        
        # Test in a template context
        template = Template("{% load inclusion_tags %}{% recent_tours 2 %}")
        rendered = template.render(Context({}))
        self.assertIn('recent-tours', rendered)
        self.assertIn('Rome Food Tour', rendered)
        self.assertIn('Tokyo Adventure', rendered)
        
    def test_sidebar_categories_tag(self):
        """
        Test the sidebar_categories inclusion tag.
        
        Verifies that the tag correctly renders the template with
        tour categories in the context.
        """
        # Get the context from the inclusion tag
        context = self.sidebar_categories()
        
        # Check that the context contains the expected data
        self.assertIn('categories', context)
        self.assertEqual(len(context['categories']), 3)
        
        # Check that categories are included
        category_names = [c.name for c in context['categories']]
        self.assertIn('Cultural', category_names)
        self.assertIn('Adventure', category_names)
        self.assertIn('Food & Culinary', category_names)
        
        # Test in a template context
        template = Template("{% load inclusion_tags %}{% sidebar_categories %}")
        rendered = template.render(Context({}))
        self.assertIn('sidebar-categories', rendered)
        self.assertIn('Cultural', rendered)
        self.assertIn('Adventure', rendered)
        self.assertIn('Food &amp; Culinary', rendered)  # HTML-escaped
        
    def test_social_links_tag(self):
        """
        Test the social_links inclusion tag.
        
        Verifies that the tag correctly renders the template with
        social media links from site settings in the context.
        """
        # Get the context from the inclusion tag
        context = self.social_links()
        
        # Check that the context contains the expected data
        self.assertIn('facebook_url', context)
        self.assertIn('twitter_url', context)
        self.assertIn('instagram_url', context)
        
        self.assertEqual(context['facebook_url'], 'https://facebook.com/travelguide')
        self.assertEqual(context['twitter_url'], 'https://twitter.com/travelguide')
        self.assertEqual(context['instagram_url'], 'https://instagram.com/travelguide')
        
        # Test in a template context
        template = Template("{% load inclusion_tags %}{% social_links %}")
        rendered = template.render(Context({}))
        self.assertIn('social-links', rendered)
        self.assertIn('https://facebook.com/travelguide', rendered)
        self.assertIn('https://twitter.com/travelguide', rendered)
        self.assertIn('https://instagram.com/travelguide', rendered)
        
    def test_newsletter_form_tag(self):
        """
        Test the newsletter_form inclusion tag.
        
        Verifies that the tag correctly renders the template with
        the newsletter form.
        """
        # Get the context from the inclusion tag
        context = self.newsletter_form()
        
        # Check that the context contains the expected data
        self.assertIn('form', context)
        
        # Test in a template context
        template = Template("{% load inclusion_tags %}{% newsletter_form %}")
        rendered = template.render(Context({}))
        self.assertIn('newsletter-form', rendered)
        self.assertIn('email', rendered)
        self.assertIn('Subscribe', rendered)
