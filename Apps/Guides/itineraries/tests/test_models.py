"""
Tests for the itineraries app models.

This module contains comprehensive test cases for Itinerary, ItineraryDay,
and Activity models to ensure they function correctly.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from itineraries.models import Itinerary, ItineraryDay, Activity
from destinations.models import Destination
from tours.models import Tour

User = get_user_model()


class ItineraryModelTest(TestCase):
    """
    Tests for the Itinerary model.
    
    Verifies model creation, validation rules, and methods related to itineraries.
    """
    
    def setUp(self):
        """
        Set up test data for all test methods.
        
        Creates a test user, tour, and example itinerary.
        """
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Create test tour
        self.tour = Tour.objects.create(
            name='Test Tour',
            description='Test tour description',
            duration=7,
            price=1000.00,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=7)
        )
        
        # Create test itinerary
        self.itinerary = Itinerary.objects.create(
            title='Test Itinerary',
            description='Test description',
            user=self.user,
            tour=self.tour,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=7),
            is_public=True
        )
    
    def test_itinerary_creation(self):
        """
        Test that an itinerary can be created with valid data.
        
        Checks if the itinerary instance is created with the correct attributes.
        """
        self.assertEqual(self.itinerary.title, 'Test Itinerary')
        self.assertEqual(self.itinerary.description, 'Test description')
        self.assertEqual(self.itinerary.user, self.user)
        self.assertEqual(self.itinerary.tour, self.tour)
        self.assertTrue(self.itinerary.is_public)
    
    def test_string_representation(self):
        """
        Test the string representation of an Itinerary instance.
        
        Verifies that the __str__ method returns the itinerary title.
        """
        self.assertEqual(str(self.itinerary), 'Test Itinerary')
    
    def test_get_duration(self):
        """
        Test the get_duration method.
        
        Verifies that the duration is correctly calculated from start_date and end_date.
        """
        # Duration should be end_date - start_date + 1 (inclusive of both days)
        self.assertEqual(self.itinerary.get_duration(), 8)
    
    def test_get_absolute_url(self):
        """
        Test the get_absolute_url method.
        
        Verifies that the URL is correctly generated.
        """
        expected_url = f'/itineraries/{self.itinerary.pk}/'
        self.assertEqual(self.itinerary.get_absolute_url(), expected_url)


class ItineraryDayTest(TestCase):
    """
    Tests for the ItineraryDay model.
    
    Verifies model creation, validation, and relationships with itineraries.
    """
    
    def setUp(self):
        """
        Set up test data for all test methods.
        
        Creates a test user, itinerary, destination, and itinerary day.
        """
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Create test itinerary
        self.itinerary = Itinerary.objects.create(
            title='Test Itinerary',
            description='Test description',
            user=self.user,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=7),
            is_public=True
        )
        
        # Create test destination
        self.destination = Destination.objects.create(
            name='Test Destination',
            country='Test Country',
            description='Test destination description'
        )
        
        # Create test itinerary day
        self.day = ItineraryDay.objects.create(
            itinerary=self.itinerary,
            day_number=1,
            date=self.itinerary.start_date,
            destination=self.destination,
            accommodation_details='Test hotel',
            notes='Test notes'
        )
    
    def test_day_creation(self):
        """
        Test that an itinerary day can be created with valid data.
        
        Checks if the day instance is created with the correct attributes.
        """
        self.assertEqual(self.day.itinerary, self.itinerary)
        self.assertEqual(self.day.day_number, 1)
        self.assertEqual(self.day.date, self.itinerary.start_date)
        self.assertEqual(self.day.destination, self.destination)
        self.assertEqual(self.day.accommodation_details, 'Test hotel')
    
    def test_string_representation(self):
        """
        Test the string representation of an ItineraryDay instance.
        
        Verifies that the __str__ method includes the day number and date.
        """
        expected_str = f"Day 1: {self.day.date.strftime('%Y-%m-%d')}"
        self.assertEqual(str(self.day), expected_str)
    
    def test_ordering(self):
        """
        Test that itinerary days are ordered by day_number.
        
        Verifies the Meta.ordering attribute works correctly.
        """
        # Create a second day
        day2 = ItineraryDay.objects.create(
            itinerary=self.itinerary,
            day_number=2,
            date=self.itinerary.start_date + timedelta(days=1)
        )
        
        # Get all days for this itinerary, should be ordered by day_number
        days = ItineraryDay.objects.filter(itinerary=self.itinerary)
        self.assertEqual(days[0], self.day)  # First day should be day 1
        self.assertEqual(days[1], day2)      # Second day should be day 2


class ActivityTest(TestCase):
    """
    Tests for the Activity model.
    
    Verifies model creation, validation, and relationships with itinerary days.
    """
    
    def setUp(self):
        """
        Set up test data for all test methods.
        
        Creates a test user, itinerary, day, and activity.
        """
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Create test itinerary
        self.itinerary = Itinerary.objects.create(
            title='Test Itinerary',
            description='Test description',
            user=self.user,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=7)
        )
        
        # Create test itinerary day
        self.day = ItineraryDay.objects.create(
            itinerary=self.itinerary,
            day_number=1,
            date=self.itinerary.start_date
        )
        
        # Create test activity with times
        self.activity = Activity.objects.create(
            day=self.day,
            title='Test Activity',
            description='Test description',
            start_time=timezone.now().time(),
            end_time=(timezone.now() + timedelta(hours=2)).time(),
            location='Test location',
            cost=50.00,
            booking_reference='ABC123',
            notes='Test notes'
        )
    
    def test_activity_creation(self):
        """
        Test that an activity can be created with valid data.
        
        Checks if the activity instance is created with the correct attributes.
        """
        self.assertEqual(self.activity.day, self.day)
        self.assertEqual(self.activity.title, 'Test Activity')
        self.assertEqual(self.activity.location, 'Test location')
        self.assertEqual(self.activity.cost, 50.00)
        self.assertEqual(self.activity.booking_reference, 'ABC123')
    
    def test_string_representation(self):
        """
        Test the string representation of an Activity instance.
        
        Verifies that the __str__ method includes the activity title.
        """
        self.assertEqual(str(self.activity), 'Test Activity')
    
    def test_ordering(self):
        """
        Test that activities are ordered by start_time.
        
        Verifies the Meta.ordering attribute works correctly.
        """
        # Create a second activity that starts earlier
        earlier_time = (timezone.now() - timedelta(hours=1)).time()
        activity2 = Activity.objects.create(
            day=self.day,
            title='Earlier Activity',
            start_time=earlier_time
        )
        
        # Get all activities for this day, should be ordered by start_time
        activities = Activity.objects.filter(day=self.day)
        self.assertEqual(activities[0], activity2)  # Earlier activity should be first
        self.assertEqual(activities[1], self.activity)  # Later activity should be second
        
    def test_get_duration_display(self):
        """
        Test the get_duration_display method.
        
        Verifies that the duration is correctly formatted.
        """
        duration_display = self.activity.get_duration_display()
        self.assertIn(self.activity.start_time.strftime('%I:%M %p'), duration_display)
        self.assertIn(self.activity.end_time.strftime('%I:%M %p'), duration_display)
