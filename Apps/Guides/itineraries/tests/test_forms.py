"""
Tests for the itineraries app forms.

This module contains comprehensive test cases for ItineraryForm, ItineraryDayForm,
and ActivityForm to ensure proper validation and functionality.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from itineraries.forms import ItineraryForm, ItineraryDayForm, ActivityForm
from itineraries.models import Itinerary, ItineraryDay, Activity
from destinations.models import Destination
from tours.models import Tour

User = get_user_model()


class ItineraryFormTest(TestCase):
    """
    Tests for the ItineraryForm class.
    
    Verifies form validation, custom error messages, and proper behavior
    when saving form data.
    """
    
    def setUp(self):
        """
        Set up test data for all test methods.
        
        Creates a test user and tour for form testing.
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
    
    def test_form_valid_data(self):
        """
        Test that the form accepts valid data.
        
        Verifies that form validation passes for correctly formed data.
        """
        # Create form data
        today = timezone.now().date()
        end_date = today + timedelta(days=7)
        
        form_data = {
            'title': 'Test Itinerary',
            'description': 'Test description',
            'tour': self.tour.id,
            'start_date': today,
            'end_date': end_date,
            'is_public': True
        }
        
        form = ItineraryForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
    
    def test_form_invalid_dates(self):
        """
        Test that the form rejects invalid date combinations.
        
        Verifies that validation fails when end_date is before start_date.
        """
        # Create form data with end_date before start_date
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        form_data = {
            'title': 'Test Itinerary',
            'description': 'Test description',
            'start_date': today,
            'end_date': yesterday,  # Invalid: end date before start date
            'is_public': True
        }
        
        form = ItineraryForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('end_date', form.errors)
    
    def test_form_invalid_tour_dates(self):
        """
        Test validation of tour dates against itinerary dates.
        
        Verifies that validation fails when itinerary dates don't match tour dates.
        """
        # Create form data with dates outside the tour's range
        tour_start = self.tour.start_date
        tour_end = self.tour.end_date
        
        # Itinerary starts before tour
        form_data = {
            'title': 'Test Itinerary',
            'description': 'Test description',
            'tour': self.tour.id,
            'start_date': tour_start - timedelta(days=2),  # Invalid: before tour start
            'end_date': tour_end,
            'is_public': True
        }
        
        form = ItineraryForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('start_date', form.errors)
        
        # Itinerary ends after tour
        form_data = {
            'title': 'Test Itinerary',
            'description': 'Test description',
            'tour': self.tour.id,
            'start_date': tour_start,
            'end_date': tour_end + timedelta(days=2),  # Invalid: after tour end
            'is_public': True
        }
        
        form = ItineraryForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('end_date', form.errors)
    
    def test_form_save_with_user(self):
        """
        Test that the form correctly saves the user association.
        
        Verifies that the save method associates the itinerary with the current user.
        """
        # Create form data
        today = timezone.now().date()
        end_date = today + timedelta(days=7)
        
        form_data = {
            'title': 'Test Itinerary',
            'description': 'Test description',
            'start_date': today,
            'end_date': end_date,
            'is_public': True
        }
        
        form = ItineraryForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
        
        # Save the form
        itinerary = form.save()
        
        # Verify the user is set correctly
        self.assertEqual(itinerary.user, self.user)
    
    def test_form_required_fields(self):
        """
        Test that required fields are enforced.
        
        Verifies that validation fails when required fields are missing.
        """
        # Create incomplete form data (missing title and dates)
        form_data = {
            'description': 'Test description',
            'is_public': True
        }
        
        form = ItineraryForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
        self.assertIn('start_date', form.errors)
        self.assertIn('end_date', form.errors)


class ItineraryDayFormTest(TestCase):
    """
    Tests for the ItineraryDayForm class.
    
    Verifies form validation and proper behavior when saving form data.
    """
    
    def setUp(self):
        """
        Set up test data for all test methods.
        
        Creates a test user, itinerary, and destination for form testing.
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
        
        # Create test day
        self.day = ItineraryDay.objects.create(
            itinerary=self.itinerary,
            day_number=1,
            date=self.itinerary.start_date
        )
        
        # Create test destination
        self.destination = Destination.objects.create(
            name='Test Destination',
            country='Test Country',
            description='Test destination description'
        )
    
    def test_form_valid_data(self):
        """
        Test that the form accepts valid data.
        
        Verifies that form validation passes for correctly formed data.
        """
        form_data = {
            'destination': self.destination.id,
            'accommodation_details': 'Test Hotel',
            'notes': 'Test notes for this day'
        }
        
        form = ItineraryDayForm(data=form_data, instance=self.day)
        self.assertTrue(form.is_valid())
    
    def test_form_empty_fields(self):
        """
        Test that the form accepts empty optional fields.
        
        Verifies that validation passes when optional fields are left blank.
        """
        form_data = {
            'destination': '',  # Optional
            'accommodation_details': '',  # Optional
            'notes': ''  # Optional
        }
        
        form = ItineraryDayForm(data=form_data, instance=self.day)
        self.assertTrue(form.is_valid())
    
    def test_form_save(self):
        """
        Test that the form correctly saves changes to a day.
        
        Verifies that the form updates all fields correctly.
        """
        form_data = {
            'destination': self.destination.id,
            'accommodation_details': 'Luxury Hotel',
            'notes': 'Special notes for this day'
        }
        
        form = ItineraryDayForm(data=form_data, instance=self.day)
        self.assertTrue(form.is_valid())
        
        # Save the form
        updated_day = form.save()
        
        # Verify the fields are updated correctly
        self.assertEqual(updated_day.destination, self.destination)
        self.assertEqual(updated_day.accommodation_details, 'Luxury Hotel')
        self.assertEqual(updated_day.notes, 'Special notes for this day')


class ActivityFormTest(TestCase):
    """
    Tests for the ActivityForm class.
    
    Verifies form validation, time handling, and proper behavior when saving form data.
    """
    
    def setUp(self):
        """
        Set up test data for all test methods.
        
        Creates a test user, itinerary, and day for form testing.
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
        
        # Create test day
        self.day = ItineraryDay.objects.create(
            itinerary=self.itinerary,
            day_number=1,
            date=self.itinerary.start_date
        )
    
    def test_form_valid_data(self):
        """
        Test that the form accepts valid data.
        
        Verifies that form validation passes for correctly formed data.
        """
        # Get current time and later time for testing
        now = timezone.now().time()
        later = (timezone.now() + timedelta(hours=2)).time()
        
        form_data = {
            'title': 'Test Activity',
            'start_time': now.strftime('%H:%M'),
            'end_time': later.strftime('%H:%M'),
            'location': 'Test Location',
            'description': 'Test activity description',
            'cost': 50.00,
            'booking_reference': 'ABC123',
            'notes': 'Test notes'
        }
        
        form = ActivityForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_invalid_times(self):
        """
        Test that the form rejects invalid time combinations.
        
        Verifies that validation fails when end_time is before or equal to start_time.
        """
        # Get current time for testing
        now = timezone.now().time()
        earlier = (timezone.now() - timedelta(hours=1)).time()
        
        # End time before start time
        form_data = {
            'title': 'Test Activity',
            'start_time': now.strftime('%H:%M'),
            'end_time': earlier.strftime('%H:%M'),  # Invalid: end time before start time
            'location': 'Test Location'
        }
        
        form = ActivityForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('end_time', form.errors)
        
        # End time same as start time
        form_data = {
            'title': 'Test Activity',
            'start_time': now.strftime('%H:%M'),
            'end_time': now.strftime('%H:%M'),  # Invalid: end time same as start time
            'location': 'Test Location'
        }
        
        form = ActivityForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('end_time', form.errors)
    
    def test_form_optional_fields(self):
        """
        Test that optional fields are truly optional.
        
        Verifies that validation passes when optional fields are left blank.
        """
        form_data = {
            'title': 'Test Activity',  # Only required field
            'start_time': '',  # Optional
            'end_time': '',  # Optional
            'location': '',  # Optional
            'description': '',  # Optional
            'cost': '',  # Optional
            'booking_reference': '',  # Optional
            'notes': ''  # Optional
        }
        
        form = ActivityForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_save(self):
        """
        Test that the form correctly creates a new activity.
        
        Verifies that the form creates an activity with the correct fields.
        """
        # Get current time and later time for testing
        now = timezone.now().time()
        later = (timezone.now() + timedelta(hours=2)).time()
        
        form_data = {
            'title': 'Museum Visit',
            'start_time': now.strftime('%H:%M'),
            'end_time': later.strftime('%H:%M'),
            'location': 'City Museum',
            'description': 'Visit to the city museum',
            'cost': 25.00,
            'booking_reference': 'MUS123',
            'notes': 'Guided tour available'
        }
        
        form = ActivityForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Save the form as a new activity for the day
        activity = form.save(commit=False)
        activity.day = self.day
        activity.save()
        
        # Verify the activity was created correctly
        self.assertEqual(activity.title, 'Museum Visit')
        self.assertEqual(activity.location, 'City Museum')
        self.assertEqual(float(activity.cost), 25.00)
        self.assertEqual(activity.booking_reference, 'MUS123')
