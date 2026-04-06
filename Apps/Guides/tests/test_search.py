"""
Test cases for the search functionality across the TravelGuide application.

This module contains comprehensive test cases for the search functionality,
including searching for destinations, tours, and other content.
Every test function is thoroughly documented to make understanding
the tests easier for programmers.
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
import datetime
import json

from destinations.models import Region, Destination, Attraction
from tours.models import Tour, TourCategory
from itineraries.models import Itinerary
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class SearchFunctionalityTests(TravelGuideBaseTestCase):
    """
    Tests for the search functionality across the TravelGuide application.
    
    These tests verify that the search functionality works correctly,
    including searching for destinations, tours, and other content.
    Each test focuses on a specific aspect of the search functionality.
    """
    
    def setUp(self):
        """
        Set up test data for search functionality tests.
        
        Extends the base setUp method to include additional data for testing
        the search functionality.
        """
        super().setUp()
        
        # Create additional regions with specific keywords for testing search
        self.asia_region = Region.objects.create(
            name="Asia",
            description="Explore the diverse cultures and landscapes of Asia.",
            image="regions/asia.jpg"
        )
        
        self.europe_region = Region.objects.create(
            name="Europe",
            description="Discover historic cities and beautiful countryside in Europe.",
            image="regions/europe.jpg"
        )
        
        # Create additional destinations with specific keywords for testing search
        self.tokyo_destination = Destination.objects.create(
            name="Tokyo",
            description="Experience the vibrant city life of Tokyo, Japan's capital.",
            region=self.asia_region,
            image="destinations/tokyo.jpg",
            is_featured=True,
            latitude=35.6762,
            longitude=139.6503
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
        
        self.kyoto_destination = Destination.objects.create(
            name="Kyoto",
            description="Discover traditional Japanese culture in historic Kyoto.",
            region=self.asia_region,
            image="destinations/kyoto.jpg",
            is_featured=False,
            latitude=35.0116,
            longitude=135.7681
        )
        
        # Create attractions with specific keywords for testing search
        self.tokyo_tower = Attraction.objects.create(
            name="Tokyo Tower",
            description="Visit the iconic Tokyo Tower for panoramic views of the city.",
            destination=self.tokyo_destination,
            image="attractions/tokyo_tower.jpg",
            address="4 Chome-2-8 Shibakoen, Minato City, Tokyo",
            latitude=35.6586,
            longitude=139.7454,
            website="https://www.tokyotower.co.jp/en/"
        )
        
        self.eiffel_tower = Attraction.objects.create(
            name="Eiffel Tower",
            description="The iconic Eiffel Tower offers stunning views of Paris.",
            destination=self.paris_destination,
            image="attractions/eiffel_tower.jpg",
            address="Champ de Mars, 5 Avenue Anatole France, 75007 Paris",
            latitude=48.8584,
            longitude=2.2945,
            website="https://www.toureiffel.paris/en"
        )
        
        self.fushimi_inari = Attraction.objects.create(
            name="Fushimi Inari Shrine",
            description="Famous for its thousands of vermilion torii gates.",
            destination=self.kyoto_destination,
            image="attractions/fushimi_inari.jpg",
            address="68 Fukakusa Yabunouchicho, Fushimi Ward, Kyoto",
            latitude=34.9671,
            longitude=135.7727,
            website="http://inari.jp/"
        )
        
        # Create tour categories with specific keywords for testing search
        self.adventure_category = TourCategory.objects.create(
            name="Adventure",
            description="Exciting adventure tours for thrill-seekers."
        )
        
        self.cultural_category = TourCategory.objects.create(
            name="Cultural",
            description="Immersive cultural experiences and historical tours."
        )
        
        self.food_category = TourCategory.objects.create(
            name="Food & Culinary",
            description="Delicious food tours and culinary experiences."
        )
        
        # Create tours with specific keywords for testing search
        self.japan_adventure = Tour.objects.create(
            name="Japan Adventure",
            description="An exciting adventure through Japan's natural wonders.",
            destination=self.tokyo_destination,
            category=self.adventure_category,
            duration=7,
            price=1500.00,
            image="tours/japan_adventure.jpg",
            is_featured=True
        )
        
        self.paris_culture = Tour.objects.create(
            name="Paris Cultural Experience",
            description="Explore the rich cultural heritage of Paris.",
            destination=self.paris_destination,
            category=self.cultural_category,
            duration=5,
            price=1200.00,
            image="tours/paris_culture.jpg",
            is_featured=True
        )
        
        self.kyoto_food = Tour.objects.create(
            name="Kyoto Food Tour",
            description="Taste the traditional flavors of Kyoto cuisine.",
            destination=self.kyoto_destination,
            category=self.food_category,
            duration=3,
            price=800.00,
            image="tours/kyoto_food.jpg",
            is_featured=False
        )
        
        # Create itineraries with specific keywords for testing search
        self.japan_itinerary = Itinerary.objects.create(
            user=self.test_user,
            title="Japan Exploration",
            description="A comprehensive itinerary for exploring Japan.",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + datetime.timedelta(days=10),
            is_public=True,
            destination=self.tokyo_destination
        )
        
        self.paris_itinerary = Itinerary.objects.create(
            user=self.test_user,
            title="Paris Weekend",
            description="A weekend getaway in the city of lights.",
            start_date=timezone.now().date() + datetime.timedelta(days=30),
            end_date=timezone.now().date() + datetime.timedelta(days=33),
            is_public=True,
            destination=self.paris_destination
        )
        
        # URL for testing
        self.search_url = reverse('core:search')
        self.api_search_url = reverse('api:search')
    
    def test_search_view_get(self):
        """
        Test that the search page loads successfully.
        
        Verifies that the search page returns a 200 OK status code
        and contains the search form.
        """
        response = self.client.get(self.search_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/search.html')
        self.assertContains(response, '<form')
        self.assertContains(response, 'name="q"')
        
    def test_search_destinations(self):
        """
        Test searching for destinations.
        
        Verifies that searching for a term returns destinations
        that match the search term in their name or description.
        """
        # Search for "Tokyo" should return Tokyo destination
        response = self.client.get(f"{self.search_url}?q=Tokyo")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tokyo")
        self.assertContains(response, "Japan's capital")
        
        # Search for "Eiffel" should return Paris destination
        response = self.client.get(f"{self.search_url}?q=Eiffel")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Paris")
        self.assertContains(response, "Eiffel Tower")
        
        # Search for "traditional" should return Kyoto destination
        response = self.client.get(f"{self.search_url}?q=traditional")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kyoto")
        self.assertContains(response, "traditional Japanese culture")
        
    def test_search_tours(self):
        """
        Test searching for tours.
        
        Verifies that searching for a term returns tours
        that match the search term in their name or description.
        """
        # Search for "adventure" should return Japan Adventure tour
        response = self.client.get(f"{self.search_url}?q=adventure")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Japan Adventure")
        self.assertContains(response, "natural wonders")
        
        # Search for "cultural" should return Paris Cultural Experience tour
        response = self.client.get(f"{self.search_url}?q=cultural")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Paris Cultural Experience")
        self.assertContains(response, "rich cultural heritage")
        
        # Search for "food" should return Kyoto Food Tour
        response = self.client.get(f"{self.search_url}?q=food")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kyoto Food Tour")
        self.assertContains(response, "traditional flavors")
        
    def test_search_attractions(self):
        """
        Test searching for attractions.
        
        Verifies that searching for a term returns attractions
        that match the search term in their name or description.
        """
        # Search for "tower" should return Tokyo Tower and Eiffel Tower
        response = self.client.get(f"{self.search_url}?q=tower")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tokyo Tower")
        self.assertContains(response, "Eiffel Tower")
        
        # Search for "shrine" should return Fushimi Inari Shrine
        response = self.client.get(f"{self.search_url}?q=shrine")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fushimi Inari Shrine")
        self.assertContains(response, "vermilion torii gates")
        
    def test_search_itineraries(self):
        """
        Test searching for itineraries.
        
        Verifies that searching for a term returns public itineraries
        that match the search term in their title or description.
        """
        # Search for "exploration" should return Japan Exploration itinerary
        response = self.client.get(f"{self.search_url}?q=exploration")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Japan Exploration")
        
        # Search for "weekend" should return Paris Weekend itinerary
        response = self.client.get(f"{self.search_url}?q=weekend")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Paris Weekend")
        self.assertContains(response, "city of lights")
        
    def test_search_combined_results(self):
        """
        Test searching for a term that matches multiple types of content.
        
        Verifies that searching for a term returns all types of content
        that match the search term.
        """
        # Search for "Japan" should return Tokyo destination, Japan Adventure tour,
        # and Japan Exploration itinerary
        response = self.client.get(f"{self.search_url}?q=Japan")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tokyo")
        self.assertContains(response, "Japan Adventure")
        self.assertContains(response, "Japan Exploration")
        
        # Search for "Paris" should return Paris destination, Paris Cultural Experience tour,
        # and Paris Weekend itinerary
        response = self.client.get(f"{self.search_url}?q=Paris")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Paris")
        self.assertContains(response, "Paris Cultural Experience")
        self.assertContains(response, "Paris Weekend")
        
    def test_search_no_results(self):
        """
        Test searching for a term that doesn't match any content.
        
        Verifies that searching for a term that doesn't match any content
        displays a message indicating no results were found.
        """
        response = self.client.get(f"{self.search_url}?q=nonexistent")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No results found")
        self.assertNotContains(response, "Tokyo")
        self.assertNotContains(response, "Paris")
        self.assertNotContains(response, "Kyoto")
        
    def test_search_empty_query(self):
        """
        Test searching with an empty query.
        
        Verifies that submitting an empty search query redirects back
        to the search page without performing a search.
        """
        response = self.client.get(f"{self.search_url}?q=")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a search term")
        
    def test_search_case_insensitive(self):
        """
        Test that search is case-insensitive.
        
        Verifies that searching for a term in different cases
        returns the same results.
        """
        # Search for "TOKYO" (uppercase) should return Tokyo destination
        response = self.client.get(f"{self.search_url}?q=TOKYO")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tokyo")
        self.assertContains(response, "Japan's capital")
        
        # Search for "paris" (lowercase) should return Paris destination
        response = self.client.get(f"{self.search_url}?q=paris")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Paris")
        self.assertContains(response, "Eiffel Tower")
        
    def test_search_partial_match(self):
        """
        Test searching with partial terms.
        
        Verifies that searching for a partial term returns results
        that contain that term as part of a word.
        """
        # Search for "cult" should return results with "cultural" and "culture"
        response = self.client.get(f"{self.search_url}?q=cult")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cultural")
        self.assertContains(response, "culture")
        
        # Search for "trad" should return results with "traditional"
        response = self.client.get(f"{self.search_url}?q=trad")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "traditional")
        
    def test_search_api(self):
        """
        Test the search API endpoint.
        
        Verifies that the search API returns the correct results
        in JSON format.
        """
        # Search for "Tokyo" via API
        response = self.client.get(f"{self.api_search_url}?q=Tokyo")
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('destinations', data)
        self.assertIn('tours', data)
        self.assertIn('attractions', data)
        self.assertIn('itineraries', data)
        
        # Verify that Tokyo destination is in the results
        destination_names = [d['name'] for d in data['destinations']]
        self.assertIn("Tokyo", destination_names)
        
        # Search for "food" via API
        response = self.client.get(f"{self.api_search_url}?q=food")
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        
        # Verify that Kyoto Food Tour is in the results
        tour_names = [t['name'] for t in data['tours']]
        self.assertIn("Kyoto Food Tour", tour_names)
        
    def test_search_api_filters(self):
        """
        Test the search API endpoint with filters.
        
        Verifies that the search API correctly applies filters
        to limit the search results to specific types of content.
        """
        # Search for "Japan" with destinations filter
        response = self.client.get(f"{self.api_search_url}?q=Japan&type=destinations")
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('destinations', data)
        self.assertNotIn('tours', data)
        self.assertNotIn('attractions', data)
        self.assertNotIn('itineraries', data)
        
        # Search for "Paris" with tours filter
        response = self.client.get(f"{self.api_search_url}?q=Paris&type=tours")
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertNotIn('destinations', data)
        self.assertIn('tours', data)
        self.assertNotIn('attractions', data)
        self.assertNotIn('itineraries', data)
        
        tour_names = [t['name'] for t in data['tours']]
        self.assertIn("Paris Cultural Experience", tour_names)
        
    def test_search_with_region_filter(self):
        """
        Test searching with a region filter.
        
        Verifies that searching with a region filter returns only
        destinations and tours in that region.
        """
        # Search for destinations in Asia
        response = self.client.get(f"{self.search_url}?q=&region={self.asia_region.id}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tokyo")
        self.assertContains(response, "Kyoto")
        self.assertNotContains(response, "Paris")
        
        # Search for "tour" in Europe region
        response = self.client.get(f"{self.search_url}?q=tour&region={self.europe_region.id}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Paris Cultural Experience")
        self.assertNotContains(response, "Japan Adventure")
        self.assertNotContains(response, "Kyoto Food Tour")
        
    def test_search_with_category_filter(self):
        """
        Test searching with a tour category filter.
        
        Verifies that searching with a category filter returns only
        tours in that category.
        """
        # Search for tours in Adventure category
        response = self.client.get(f"{self.search_url}?q=&category={self.adventure_category.id}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Japan Adventure")
        self.assertNotContains(response, "Paris Cultural Experience")
        self.assertNotContains(response, "Kyoto Food Tour")
        
        # Search for "tour" in Food & Culinary category
        response = self.client.get(f"{self.search_url}?q=tour&category={self.food_category.id}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kyoto Food Tour")
        self.assertNotContains(response, "Japan Adventure")
        self.assertNotContains(response, "Paris Cultural Experience")
        
    def test_search_with_price_range_filter(self):
        """
        Test searching with a price range filter.
        
        Verifies that searching with a price range filter returns only
        tours within that price range.
        """
        # Search for tours with price <= 1000
        response = self.client.get(f"{self.search_url}?q=&max_price=1000")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kyoto Food Tour")  # $800
        self.assertNotContains(response, "Japan Adventure")  # $1500
        self.assertNotContains(response, "Paris Cultural Experience")  # $1200
        
        # Search for tours with price >= 1000
        response = self.client.get(f"{self.search_url}?q=&min_price=1000")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Japan Adventure")  # $1500
        self.assertContains(response, "Paris Cultural Experience")  # $1200
        self.assertNotContains(response, "Kyoto Food Tour")  # $800
        
        # Search for tours with 800 <= price <= 1300
        response = self.client.get(f"{self.search_url}?q=&min_price=800&max_price=1300")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Paris Cultural Experience")  # $1200
        self.assertContains(response, "Kyoto Food Tour")  # $800
        self.assertNotContains(response, "Japan Adventure")  # $1500
        
    def test_search_with_duration_filter(self):
        """
        Test searching with a duration filter.
        
        Verifies that searching with a duration filter returns only
        tours with that duration.
        """
        # Search for tours with duration <= 5 days
        response = self.client.get(f"{self.search_url}?q=&max_duration=5")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Paris Cultural Experience")  # 5 days
        self.assertContains(response, "Kyoto Food Tour")  # 3 days
        self.assertNotContains(response, "Japan Adventure")  # 7 days
        
        # Search for tours with duration >= 5 days
        response = self.client.get(f"{self.search_url}?q=&min_duration=5")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Japan Adventure")  # 7 days
        self.assertContains(response, "Paris Cultural Experience")  # 5 days
        self.assertNotContains(response, "Kyoto Food Tour")  # 3 days
        
    def test_search_with_multiple_filters(self):
        """
        Test searching with multiple filters.
        
        Verifies that searching with multiple filters returns only
        content that matches all filters.
        """
        # Search for tours in Asia region with duration <= 5 days
        response = self.client.get(
            f"{self.search_url}?q=&region={self.asia_region.id}&max_duration=5"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kyoto Food Tour")  # Asia, 3 days
        self.assertNotContains(response, "Japan Adventure")  # Asia, 7 days
        self.assertNotContains(response, "Paris Cultural Experience")  # Europe, 5 days
        
        # Search for tours in Food category with price >= 700
        response = self.client.get(
            f"{self.search_url}?q=&category={self.food_category.id}&min_price=700"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kyoto Food Tour")  # Food, $800
        self.assertNotContains(response, "Japan Adventure")  # Adventure, $1500
        self.assertNotContains(response, "Paris Cultural Experience")  # Cultural, $1200
