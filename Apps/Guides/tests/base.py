"""
Base test case for the TravelGuide project.

This module provides a base test case class with common functionality
that can be inherited by all test cases in the project.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from destinations.models import Destination, Region, Attraction, DestinationImage
from tours.models import Tour, TourCategory, TourDate, TourImage
from reviews.models import Review, ReviewImage, ReviewComment
from accounts.models import Profile

User = get_user_model()

class TravelGuideBaseTestCase(TestCase):
    """
    Base test case for TravelGuide tests.
    
    This class provides common setup and utility methods for all test cases
    in the TravelGuide project. It includes methods for creating test users,
    destinations, tours, and other common objects used in tests.
    """
    
    def setUp(self):
        """
        Set up common test data before each test method runs.
        
        Creates a test user, admin user, region, destination, and tour
        that can be used by test methods.
        """
        # Create test users
        self.test_user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword123'
        )
        
        self.admin_user = User.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='adminpassword123'
        )
        
        # Create a test region
        self.region = Region.objects.create(
            name='Test Region',
            slug='test-region',
            description='A test region description'
        )
        
        # Create a test destination
        self.destination = Destination.objects.create(
            name='Test Destination',
            slug='test-destination',
            description='A test destination description',
            region=self.region,
            price=1000.00,
            rating=4.5,
            latitude=12.345,
            longitude=67.890,
            is_featured=True,
            is_active=True
        )
        
        # Create a destination image
        self.destination_image = DestinationImage.objects.create(
            destination=self.destination,
            image='destinations/test-image.jpg',
            alt_text='Test destination image',
            is_primary=True
        )
        
        # Create a test attraction
        self.attraction = Attraction.objects.create(
            name='Test Attraction',
            description='A test attraction description',
            category='landmark',
            destination=self.destination,
            is_featured=True,
            is_active=True
        )
        
        # Create a tour category
        self.tour_category = TourCategory.objects.create(
            name='Test Category',
            slug='test-category',
            description='A test category description'
        )
        
        # Create a test tour
        self.tour = Tour.objects.create(
            title='Test Tour',
            slug='test-tour',
            description='A test tour description',
            duration=5,
            price=2000.00,
            destination=self.destination,
            is_featured=True,
            is_active=True
        )
        
        # Add category to tour
        self.tour.categories.add(self.tour_category)
        
        # Create a tour date
        self.tour_date = TourDate.objects.create(
            tour=self.tour,
            start_date=timezone.now() + timezone.timedelta(days=30),
            end_date=timezone.now() + timezone.timedelta(days=35),
            price=2000.00,
            available_seats=20
        )
        
        # Create a tour image
        self.tour_image = TourImage.objects.create(
            tour=self.tour,
            image='tours/test-tour-image.jpg',
            alt_text='Test tour image',
            is_primary=True
        )
    
    def create_review(self, user=None, content_object=None, rating=5):
        """
        Create a test review.
        
        Args:
            user: User creating the review (defaults to self.test_user)
            content_object: Object being reviewed (defaults to self.destination)
            rating: Review rating (defaults to 5)
            
        Returns:
            Review: The created review object
        """
        from django.contrib.contenttypes.models import ContentType
        
        if user is None:
            user = self.test_user
            
        if content_object is None:
            content_object = self.destination
            
        content_type = ContentType.objects.get_for_model(content_object)
        
        review = Review.objects.create(
            user=user,
            content_type=content_type,
            object_id=content_object.id,
            title='Test Review',
            content='This is a test review content.',
            rating=rating,
            status='approved'
        )
        
        return review
    
    def login_test_user(self):
        """
        Log in the test user.
        
        Returns:
            bool: True if login successful
        """
        return self.client.login(username='testuser', password='testpassword123')
    
    def login_admin_user(self):
        """
        Log in the admin user.
        
        Returns:
            bool: True if login successful
        """
        return self.client.login(username='adminuser', password='adminpassword123')
