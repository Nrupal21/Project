"""
Test cases for the tours app.

This module contains comprehensive test cases for all functionality
in the tours app, including models, views, forms, and utilities.
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from tours.models import Tour, TourCategory, TourDate, TourImage, TourItinerary
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class TourModelTests(TravelGuideBaseTestCase):
    """
    Tests for the Tour model in the tours app.
    
    These tests verify that Tour objects can be created correctly,
    and that their methods work as expected.
    """
    
    def test_tour_creation(self):
        """
        Test that a Tour can be created with the expected attributes.
        
        Verifies that the Tour model can be instantiated with the required
        fields and that the values are stored correctly.
        """
        tour = Tour.objects.create(
            title='Another Tour',
            slug='another-tour',
            description='Another tour description',
            duration=7,
            price=3000.00,
            destination=self.destination,
            is_featured=False,
            is_active=True
        )
        
        # Verify the tour was created with the correct attributes
        self.assertEqual(tour.title, 'Another Tour')
        self.assertEqual(tour.slug, 'another-tour')
        self.assertEqual(tour.duration, 7)
        self.assertEqual(tour.price, 3000.00)
        self.assertEqual(tour.destination, self.destination)
        
    def test_tour_str_method(self):
        """
        Test the string representation of a Tour object.
        
        Verifies that the __str__ method returns the expected string.
        """
        self.assertEqual(str(self.tour), 'Test Tour')
        
    def test_tour_get_absolute_url(self):
        """
        Test the get_absolute_url method of the Tour model.
        
        Verifies that the URL generated for a tour is correct.
        """
        expected_url = reverse('tours:tour_detail', kwargs={'slug': self.tour.slug})
        self.assertEqual(self.tour.get_absolute_url(), expected_url)
        
    def test_tour_primary_image(self):
        """
        Test that a Tour correctly identifies its primary image.
        
        Verifies that the primary_image property returns the correct image.
        """
        # The primary image should be the one created in setUp
        self.assertEqual(self.tour.primary_image, self.tour_image)
        
    def test_tour_upcoming_dates(self):
        """
        Test that a Tour correctly identifies its upcoming dates.
        
        Verifies that the upcoming_dates property returns dates in the future.
        """
        # Create a past tour date
        past_date = TourDate.objects.create(
            tour=self.tour,
            start_date=timezone.now() - timezone.timedelta(days=30),
            end_date=timezone.now() - timezone.timedelta(days=25),
            price=2000.00,
            available_seats=20
        )
        
        # Create another future tour date
        future_date = TourDate.objects.create(
            tour=self.tour,
            start_date=timezone.now() + timezone.timedelta(days=60),
            end_date=timezone.now() + timezone.timedelta(days=65),
            price=2200.00,
            available_seats=15
        )
        
        # The upcoming dates should include the two future dates (one from setUp + one new)
        upcoming_dates = self.tour.upcoming_dates
        self.assertEqual(upcoming_dates.count(), 2)
        self.assertIn(self.tour_date, upcoming_dates)
        self.assertIn(future_date, upcoming_dates)
        self.assertNotIn(past_date, upcoming_dates)


class TourCategoryModelTests(TravelGuideBaseTestCase):
    """
    Tests for the TourCategory model in the tours app.
    
    These tests verify that TourCategory objects can be created correctly,
    and that their methods work as expected.
    """
    
    def test_category_creation(self):
        """
        Test that a TourCategory can be created with the expected attributes.
        
        Verifies that the TourCategory model can be instantiated with the required
        fields and that the values are stored correctly.
        """
        category = TourCategory.objects.create(
            name='Another Category',
            slug='another-category',
            description='Another category description'
        )
        
        # Verify the category was created with the correct attributes
        self.assertEqual(category.name, 'Another Category')
        self.assertEqual(category.slug, 'another-category')
        self.assertEqual(category.description, 'Another category description')
        
    def test_category_str_method(self):
        """
        Test the string representation of a TourCategory object.
        
        Verifies that the __str__ method returns the expected string.
        """
        self.assertEqual(str(self.tour_category), 'Test Category')
        
    def test_category_get_absolute_url(self):
        """
        Test the get_absolute_url method of the TourCategory model.
        
        Verifies that the URL generated for a category is correct.
        """
        expected_url = reverse('tours:category_detail', kwargs={'slug': self.tour_category.slug})
        self.assertEqual(self.tour_category.get_absolute_url(), expected_url)
        
    def test_category_tours_count(self):
        """
        Test that a TourCategory correctly counts its tours.
        
        Verifies that the tours_count property returns the correct number.
        """
        # Create another tour in the same category
        tour2 = Tour.objects.create(
            title='Another Tour',
            slug='another-tour',
            description='Another tour description',
            duration=7,
            price=3000.00,
            destination=self.destination,
            is_featured=False,
            is_active=True
        )
        tour2.categories.add(self.tour_category)
        
        # The category should now have 2 tours (1 from setup + 1 new)
        self.assertEqual(self.tour_category.tours.count(), 2)


class TourDateModelTests(TravelGuideBaseTestCase):
    """
    Tests for the TourDate model in the tours app.
    
    These tests verify that TourDate objects can be created correctly,
    and that their methods work as expected.
    """
    
    def test_tour_date_creation(self):
        """
        Test that a TourDate can be created with the expected attributes.
        
        Verifies that the TourDate model can be instantiated with the required
        fields and that the values are stored correctly.
        """
        start_date = timezone.now() + timezone.timedelta(days=90)
        end_date = start_date + timezone.timedelta(days=5)
        
        tour_date = TourDate.objects.create(
            tour=self.tour,
            start_date=start_date,
            end_date=end_date,
            price=2500.00,
            available_seats=10
        )
        
        # Verify the tour date was created with the correct attributes
        self.assertEqual(tour_date.tour, self.tour)
        self.assertEqual(tour_date.start_date.date(), start_date.date())
        self.assertEqual(tour_date.end_date.date(), end_date.date())
        self.assertEqual(tour_date.price, 2500.00)
        self.assertEqual(tour_date.available_seats, 10)
        
    def test_tour_date_str_method(self):
        """
        Test the string representation of a TourDate object.
        
        Verifies that the __str__ method returns the expected string.
        """
        expected_str = f"{self.tour.title} ({self.tour_date.start_date.strftime('%Y-%m-%d')})"
        self.assertEqual(str(self.tour_date), expected_str)
        
    def test_tour_date_is_available(self):
        """
        Test the is_available property of the TourDate model.
        
        Verifies that the is_available property correctly determines
        if a tour date has available seats.
        """
        # The tour date created in setUp has 20 available seats
        self.assertTrue(self.tour_date.is_available)
        
        # Set available seats to 0
        self.tour_date.available_seats = 0
        self.tour_date.save()
        
        # The tour date should now be unavailable
        self.assertFalse(self.tour_date.is_available)


class TourItineraryModelTests(TravelGuideBaseTestCase):
    """
    Tests for the TourItinerary model in the tours app.
    
    These tests verify that TourItinerary objects can be created correctly,
    and that their methods work as expected.
    """
    
    def setUp(self):
        """
        Set up test data for TourItinerary tests.
        
        Extends the base setUp method to include a tour itinerary.
        """
        super().setUp()
        
        # Create a tour itinerary
        self.itinerary = TourItinerary.objects.create(
            tour=self.tour,
            day=1,
            title='Day 1: Arrival',
            description='Arrive at the destination and check in to hotel.',
            activities='Airport pickup, hotel check-in, welcome dinner'
        )
    
    def test_itinerary_creation(self):
        """
        Test that a TourItinerary can be created with the expected attributes.
        
        Verifies that the TourItinerary model can be instantiated with the required
        fields and that the values are stored correctly.
        """
        itinerary = TourItinerary.objects.create(
            tour=self.tour,
            day=2,
            title='Day 2: City Tour',
            description='Explore the main attractions of the city.',
            activities='Guided city tour, lunch at local restaurant, free time'
        )
        
        # Verify the itinerary was created with the correct attributes
        self.assertEqual(itinerary.tour, self.tour)
        self.assertEqual(itinerary.day, 2)
        self.assertEqual(itinerary.title, 'Day 2: City Tour')
        
    def test_itinerary_str_method(self):
        """
        Test the string representation of a TourItinerary object.
        
        Verifies that the __str__ method returns the expected string.
        """
        expected_str = f"{self.tour.title} - Day 1: Arrival"
        self.assertEqual(str(self.itinerary), expected_str)
        
    def test_itinerary_ordering(self):
        """
        Test that TourItinerary objects are ordered by day.
        
        Verifies that when multiple itineraries exist for a tour,
        they are returned in order of the day field.
        """
        # Create itineraries for days 2 and 3
        itinerary2 = TourItinerary.objects.create(
            tour=self.tour,
            day=2,
            title='Day 2: City Tour',
            description='Explore the main attractions of the city.',
            activities='Guided city tour, lunch at local restaurant, free time'
        )
        
        itinerary3 = TourItinerary.objects.create(
            tour=self.tour,
            day=3,
            title='Day 3: Beach Day',
            description='Relax at the beach.',
            activities='Beach activities, water sports, sunset dinner'
        )
        
        # Get all itineraries for the tour
        itineraries = TourItinerary.objects.filter(tour=self.tour)
        
        # Verify they are in the correct order
        self.assertEqual(itineraries[0], self.itinerary)  # Day 1
        self.assertEqual(itineraries[1], itinerary2)      # Day 2
        self.assertEqual(itineraries[2], itinerary3)      # Day 3


class TourViewTests(TravelGuideBaseTestCase):
    """
    Tests for the views in the tours app.
    
    These tests verify that the views render the correct templates,
    contain the expected context data, and handle form submissions correctly.
    """
    
    def test_tour_list_view(self):
        """
        Test the tour list view.
        
        Verifies that the tour list view returns a 200 status code,
        uses the correct template, and includes the tours in the context.
        """
        response = self.client.get(reverse('tours:tour_list'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'tours/tour_list.html')
        
        # Check that the tours are in the context
        self.assertIn('tours', response.context)
        self.assertIn(self.tour, response.context['tours'])
        
    def test_tour_detail_view(self):
        """
        Test the tour detail view.
        
        Verifies that the tour detail view returns a 200 status code,
        uses the correct template, and includes the tour in the context.
        """
        response = self.client.get(reverse('tours:tour_detail', kwargs={'slug': self.tour.slug}))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'tours/tour_detail.html')
        
        # Check that the tour is in the context
        self.assertEqual(response.context['tour'], self.tour)
        
    def test_category_list_view(self):
        """
        Test the category list view.
        
        Verifies that the category list view returns a 200 status code,
        uses the correct template, and includes the categories in the context.
        """
        response = self.client.get(reverse('tours:category_list'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'tours/category_list.html')
        
        # Check that the categories are in the context
        self.assertIn('categories', response.context)
        self.assertIn(self.tour_category, response.context['categories'])
        
    def test_category_detail_view(self):
        """
        Test the category detail view.
        
        Verifies that the category detail view returns a 200 status code,
        uses the correct template, and includes the category in the context.
        """
        response = self.client.get(reverse('tours:category_detail', kwargs={'slug': self.tour_category.slug}))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'tours/category_detail.html')
        
        # Check that the category is in the context
        self.assertEqual(response.context['category'], self.tour_category)
        
    def test_search_view(self):
        """
        Test the tour search view.
        
        Verifies that the search view returns a 200 status code,
        uses the correct template, and filters tours correctly.
        """
        # Test with no search parameters
        response = self.client.get(reverse('tours:search'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tours/search_results.html')
        
        # Test with search parameters
        response = self.client.get(reverse('tours:search'), {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.tour, response.context['tours'])
        
        # Test with search parameters that don't match any tours
        response = self.client.get(reverse('tours:search'), {'q': 'NonexistentTour'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['tours']), 0)
