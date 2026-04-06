"""
Test cases for the itineraries app views.

This module contains comprehensive test cases for all views
in the itineraries app. Every test function is thoroughly documented
to make understanding the tests easier for programmers.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
import datetime
import json

from itineraries.models import Itinerary, ItineraryItem, SavedItinerary
from itineraries.forms import ItineraryForm, ItineraryItemForm
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class ItineraryViewTests(TravelGuideBaseTestCase):
    """
    Tests for the views in the itineraries app.
    
    These tests verify that the views in the itineraries app work as expected,
    including list views, detail views, create views, update views, and delete views.
    Each test focuses on a specific view and its functionality.
    """
    
    def setUp(self):
        """
        Set up test data for itinerary view tests.
        
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
        
        # Create an itinerary for the admin user
        self.admin_itinerary = Itinerary.objects.create(
            user=self.admin_user,
            title="Paris Weekend",
            description="A weekend getaway in Paris",
            start_date=timezone.now().date() + datetime.timedelta(days=30),
            end_date=timezone.now().date() + datetime.timedelta(days=32),
            is_public=True,
            destination=self.create_destination("Paris", self.test_region)
        )
        
        # Create a private itinerary for the admin user
        self.admin_private_itinerary = Itinerary.objects.create(
            user=self.admin_user,
            title="Secret Getaway",
            description="A private vacation",
            start_date=timezone.now().date() + datetime.timedelta(days=60),
            end_date=timezone.now().date() + datetime.timedelta(days=65),
            is_public=False,
            destination=self.test_destination
        )
        
        # Create some itinerary items
        self.test_item = ItineraryItem.objects.create(
            itinerary=self.test_itinerary,
            day=1,
            time="09:00",
            title="Visit Tokyo Tower",
            description="Enjoy the view from Tokyo Tower",
            location="Tokyo Tower, Minato City, Tokyo",
            duration=120  # 2 hours
        )
        
        # URLs for testing
        self.itinerary_list_url = reverse('itineraries:list')
        self.itinerary_create_url = reverse('itineraries:create')
        self.itinerary_detail_url = reverse('itineraries:detail', kwargs={'pk': self.test_itinerary.pk})
        self.itinerary_update_url = reverse('itineraries:update', kwargs={'pk': self.test_itinerary.pk})
        self.itinerary_delete_url = reverse('itineraries:delete', kwargs={'pk': self.test_itinerary.pk})
        
    def test_itinerary_list_view(self):
        """
        Test the itinerary list view.
        
        Verifies that the list view displays public itineraries for anonymous users,
        and both public and the user's own private itineraries for authenticated users.
        """
        # Anonymous user should see only public itineraries
        response = self.client.get(self.itinerary_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.test_itinerary, response.context['itinerary_list'])
        self.assertIn(self.admin_itinerary, response.context['itinerary_list'])
        self.assertNotIn(self.admin_private_itinerary, response.context['itinerary_list'])
        
        # Logged in user should see public itineraries and their own private ones
        self.client.login(username='testuser', password='password')
        response = self.client.get(self.itinerary_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.test_itinerary, response.context['itinerary_list'])
        self.assertIn(self.admin_itinerary, response.context['itinerary_list'])
        self.assertNotIn(self.admin_private_itinerary, response.context['itinerary_list'])
        
        # Admin user should see public itineraries and their own private ones
        self.client.login(username='admin', password='password')
        response = self.client.get(self.itinerary_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.test_itinerary, response.context['itinerary_list'])
        self.assertIn(self.admin_itinerary, response.context['itinerary_list'])
        self.assertIn(self.admin_private_itinerary, response.context['itinerary_list'])
        
    def test_itinerary_detail_view(self):
        """
        Test the itinerary detail view.
        
        Verifies that the detail view displays the itinerary details correctly,
        and that private itineraries are only visible to their owners.
        """
        # Anonymous user should be able to view public itineraries
        response = self.client.get(self.itinerary_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['itinerary'], self.test_itinerary)
        
        # Anonymous user should not be able to view private itineraries
        private_url = reverse('itineraries:detail', kwargs={'pk': self.admin_private_itinerary.pk})
        response = self.client.get(private_url)
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Owner should be able to view their private itinerary
        self.client.login(username='admin', password='password')
        response = self.client.get(private_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['itinerary'], self.admin_private_itinerary)
        
    def test_itinerary_create_view(self):
        """
        Test the itinerary create view.
        
        Verifies that authenticated users can create new itineraries,
        and that anonymous users are redirected to the login page.
        """
        # Anonymous user should be redirected to login
        response = self.client.get(self.itinerary_create_url)
        self.assertRedirects(
            response, 
            f'/accounts/login/?next={self.itinerary_create_url}'
        )
        
        # Authenticated user should be able to access the create form
        self.client.login(username='testuser', password='password')
        response = self.client.get(self.itinerary_create_url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], ItineraryForm)
        
        # Test creating a new itinerary
        new_itinerary_data = {
            'title': 'New York City Trip',
            'description': 'Exploring the Big Apple',
            'start_date': (timezone.now().date() + datetime.timedelta(days=90)).strftime('%Y-%m-%d'),
            'end_date': (timezone.now().date() + datetime.timedelta(days=95)).strftime('%Y-%m-%d'),
            'is_public': True,
            'destination': self.test_destination.id
        }
        
        response = self.client.post(self.itinerary_create_url, new_itinerary_data)
        
        # Check that the itinerary was created
        self.assertEqual(Itinerary.objects.filter(title='New York City Trip').count(), 1)
        
        # Get the newly created itinerary
        new_itinerary = Itinerary.objects.get(title='New York City Trip')
        
        # Check that we're redirected to the detail page
        self.assertRedirects(
            response,
            reverse('itineraries:detail', kwargs={'pk': new_itinerary.pk})
        )
        
    def test_itinerary_update_view(self):
        """
        Test the itinerary update view.
        
        Verifies that only the owner of an itinerary can update it,
        and that the update works correctly.
        """
        # Anonymous user should be redirected to login
        response = self.client.get(self.itinerary_update_url)
        self.assertRedirects(
            response, 
            f'/accounts/login/?next={self.itinerary_update_url}'
        )
        
        # Non-owner should get a forbidden response
        self.client.login(username='admin', password='password')
        response = self.client.get(self.itinerary_update_url)
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Owner should be able to access the update form
        self.client.login(username='testuser', password='password')
        response = self.client.get(self.itinerary_update_url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], ItineraryForm)
        
        # Test updating the itinerary
        update_data = {
            'title': 'Updated Tokyo Adventure',
            'description': 'An updated 5-day adventure in Tokyo',
            'start_date': self.test_itinerary.start_date.strftime('%Y-%m-%d'),
            'end_date': self.test_itinerary.end_date.strftime('%Y-%m-%d'),
            'is_public': False,
            'destination': self.test_destination.id
        }
        
        response = self.client.post(self.itinerary_update_url, update_data)
        
        # Refresh the itinerary from the database
        self.test_itinerary.refresh_from_db()
        
        # Check that the itinerary was updated
        self.assertEqual(self.test_itinerary.title, 'Updated Tokyo Adventure')
        self.assertEqual(self.test_itinerary.description, 'An updated 5-day adventure in Tokyo')
        self.assertFalse(self.test_itinerary.is_public)
        
        # Check that we're redirected to the detail page
        self.assertRedirects(
            response,
            reverse('itineraries:detail', kwargs={'pk': self.test_itinerary.pk})
        )
        
    def test_itinerary_delete_view(self):
        """
        Test the itinerary delete view.
        
        Verifies that only the owner of an itinerary can delete it,
        and that the deletion works correctly.
        """
        # Anonymous user should be redirected to login
        response = self.client.get(self.itinerary_delete_url)
        self.assertRedirects(
            response, 
            f'/accounts/login/?next={self.itinerary_delete_url}'
        )
        
        # Non-owner should get a forbidden response
        self.client.login(username='admin', password='password')
        response = self.client.get(self.itinerary_delete_url)
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Owner should be able to access the delete confirmation page
        self.client.login(username='testuser', password='password')
        response = self.client.get(self.itinerary_delete_url)
        self.assertEqual(response.status_code, 200)
        
        # Test deleting the itinerary
        response = self.client.post(self.itinerary_delete_url)
        
        # Check that the itinerary was deleted
        self.assertEqual(Itinerary.objects.filter(pk=self.test_itinerary.pk).count(), 0)
        
        # Check that we're redirected to the list page
        self.assertRedirects(response, reverse('itineraries:list'))


class ItineraryItemViewTests(TravelGuideBaseTestCase):
    """
    Tests for the ItineraryItem views in the itineraries app.
    
    These tests verify that the views for managing itinerary items work as expected,
    including create, update, and delete views. Each test focuses on a specific view
    and its functionality.
    """
    
    def setUp(self):
        """
        Set up test data for itinerary item view tests.
        
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
        
        # URLs for testing
        self.item_create_url = reverse('itineraries:item_create', kwargs={'itinerary_id': self.test_itinerary.pk})
        self.item_update_url = reverse('itineraries:item_update', kwargs={'pk': self.test_item.pk})
        self.item_delete_url = reverse('itineraries:item_delete', kwargs={'pk': self.test_item.pk})
        
    def test_item_create_view(self):
        """
        Test the itinerary item create view.
        
        Verifies that only the owner of an itinerary can add items to it,
        and that the item creation works correctly.
        """
        # Anonymous user should be redirected to login
        response = self.client.get(self.item_create_url)
        self.assertRedirects(
            response, 
            f'/accounts/login/?next={self.item_create_url}'
        )
        
        # Non-owner should get a forbidden response
        self.client.login(username='admin', password='password')
        response = self.client.get(self.item_create_url)
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Owner should be able to access the create form
        self.client.login(username='testuser', password='password')
        response = self.client.get(self.item_create_url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], ItineraryItemForm)
        
        # Test creating a new item
        new_item_data = {
            'day': 2,
            'time': '10:00',
            'title': 'Visit Senso-ji Temple',
            'description': 'Explore the ancient temple',
            'location': 'Senso-ji, Asakusa, Tokyo',
            'duration': 180  # 3 hours
        }
        
        response = self.client.post(self.item_create_url, new_item_data)
        
        # Check that the item was created
        self.assertEqual(
            ItineraryItem.objects.filter(
                itinerary=self.test_itinerary,
                title='Visit Senso-ji Temple'
            ).count(),
            1
        )
        
        # Check that we're redirected to the itinerary detail page
        self.assertRedirects(
            response,
            reverse('itineraries:detail', kwargs={'pk': self.test_itinerary.pk})
        )
        
    def test_item_update_view(self):
        """
        Test the itinerary item update view.
        
        Verifies that only the owner of an itinerary can update its items,
        and that the update works correctly.
        """
        # Anonymous user should be redirected to login
        response = self.client.get(self.item_update_url)
        self.assertRedirects(
            response, 
            f'/accounts/login/?next={self.item_update_url}'
        )
        
        # Non-owner should get a forbidden response
        self.client.login(username='admin', password='password')
        response = self.client.get(self.item_update_url)
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Owner should be able to access the update form
        self.client.login(username='testuser', password='password')
        response = self.client.get(self.item_update_url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], ItineraryItemForm)
        
        # Test updating the item
        update_data = {
            'day': 1,
            'time': '10:00',
            'title': 'Updated Tokyo Tower Visit',
            'description': 'Updated description',
            'location': 'Tokyo Tower, Minato City, Tokyo',
            'duration': 150  # 2.5 hours
        }
        
        response = self.client.post(self.item_update_url, update_data)
        
        # Refresh the item from the database
        self.test_item.refresh_from_db()
        
        # Check that the item was updated
        self.assertEqual(self.test_item.title, 'Updated Tokyo Tower Visit')
        self.assertEqual(self.test_item.description, 'Updated description')
        self.assertEqual(self.test_item.time, '10:00')
        self.assertEqual(self.test_item.duration, 150)
        
        # Check that we're redirected to the itinerary detail page
        self.assertRedirects(
            response,
            reverse('itineraries:detail', kwargs={'pk': self.test_itinerary.pk})
        )
        
    def test_item_delete_view(self):
        """
        Test the itinerary item delete view.
        
        Verifies that only the owner of an itinerary can delete its items,
        and that the deletion works correctly.
        """
        # Anonymous user should be redirected to login
        response = self.client.get(self.item_delete_url)
        self.assertRedirects(
            response, 
            f'/accounts/login/?next={self.item_delete_url}'
        )
        
        # Non-owner should get a forbidden response
        self.client.login(username='admin', password='password')
        response = self.client.get(self.item_delete_url)
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Owner should be able to access the delete confirmation page
        self.client.login(username='testuser', password='password')
        response = self.client.get(self.item_delete_url)
        self.assertEqual(response.status_code, 200)
        
        # Test deleting the item
        response = self.client.post(self.item_delete_url)
        
        # Check that the item was deleted
        self.assertEqual(ItineraryItem.objects.filter(pk=self.test_item.pk).count(), 0)
        
        # Check that we're redirected to the itinerary detail page
        self.assertRedirects(
            response,
            reverse('itineraries:detail', kwargs={'pk': self.test_itinerary.pk})
        )


class SavedItineraryViewTests(TravelGuideBaseTestCase):
    """
    Tests for the SavedItinerary views in the itineraries app.
    
    These tests verify that the views for managing saved itineraries work as expected,
    including save, unsave, and list views. Each test focuses on a specific view
    and its functionality.
    """
    
    def setUp(self):
        """
        Set up test data for saved itinerary view tests.
        
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
        
        # URLs for testing
        self.save_url = reverse('itineraries:save', kwargs={'pk': self.admin_itinerary.pk})
        self.unsave_url = reverse('itineraries:unsave', kwargs={'pk': self.admin_itinerary.pk})
        self.saved_list_url = reverse('itineraries:saved_list')
        
    def test_save_itinerary_view(self):
        """
        Test the save itinerary view.
        
        Verifies that authenticated users can save public itineraries,
        and that anonymous users are redirected to the login page.
        """
        # Create another itinerary to save
        another_itinerary = Itinerary.objects.create(
            user=self.admin_user,
            title="Paris Weekend",
            description="A weekend getaway in Paris",
            start_date=timezone.now().date() + datetime.timedelta(days=30),
            end_date=timezone.now().date() + datetime.timedelta(days=32),
            is_public=True,
            destination=self.create_destination("Paris", self.test_region)
        )
        
        save_url = reverse('itineraries:save', kwargs={'pk': another_itinerary.pk})
        
        # Anonymous user should be redirected to login
        response = self.client.post(save_url)
        self.assertRedirects(
            response, 
            f'/accounts/login/?next={save_url}'
        )
        
        # Authenticated user should be able to save the itinerary
        self.client.login(username='testuser', password='password')
        
        # Test with AJAX request
        response = self.client.post(
            save_url,
            {'notes': 'Planning to use this for my Paris trip'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Check that the response is JSON
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Parse the JSON response
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Check that the itinerary was saved
        self.assertEqual(
            SavedItinerary.objects.filter(
                user=self.test_user,
                itinerary=another_itinerary
            ).count(),
            1
        )
        
        # Test with non-AJAX request
        third_itinerary = Itinerary.objects.create(
            user=self.admin_user,
            title="Rome Adventure",
            description="A week in Rome",
            start_date=timezone.now().date() + datetime.timedelta(days=60),
            end_date=timezone.now().date() + datetime.timedelta(days=67),
            is_public=True,
            destination=self.create_destination("Rome", self.test_region)
        )
        
        save_url = reverse('itineraries:save', kwargs={'pk': third_itinerary.pk})
        
        response = self.client.post(
            save_url,
            {'notes': 'Rome looks amazing'}
        )
        
        # Check that we're redirected to the itinerary detail page
        self.assertRedirects(
            response,
            reverse('itineraries:detail', kwargs={'pk': third_itinerary.pk})
        )
        
        # Check that the itinerary was saved
        self.assertEqual(
            SavedItinerary.objects.filter(
                user=self.test_user,
                itinerary=third_itinerary
            ).count(),
            1
        )
        
    def test_unsave_itinerary_view(self):
        """
        Test the unsave itinerary view.
        
        Verifies that authenticated users can unsave itineraries they have saved,
        and that anonymous users are redirected to the login page.
        """
        # Anonymous user should be redirected to login
        response = self.client.post(self.unsave_url)
        self.assertRedirects(
            response, 
            f'/accounts/login/?next={self.unsave_url}'
        )
        
        # Authenticated user should be able to unsave the itinerary
        self.client.login(username='testuser', password='password')
        
        # Test with AJAX request
        response = self.client.post(
            self.unsave_url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Check that the response is JSON
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Parse the JSON response
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Check that the saved itinerary was deleted
        self.assertEqual(
            SavedItinerary.objects.filter(
                user=self.test_user,
                itinerary=self.admin_itinerary
            ).count(),
            0
        )
        
        # Create another saved itinerary for testing non-AJAX request
        SavedItinerary.objects.create(
            user=self.test_user,
            itinerary=self.admin_itinerary,
            notes="Saving again"
        )
        
        # Test with non-AJAX request
        response = self.client.post(self.unsave_url)
        
        # Check that we're redirected to the itinerary detail page
        self.assertRedirects(
            response,
            reverse('itineraries:detail', kwargs={'pk': self.admin_itinerary.pk})
        )
        
        # Check that the saved itinerary was deleted
        self.assertEqual(
            SavedItinerary.objects.filter(
                user=self.test_user,
                itinerary=self.admin_itinerary
            ).count(),
            0
        )
        
    def test_saved_itinerary_list_view(self):
        """
        Test the saved itinerary list view.
        
        Verifies that authenticated users can view their saved itineraries,
        and that anonymous users are redirected to the login page.
        """
        # Anonymous user should be redirected to login
        response = self.client.get(self.saved_list_url)
        self.assertRedirects(
            response, 
            f'/accounts/login/?next={self.saved_list_url}'
        )
        
        # Authenticated user should be able to view their saved itineraries
        self.client.login(username='testuser', password='password')
        response = self.client.get(self.saved_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.saved_itinerary, response.context['saveditinerary_list'])
        
        # Create another saved itinerary
        another_itinerary = Itinerary.objects.create(
            user=self.admin_user,
            title="Paris Weekend",
            description="A weekend getaway in Paris",
            start_date=timezone.now().date() + datetime.timedelta(days=30),
            end_date=timezone.now().date() + datetime.timedelta(days=32),
            is_public=True,
            destination=self.create_destination("Paris", self.test_region)
        )
        
        another_saved = SavedItinerary.objects.create(
            user=self.test_user,
            itinerary=another_itinerary,
            notes="Planning to use this for my Paris trip"
        )
        
        # Refresh the page to see both saved itineraries
        response = self.client.get(self.saved_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.saved_itinerary, response.context['saveditinerary_list'])
        self.assertIn(another_saved, response.context['saveditinerary_list'])
        
        # Other user should not see these saved itineraries
        self.client.login(username='admin', password='password')
        response = self.client.get(self.saved_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['saveditinerary_list']), 0)
