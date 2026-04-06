"""
Test cases for the itineraries app models.

This module contains comprehensive test cases for all models
in the itineraries app. Every test function is thoroughly documented
to make understanding the tests easier for programmers.
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
import datetime

from itineraries.models import Itinerary, ItineraryItem, SavedItinerary
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class ItineraryModelTests(TravelGuideBaseTestCase):
    """
    Tests for the Itinerary model in the itineraries app.
    
    These tests verify that Itinerary objects can be created correctly,
    and that their methods work as expected. Each test focuses on a 
    specific aspect of the Itinerary model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for Itinerary tests.
        
        Extends the base setUp method to include itineraries for testing.
        """
        super().setUp()
        
        # Create an itinerary for the test user
        self.test_itinerary = Itinerary.objects.create(
            user=self.test_user,
            title="Tokyo Adventure",
            description="A 5-day adventure in Tokyo",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + datetime.timedelta(days=5),
            is_public=True,
            destination=self.test_destination
        )
    
    def test_itinerary_creation(self):
        """
        Test that an Itinerary can be created with the expected attributes.
        
        Verifies that the Itinerary model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new itinerary for the admin user
        itinerary = Itinerary.objects.create(
            user=self.admin_user,
            title="Paris Weekend",
            description="A weekend getaway in Paris",
            start_date=timezone.now().date() + datetime.timedelta(days=30),
            end_date=timezone.now().date() + datetime.timedelta(days=32),
            is_public=False,
            destination=self.create_destination("Paris", self.test_region)
        )
        
        # Verify the itinerary was created with the correct attributes
        self.assertEqual(itinerary.user, self.admin_user)
        self.assertEqual(itinerary.title, "Paris Weekend")
        self.assertEqual(itinerary.description, "A weekend getaway in Paris")
        self.assertEqual(itinerary.start_date, timezone.now().date() + datetime.timedelta(days=30))
        self.assertEqual(itinerary.end_date, timezone.now().date() + datetime.timedelta(days=32))
        self.assertFalse(itinerary.is_public)
        self.assertEqual(itinerary.destination.name, "Paris")
        
    def test_itinerary_str_method(self):
        """
        Test the string representation of an Itinerary object.
        
        Verifies that the __str__ method returns the expected string,
        which should be the itinerary title.
        """
        self.assertEqual(str(self.test_itinerary), "Tokyo Adventure")
        
    def test_itinerary_get_absolute_url(self):
        """
        Test the get_absolute_url method of the Itinerary model.
        
        Verifies that the URL generated for an itinerary detail page is correct
        and matches the expected URL pattern.
        """
        expected_url = reverse('itineraries:detail', kwargs={'pk': self.test_itinerary.pk})
        self.assertEqual(self.test_itinerary.get_absolute_url(), expected_url)
        
    def test_itinerary_duration(self):
        """
        Test the duration property of the Itinerary model.
        
        Verifies that the duration property correctly calculates
        the number of days between start_date and end_date.
        """
        # The duration should be 5 days
        self.assertEqual(self.test_itinerary.duration, 5)
        
        # Change the end date to 10 days after the start date
        self.test_itinerary.end_date = self.test_itinerary.start_date + datetime.timedelta(days=10)
        self.test_itinerary.save()
        
        # Now the duration should be 10 days
        self.assertEqual(self.test_itinerary.duration, 10)
        
    def test_itinerary_days(self):
        """
        Test the days property of the Itinerary model.
        
        Verifies that the days property correctly returns a list of dates
        between start_date and end_date.
        """
        # The itinerary is 5 days long
        days = self.test_itinerary.days
        
        # Verify that the list contains 6 dates (start date to end date inclusive)
        self.assertEqual(len(days), 6)
        
        # Verify that the first date is the start date
        self.assertEqual(days[0], self.test_itinerary.start_date)
        
        # Verify that the last date is the end date
        self.assertEqual(days[-1], self.test_itinerary.end_date)
        
    def test_itinerary_items_by_day(self):
        """
        Test the items_by_day method of the Itinerary model.
        
        Verifies that the items_by_day method correctly groups
        itinerary items by day.
        """
        # Create some itinerary items
        item1 = ItineraryItem.objects.create(
            itinerary=self.test_itinerary,
            day=1,
            time="09:00",
            title="Visit Tokyo Tower",
            description="Enjoy the view from Tokyo Tower",
            location="Tokyo Tower, Minato City, Tokyo",
            duration=120  # 2 hours
        )
        
        item2 = ItineraryItem.objects.create(
            itinerary=self.test_itinerary,
            day=1,
            time="14:00",
            title="Lunch in Shibuya",
            description="Enjoy lunch at a local restaurant",
            location="Shibuya, Tokyo",
            duration=60  # 1 hour
        )
        
        item3 = ItineraryItem.objects.create(
            itinerary=self.test_itinerary,
            day=2,
            time="10:00",
            title="Visit Senso-ji Temple",
            description="Explore the ancient temple",
            location="Senso-ji, Asakusa, Tokyo",
            duration=180  # 3 hours
        )
        
        # Get items grouped by day
        items_by_day = self.test_itinerary.items_by_day()
        
        # Verify that there are items for days 1 and 2
        self.assertIn(1, items_by_day)
        self.assertIn(2, items_by_day)
        
        # Verify that day 1 has 2 items
        self.assertEqual(len(items_by_day[1]), 2)
        
        # Verify that day 2 has 1 item
        self.assertEqual(len(items_by_day[2]), 1)
        
        # Verify that the items are in the correct order (by time)
        self.assertEqual(items_by_day[1][0], item1)
        self.assertEqual(items_by_day[1][1], item2)
        self.assertEqual(items_by_day[2][0], item3)


class ItineraryItemModelTests(TravelGuideBaseTestCase):
    """
    Tests for the ItineraryItem model in the itineraries app.
    
    These tests verify that ItineraryItem objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the ItineraryItem model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for ItineraryItem tests.
        
        Extends the base setUp method to include itineraries and items for testing.
        """
        super().setUp()
        
        # Create an itinerary for the test user
        self.test_itinerary = Itinerary.objects.create(
            user=self.test_user,
            title="Tokyo Adventure",
            description="A 5-day adventure in Tokyo",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + datetime.timedelta(days=5),
            is_public=True,
            destination=self.test_destination
        )
        
        # Create an itinerary item
        self.test_item = ItineraryItem.objects.create(
            itinerary=self.test_itinerary,
            day=1,
            time="09:00",
            title="Visit Tokyo Tower",
            description="Enjoy the view from Tokyo Tower",
            location="Tokyo Tower, Minato City, Tokyo",
            duration=120  # 2 hours
        )
    
    def test_itinerary_item_creation(self):
        """
        Test that an ItineraryItem can be created with the expected attributes.
        
        Verifies that the ItineraryItem model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new itinerary item
        item = ItineraryItem.objects.create(
            itinerary=self.test_itinerary,
            day=2,
            time="10:00",
            title="Visit Senso-ji Temple",
            description="Explore the ancient temple",
            location="Senso-ji, Asakusa, Tokyo",
            duration=180  # 3 hours
        )
        
        # Verify the item was created with the correct attributes
        self.assertEqual(item.itinerary, self.test_itinerary)
        self.assertEqual(item.day, 2)
        self.assertEqual(item.time, "10:00")
        self.assertEqual(item.title, "Visit Senso-ji Temple")
        self.assertEqual(item.description, "Explore the ancient temple")
        self.assertEqual(item.location, "Senso-ji, Asakusa, Tokyo")
        self.assertEqual(item.duration, 180)
        
    def test_itinerary_item_str_method(self):
        """
        Test the string representation of an ItineraryItem object.
        
        Verifies that the __str__ method returns the expected string,
        which should include the day, time, and title.
        """
        expected_str = "Day 1, 09:00: Visit Tokyo Tower"
        self.assertEqual(str(self.test_item), expected_str)
        
    def test_itinerary_item_formatted_duration(self):
        """
        Test the formatted_duration property of the ItineraryItem model.
        
        Verifies that the formatted_duration property correctly formats
        the duration in hours and minutes.
        """
        # 120 minutes = 2 hours
        self.assertEqual(self.test_item.formatted_duration, "2 hours")
        
        # Create an item with a duration that includes minutes
        item = ItineraryItem.objects.create(
            itinerary=self.test_itinerary,
            day=2,
            time="10:00",
            title="Visit Senso-ji Temple",
            description="Explore the ancient temple",
            location="Senso-ji, Asakusa, Tokyo",
            duration=90  # 1 hour 30 minutes
        )
        
        # 90 minutes = 1 hour 30 minutes
        self.assertEqual(item.formatted_duration, "1 hour 30 minutes")
        
        # Create an item with a duration less than 1 hour
        item = ItineraryItem.objects.create(
            itinerary=self.test_itinerary,
            day=2,
            time="14:00",
            title="Coffee Break",
            description="Quick coffee break",
            location="Cafe, Tokyo",
            duration=30  # 30 minutes
        )
        
        # 30 minutes
        self.assertEqual(item.formatted_duration, "30 minutes")
        
    def test_itinerary_item_end_time(self):
        """
        Test the end_time property of the ItineraryItem model.
        
        Verifies that the end_time property correctly calculates
        the end time based on the start time and duration.
        """
        # Start time is 09:00, duration is 120 minutes (2 hours)
        # End time should be 11:00
        self.assertEqual(self.test_item.end_time, "11:00")
        
        # Create an item that crosses into the next hour with minutes
        item = ItineraryItem.objects.create(
            itinerary=self.test_itinerary,
            day=2,
            time="10:30",
            title="Visit Senso-ji Temple",
            description="Explore the ancient temple",
            location="Senso-ji, Asakusa, Tokyo",
            duration=90  # 1 hour 30 minutes
        )
        
        # Start time is 10:30, duration is 90 minutes (1 hour 30 minutes)
        # End time should be 12:00
        self.assertEqual(item.end_time, "12:00")
        
        # Create an item that crosses into the next day
        item = ItineraryItem.objects.create(
            itinerary=self.test_itinerary,
            day=2,
            time="23:00",
            title="Night Tour",
            description="Late night tour of Tokyo",
            location="Tokyo, Japan",
            duration=120  # 2 hours
        )
        
        # Start time is 23:00, duration is 120 minutes (2 hours)
        # End time should be 01:00
        self.assertEqual(item.end_time, "01:00")


class SavedItineraryModelTests(TravelGuideBaseTestCase):
    """
    Tests for the SavedItinerary model in the itineraries app.
    
    These tests verify that SavedItinerary objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the SavedItinerary model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for SavedItinerary tests.
        
        Extends the base setUp method to include itineraries and saved itineraries for testing.
        """
        super().setUp()
        
        # Create an itinerary for the admin user
        self.admin_itinerary = Itinerary.objects.create(
            user=self.admin_user,
            title="Tokyo Adventure",
            description="A 5-day adventure in Tokyo",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + datetime.timedelta(days=5),
            is_public=True,
            destination=self.test_destination
        )
        
        # Create a saved itinerary for the test user
        self.saved_itinerary = SavedItinerary.objects.create(
            user=self.test_user,
            itinerary=self.admin_itinerary,
            notes="Looks like a great itinerary to follow"
        )
    
    def test_saved_itinerary_creation(self):
        """
        Test that a SavedItinerary can be created with the expected attributes.
        
        Verifies that the SavedItinerary model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create another itinerary
        itinerary = Itinerary.objects.create(
            user=self.admin_user,
            title="Paris Weekend",
            description="A weekend getaway in Paris",
            start_date=timezone.now().date() + datetime.timedelta(days=30),
            end_date=timezone.now().date() + datetime.timedelta(days=32),
            is_public=True,
            destination=self.create_destination("Paris", self.test_region)
        )
        
        # Create a new saved itinerary
        saved = SavedItinerary.objects.create(
            user=self.test_user,
            itinerary=itinerary,
            notes="Planning to use this for my Paris trip"
        )
        
        # Verify the saved itinerary was created with the correct attributes
        self.assertEqual(saved.user, self.test_user)
        self.assertEqual(saved.itinerary, itinerary)
        self.assertEqual(saved.notes, "Planning to use this for my Paris trip")
        self.assertIsNotNone(saved.saved_at)
        
    def test_saved_itinerary_str_method(self):
        """
        Test the string representation of a SavedItinerary object.
        
        Verifies that the __str__ method returns the expected string,
        which should include the user's username and the itinerary title.
        """
        expected_str = f"testuser saved Tokyo Adventure"
        self.assertEqual(str(self.saved_itinerary), expected_str)
        
    def test_saved_itinerary_unique_constraint(self):
        """
        Test the unique constraint on SavedItinerary.
        
        Verifies that a user cannot save the same itinerary twice.
        """
        # Try to create another saved itinerary for the same user and itinerary
        with self.assertRaises(Exception):  # Should raise an integrity error
            SavedItinerary.objects.create(
                user=self.test_user,
                itinerary=self.admin_itinerary,
                notes="Another note"
            )
