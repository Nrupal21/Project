"""
Tests for the itineraries app views.

This module contains comprehensive test cases for views including list, detail,
create, update, delete views for itineraries, as well as day and activity management views.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from itineraries.models import Itinerary, ItineraryDay, Activity
from itineraries.forms import ItineraryForm, ItineraryDayForm, ActivityForm

User = get_user_model()


class ItineraryListViewTest(TestCase):
    """
    Test the ItineraryListView.
    
    Verifies that the view correctly displays public itineraries,
    handles pagination, and filters as expected.
    """
    
    def setUp(self):
        """
        Set up test data for all test methods.
        
        Creates multiple users and itineraries with different visibility settings.
        """
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='password123'
        )
        
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='password123'
        )
        
        # Create public and private itineraries for both users
        # User 1 itineraries
        self.public_itinerary1 = Itinerary.objects.create(
            title='Public Itinerary 1',
            description='Test description',
            user=self.user1,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=7),
            is_public=True
        )
        
        self.private_itinerary1 = Itinerary.objects.create(
            title='Private Itinerary 1',
            description='Test description',
            user=self.user1,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=7),
            is_public=False
        )
        
        # User 2 itineraries
        self.public_itinerary2 = Itinerary.objects.create(
            title='Public Itinerary 2',
            description='Test description',
            user=self.user2,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=7),
            is_public=True
        )
        
        self.private_itinerary2 = Itinerary.objects.create(
            title='Private Itinerary 2',
            description='Test description',
            user=self.user2,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=7),
            is_public=False
        )
        
        # Set up the test client
        self.client = Client()
    
    def test_view_url_exists_at_desired_location(self):
        """
        Test that the itinerary list view is accessible at the expected URL.
        
        Verifies the URL routing is working correctly.
        """
        response = self.client.get('/itineraries/')
        self.assertEqual(response.status_code, 200)
    
    def test_view_url_accessible_by_name(self):
        """
        Test that the itinerary list view is accessible by its name.
        
        Verifies that the named URL pattern works correctly.
        """
        response = self.client.get(reverse('itineraries:itinerary_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_view_uses_correct_template(self):
        """
        Test that the itinerary list view uses the correct template.
        
        Verifies template rendering is working as expected.
        """
        response = self.client.get(reverse('itineraries:itinerary_list'))
        self.assertTemplateUsed(response, 'itineraries/itinerary_list.html')
    
    def test_only_public_itineraries_in_list(self):
        """
        Test that only public itineraries are displayed in the list.
        
        Verifies filtering by is_public flag works correctly.
        """
        response = self.client.get(reverse('itineraries:itinerary_list'))
        self.assertContains(response, 'Public Itinerary 1')
        self.assertContains(response, 'Public Itinerary 2')
        self.assertNotContains(response, 'Private Itinerary 1')
        self.assertNotContains(response, 'Private Itinerary 2')


class MyItinerariesViewTest(TestCase):
    """
    Test the MyItinerariesView.
    
    Verifies that the view correctly displays only the logged-in user's itineraries,
    regardless of their visibility status.
    """
    
    def setUp(self):
        """
        Set up test data for all test methods.
        
        Creates multiple users and itineraries with different visibility settings.
        """
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='password123'
        )
        
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='password123'
        )
        
        # Create public and private itineraries for both users
        # User 1 itineraries
        self.public_itinerary1 = Itinerary.objects.create(
            title='Public Itinerary 1',
            description='Test description',
            user=self.user1,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=7),
            is_public=True
        )
        
        self.private_itinerary1 = Itinerary.objects.create(
            title='Private Itinerary 1',
            description='Test description',
            user=self.user1,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=7),
            is_public=False
        )
        
        # User 2 itineraries
        self.public_itinerary2 = Itinerary.objects.create(
            title='Public Itinerary 2',
            description='Test description',
            user=self.user2,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=7),
            is_public=True
        )
        
        self.private_itinerary2 = Itinerary.objects.create(
            title='Private Itinerary 2',
            description='Test description',
            user=self.user2,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=7),
            is_public=False
        )
        
        # Set up the test client
        self.client = Client()
    
    def test_redirect_if_not_logged_in(self):
        """
        Test that unauthenticated users are redirected to the login page.
        
        Verifies authentication protection works correctly.
        """
        response = self.client.get(reverse('itineraries:my_itineraries'))
        self.assertRedirects(
            response, 
            f'/accounts/login/?next={reverse("itineraries:my_itineraries")}'
        )
    
    def test_logged_in_user_sees_only_own_itineraries(self):
        """
        Test that a logged-in user only sees their own itineraries.
        
        Verifies that user filtering works correctly.
        """
        # Log in as user1
        self.client.login(username='testuser1', password='password123')
        response = self.client.get(reverse('itineraries:my_itineraries'))
        
        # Check that user1 sees their own itineraries only
        self.assertContains(response, 'Public Itinerary 1')
        self.assertContains(response, 'Private Itinerary 1')
        self.assertNotContains(response, 'Public Itinerary 2')
        self.assertNotContains(response, 'Private Itinerary 2')


class ItineraryDetailViewTest(TestCase):
    """
    Test the ItineraryDetailView.
    
    Verifies that the view correctly displays itinerary details, handles
    permissions properly, and includes related days and activities.
    """
    
    def setUp(self):
        """
        Set up test data for all test methods.
        
        Creates users, itineraries, days, and activities for testing.
        """
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='password123'
        )
        
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='password123'
        )
        
        # Create public and private itineraries
        self.public_itinerary = Itinerary.objects.create(
            title='Public Itinerary',
            description='Test description',
            user=self.user1,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=2),
            is_public=True
        )
        
        self.private_itinerary = Itinerary.objects.create(
            title='Private Itinerary',
            description='Test description',
            user=self.user1,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=2),
            is_public=False
        )
        
        # Create days for the public itinerary
        self.day1 = ItineraryDay.objects.create(
            itinerary=self.public_itinerary,
            day_number=1,
            date=self.public_itinerary.start_date
        )
        
        self.day2 = ItineraryDay.objects.create(
            itinerary=self.public_itinerary,
            day_number=2,
            date=self.public_itinerary.start_date + timedelta(days=1)
        )
        
        # Create activities for day 1
        self.activity1 = Activity.objects.create(
            day=self.day1,
            title='Morning Activity',
            start_time=timezone.now().time(),
            end_time=(timezone.now() + timedelta(hours=2)).time()
        )
        
        self.activity2 = Activity.objects.create(
            day=self.day1,
            title='Afternoon Activity',
            start_time=(timezone.now() + timedelta(hours=4)).time(),
            end_time=(timezone.now() + timedelta(hours=6)).time()
        )
        
        # Set up the test client
        self.client = Client()
    
    def test_public_itinerary_visible_to_all(self):
        """
        Test that a public itinerary is visible to all users.
        
        Verifies that public itineraries are accessible without authentication.
        """
        # Test without login
        response = self.client.get(
            reverse('itineraries:itinerary_detail', kwargs={'pk': self.public_itinerary.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Public Itinerary')
    
    def test_private_itinerary_visible_only_to_owner(self):
        """
        Test that a private itinerary is only visible to its owner.
        
        Verifies permission handling for private content.
        """
        # Test without login - should get permission denied
        response = self.client.get(
            reverse('itineraries:itinerary_detail', kwargs={'pk': self.private_itinerary.pk})
        )
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Login as user2 (not the owner) - should still get permission denied
        self.client.login(username='testuser2', password='password123')
        response = self.client.get(
            reverse('itineraries:itinerary_detail', kwargs={'pk': self.private_itinerary.pk})
        )
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Login as user1 (the owner) - should be able to view
        self.client.login(username='testuser1', password='password123')
        response = self.client.get(
            reverse('itineraries:itinerary_detail', kwargs={'pk': self.private_itinerary.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Private Itinerary')
    
    def test_days_and_activities_displayed(self):
        """
        Test that itinerary days and activities are displayed on the detail page.
        
        Verifies that related objects are correctly included.
        """
        response = self.client.get(
            reverse('itineraries:itinerary_detail', kwargs={'pk': self.public_itinerary.pk})
        )
        
        # Check that days are displayed
        self.assertContains(response, f'Day 1: {self.day1.date.strftime("%A, %B %-d, %Y")}', html=True)
        self.assertContains(response, f'Day 2: {self.day2.date.strftime("%A, %B %-d, %Y")}', html=True)
        
        # Check that activities are displayed
        self.assertContains(response, 'Morning Activity')
        self.assertContains(response, 'Afternoon Activity')


class ItineraryCreateViewTest(TestCase):
    """
    Test the ItineraryCreateView.
    
    Verifies form display, validation, saving, and permissions for creating itineraries.
    """
    
    def setUp(self):
        """
        Set up test data for all test methods.
        
        Creates a test user and client for testing form submission.
        """
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Set up the test client
        self.client = Client()
    
    def test_redirect_if_not_logged_in(self):
        """
        Test that unauthenticated users are redirected to login page.
        
        Verifies authentication requirement works correctly.
        """
        response = self.client.get(reverse('itineraries:itinerary_create'))
        self.assertRedirects(
            response, 
            f'/accounts/login/?next={reverse("itineraries:itinerary_create")}'
        )
    
    def test_logged_in_user_can_access_create_form(self):
        """
        Test that authenticated users can access the create form.
        
        Verifies form display works correctly for authenticated users.
        """
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('itineraries:itinerary_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'itineraries/itinerary_form.html')
    
    def test_form_valid_submission(self):
        """
        Test that a valid form submission creates a new itinerary.
        
        Verifies form processing and database update work correctly.
        """
        self.client.login(username='testuser', password='password123')
        
        # Create post data
        today = timezone.now().date()
        end_date = today + timedelta(days=7)
        
        form_data = {
            'title': 'New Test Itinerary',
            'description': 'Creating a new itinerary through the form',
            'start_date': today.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'is_public': True
        }
        
        # Submit the form
        response = self.client.post(
            reverse('itineraries:itinerary_create'),
            data=form_data,
            follow=True  # Follow redirects
        )
        
        # Check that the itinerary was created
        self.assertEqual(Itinerary.objects.count(), 1)
        
        # Check that the itinerary has correct data
        itinerary = Itinerary.objects.first()
        self.assertEqual(itinerary.title, 'New Test Itinerary')
        self.assertEqual(itinerary.user, self.user)
        
        # Check that days were created automatically
        self.assertEqual(ItineraryDay.objects.count(), 8)  # 8 days including both start and end
    
    def test_form_invalid_submission(self):
        """
        Test that an invalid form submission does not create an itinerary.
        
        Verifies form validation works correctly.
        """
        self.client.login(username='testuser', password='password123')
        
        # Create invalid post data (end_date before start_date)
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        form_data = {
            'title': 'Invalid Itinerary',
            'description': 'This should fail validation',
            'start_date': today.strftime('%Y-%m-%d'),
            'end_date': yesterday.strftime('%Y-%m-%d'),  # Invalid: end date before start date
            'is_public': True
        }
        
        # Submit the form
        response = self.client.post(
            reverse('itineraries:itinerary_create'),
            data=form_data
        )
        
        # Check that the form was not valid and no itinerary was created
        self.assertEqual(response.status_code, 200)  # Form redisplayed
        self.assertEqual(Itinerary.objects.count(), 0)  # No itinerary created
