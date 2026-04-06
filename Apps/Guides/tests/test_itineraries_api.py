"""
Test cases for the itineraries app API endpoints.

This module contains comprehensive test cases for all API endpoints
in the itineraries app. Every test function is thoroughly documented
to make understanding the tests easier for programmers.
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
import datetime
import json

from itineraries.models import Itinerary, ItineraryItem, SavedItinerary
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class ItineraryAPITests(TravelGuideBaseTestCase):
    """
    Tests for the API endpoints in the itineraries app.
    
    These tests verify that the API endpoints work correctly, including
    authentication, permissions, and data manipulation. Each test focuses
    on a specific endpoint and its functionality.
    """
    
    def setUp(self):
        """
        Set up test data for API tests.
        
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
        self.api_itinerary_list_url = reverse('api:itineraries-list')
        self.api_itinerary_detail_url = reverse('api:itineraries-detail', kwargs={'pk': self.test_itinerary.pk})
        self.api_item_list_url = reverse('api:itinerary-items-list', kwargs={'itinerary_id': self.test_itinerary.pk})
        self.api_item_detail_url = reverse('api:itinerary-items-detail', kwargs={'pk': self.test_item.pk})
    
    def test_itinerary_list_api(self):
        """
        Test the itinerary list API endpoint.
        
        Verifies that the endpoint returns a list of public itineraries for anonymous users,
        and both public and the user's own private itineraries for authenticated users.
        """
        # Anonymous user should see only public itineraries
        response = self.client.get(self.api_itinerary_list_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertGreaterEqual(len(data), 1)
        
        # Create a private itinerary for the test user
        private_itinerary = Itinerary.objects.create(
            user=self.test_user,
            title="Private Trip",
            description="A private trip",
            start_date=timezone.now().date() + datetime.timedelta(days=30),
            end_date=timezone.now().date() + datetime.timedelta(days=35),
            is_public=False,
            destination=self.test_destination
        )
        
        # Anonymous user should still only see public itineraries
        response = self.client.get(self.api_itinerary_list_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        itinerary_ids = [item['id'] for item in data]
        self.assertIn(self.test_itinerary.id, itinerary_ids)
        self.assertNotIn(private_itinerary.id, itinerary_ids)
        
        # Authenticated user should see public itineraries and their own private ones
        self.client.login(username='testuser', password='password')
        response = self.client.get(self.api_itinerary_list_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        itinerary_ids = [item['id'] for item in data]
        self.assertIn(self.test_itinerary.id, itinerary_ids)
        self.assertIn(private_itinerary.id, itinerary_ids)
        
    def test_itinerary_detail_api(self):
        """
        Test the itinerary detail API endpoint.
        
        Verifies that the endpoint returns the details of a public itinerary for anonymous users,
        and that private itineraries are only accessible to their owners.
        """
        # Anonymous user should be able to view public itineraries
        response = self.client.get(self.api_itinerary_detail_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['id'], self.test_itinerary.id)
        self.assertEqual(data['title'], "Tokyo Adventure")
        
        # Create a private itinerary for the test user
        private_itinerary = Itinerary.objects.create(
            user=self.test_user,
            title="Private Trip",
            description="A private trip",
            start_date=timezone.now().date() + datetime.timedelta(days=30),
            end_date=timezone.now().date() + datetime.timedelta(days=35),
            is_public=False,
            destination=self.test_destination
        )
        
        private_url = reverse('api:itineraries-detail', kwargs={'pk': private_itinerary.pk})
        
        # Anonymous user should not be able to view private itineraries
        response = self.client.get(private_url)
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Owner should be able to view their private itinerary
        self.client.login(username='testuser', password='password')
        response = self.client.get(private_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['id'], private_itinerary.id)
        self.assertEqual(data['title'], "Private Trip")
        
    def test_itinerary_create_api(self):
        """
        Test the itinerary create API endpoint.
        
        Verifies that authenticated users can create new itineraries,
        and that anonymous users receive an authentication error.
        """
        # Data for a new itinerary
        new_itinerary_data = {
            'title': 'New York City Trip',
            'description': 'Exploring the Big Apple',
            'start_date': (timezone.now().date() + datetime.timedelta(days=90)).strftime('%Y-%m-%d'),
            'end_date': (timezone.now().date() + datetime.timedelta(days=95)).strftime('%Y-%m-%d'),
            'is_public': True,
            'destination': self.test_destination.id
        }
        
        # Anonymous user should not be able to create an itinerary
        response = self.client.post(
            self.api_itinerary_list_url,
            data=json.dumps(new_itinerary_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)  # Unauthorized
        
        # Authenticated user should be able to create an itinerary
        self.client.login(username='testuser', password='password')
        response = self.client.post(
            self.api_itinerary_list_url,
            data=json.dumps(new_itinerary_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)  # Created
        data = json.loads(response.content)
        self.assertEqual(data['title'], 'New York City Trip')
        self.assertEqual(data['description'], 'Exploring the Big Apple')
        self.assertTrue(data['is_public'])
        
        # Check that the itinerary was created in the database
        self.assertTrue(Itinerary.objects.filter(title='New York City Trip').exists())
        
    def test_itinerary_update_api(self):
        """
        Test the itinerary update API endpoint.
        
        Verifies that only the owner of an itinerary can update it,
        and that the update works correctly.
        """
        # Data for updating the itinerary
        update_data = {
            'title': 'Updated Tokyo Adventure',
            'description': 'An updated 5-day adventure in Tokyo',
            'is_public': False
        }
        
        # Anonymous user should not be able to update an itinerary
        response = self.client.patch(
            self.api_itinerary_detail_url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)  # Unauthorized
        
        # Non-owner should not be able to update an itinerary
        self.client.login(username='admin', password='password')
        response = self.client.patch(
            self.api_itinerary_detail_url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Owner should be able to update their itinerary
        self.client.login(username='testuser', password='password')
        response = self.client.patch(
            self.api_itinerary_detail_url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)  # OK
        data = json.loads(response.content)
        self.assertEqual(data['title'], 'Updated Tokyo Adventure')
        self.assertEqual(data['description'], 'An updated 5-day adventure in Tokyo')
        self.assertFalse(data['is_public'])
        
        # Check that the itinerary was updated in the database
        self.test_itinerary.refresh_from_db()
        self.assertEqual(self.test_itinerary.title, 'Updated Tokyo Adventure')
        self.assertEqual(self.test_itinerary.description, 'An updated 5-day adventure in Tokyo')
        self.assertFalse(self.test_itinerary.is_public)
        
    def test_itinerary_delete_api(self):
        """
        Test the itinerary delete API endpoint.
        
        Verifies that only the owner of an itinerary can delete it,
        and that the deletion works correctly.
        """
        # Create a new itinerary for deletion testing
        itinerary_to_delete = Itinerary.objects.create(
            user=self.test_user,
            title="Itinerary to Delete",
            description="This itinerary will be deleted",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + datetime.timedelta(days=3),
            is_public=True,
            destination=self.test_destination
        )
        
        delete_url = reverse('api:itineraries-detail', kwargs={'pk': itinerary_to_delete.pk})
        
        # Anonymous user should not be able to delete an itinerary
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, 401)  # Unauthorized
        
        # Non-owner should not be able to delete an itinerary
        self.client.login(username='admin', password='password')
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Owner should be able to delete their itinerary
        self.client.login(username='testuser', password='password')
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, 204)  # No Content
        
        # Check that the itinerary was deleted from the database
        self.assertFalse(Itinerary.objects.filter(pk=itinerary_to_delete.pk).exists())
        
    def test_itinerary_item_list_api(self):
        """
        Test the itinerary item list API endpoint.
        
        Verifies that the endpoint returns a list of items for a specific itinerary,
        and that the items are accessible based on the itinerary's visibility.
        """
        # Anonymous user should be able to view items for public itineraries
        response = self.client.get(self.api_item_list_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], "Visit Tokyo Tower")
        
        # Create a private itinerary for the test user
        private_itinerary = Itinerary.objects.create(
            user=self.test_user,
            title="Private Trip",
            description="A private trip",
            start_date=timezone.now().date() + datetime.timedelta(days=30),
            end_date=timezone.now().date() + datetime.timedelta(days=35),
            is_public=False,
            destination=self.test_destination
        )
        
        # Add an item to the private itinerary
        private_item = ItineraryItem.objects.create(
            itinerary=private_itinerary,
            day=1,
            time="10:00",
            title="Secret Activity",
            description="A secret activity",
            location="Secret Location",
            duration=60
        )
        
        private_item_list_url = reverse('api:itinerary-items-list', kwargs={'itinerary_id': private_itinerary.pk})
        
        # Anonymous user should not be able to view items for private itineraries
        response = self.client.get(private_item_list_url)
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Owner should be able to view items for their private itinerary
        self.client.login(username='testuser', password='password')
        response = self.client.get(private_item_list_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], "Secret Activity")
        
    def test_itinerary_item_create_api(self):
        """
        Test the itinerary item create API endpoint.
        
        Verifies that only the owner of an itinerary can add items to it,
        and that the item creation works correctly.
        """
        # Data for a new itinerary item
        new_item_data = {
            'day': 2,
            'time': '10:00',
            'title': 'Visit Senso-ji Temple',
            'description': 'Explore the ancient temple',
            'location': 'Senso-ji, Asakusa, Tokyo',
            'duration': 180  # 3 hours
        }
        
        # Anonymous user should not be able to create an item
        response = self.client.post(
            self.api_item_list_url,
            data=json.dumps(new_item_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)  # Unauthorized
        
        # Non-owner should not be able to create an item
        self.client.login(username='admin', password='password')
        response = self.client.post(
            self.api_item_list_url,
            data=json.dumps(new_item_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Owner should be able to create an item
        self.client.login(username='testuser', password='password')
        response = self.client.post(
            self.api_item_list_url,
            data=json.dumps(new_item_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)  # Created
        data = json.loads(response.content)
        self.assertEqual(data['day'], 2)
        self.assertEqual(data['time'], '10:00')
        self.assertEqual(data['title'], 'Visit Senso-ji Temple')
        
        # Check that the item was created in the database
        self.assertTrue(
            ItineraryItem.objects.filter(
                itinerary=self.test_itinerary,
                title='Visit Senso-ji Temple'
            ).exists()
        )
        
    def test_itinerary_item_update_api(self):
        """
        Test the itinerary item update API endpoint.
        
        Verifies that only the owner of an itinerary can update its items,
        and that the update works correctly.
        """
        # Data for updating the itinerary item
        update_data = {
            'time': '10:00',
            'title': 'Updated Tokyo Tower Visit',
            'description': 'Updated description',
            'duration': 150  # 2.5 hours
        }
        
        # Anonymous user should not be able to update an item
        response = self.client.patch(
            self.api_item_detail_url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)  # Unauthorized
        
        # Non-owner should not be able to update an item
        self.client.login(username='admin', password='password')
        response = self.client.patch(
            self.api_item_detail_url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Owner should be able to update their item
        self.client.login(username='testuser', password='password')
        response = self.client.patch(
            self.api_item_detail_url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)  # OK
        data = json.loads(response.content)
        self.assertEqual(data['time'], '10:00')
        self.assertEqual(data['title'], 'Updated Tokyo Tower Visit')
        self.assertEqual(data['description'], 'Updated description')
        self.assertEqual(data['duration'], 150)
        
        # Check that the item was updated in the database
        self.test_item.refresh_from_db()
        self.assertEqual(self.test_item.time, '10:00')
        self.assertEqual(self.test_item.title, 'Updated Tokyo Tower Visit')
        self.assertEqual(self.test_item.description, 'Updated description')
        self.assertEqual(self.test_item.duration, 150)
        
    def test_itinerary_item_delete_api(self):
        """
        Test the itinerary item delete API endpoint.
        
        Verifies that only the owner of an itinerary can delete its items,
        and that the deletion works correctly.
        """
        # Create a new item for deletion testing
        item_to_delete = ItineraryItem.objects.create(
            itinerary=self.test_itinerary,
            day=2,
            time="14:00",
            title="Item to Delete",
            description="This item will be deleted",
            location="Some location",
            duration=60
        )
        
        delete_url = reverse('api:itinerary-items-detail', kwargs={'pk': item_to_delete.pk})
        
        # Anonymous user should not be able to delete an item
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, 401)  # Unauthorized
        
        # Non-owner should not be able to delete an item
        self.client.login(username='admin', password='password')
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Owner should be able to delete their item
        self.client.login(username='testuser', password='password')
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, 204)  # No Content
        
        # Check that the item was deleted from the database
        self.assertFalse(ItineraryItem.objects.filter(pk=item_to_delete.pk).exists())
