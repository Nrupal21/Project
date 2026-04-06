"""
Test cases for API permissions in the TravelGuide application.

This module contains comprehensive test cases for the API permission system,
focusing on authentication, authorization, and access control for API endpoints.
Every test function is thoroughly documented to make understanding
the tests easier for programmers.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient
from rest_framework import status

from destinations.models import Destination, Region, Attraction
from tours.models import Tour, TourCategory
from itineraries.models import Itinerary, ItineraryItem
from reviews.models import Review
from bookings.models import Booking
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class APIAuthenticationTests(TravelGuideBaseTestCase):
    """
    Tests for API authentication in the TravelGuide application.
    
    These tests verify that API authentication works correctly,
    including token authentication and session authentication.
    """
    
    def setUp(self):
        """
        Set up test data for API authentication tests.
        
        Extends the base setUp method to include API clients and tokens.
        """
        super().setUp()
        
        # Create API client
        self.api_client = APIClient()
        
        # Create token for test user
        from rest_framework.authtoken.models import Token
        self.test_user_token, _ = Token.objects.get_or_create(user=self.test_user)
        
        # URLs for testing
        self.token_url = reverse('api:token_obtain_pair')
        self.token_refresh_url = reverse('api:token_refresh')
        self.destinations_url = reverse('api:destination-list')
        self.user_profile_url = reverse('api:user-profile')
        
    def test_token_obtain(self):
        """
        Test obtaining a JWT token.
        
        Verifies that a user can obtain a JWT token with valid credentials.
        """
        response = self.client.post(self.token_url, {
            'username': 'testuser',
            'password': 'password'
        })
        
        # Check that the token was obtained
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
    def test_token_obtain_invalid_credentials(self):
        """
        Test obtaining a JWT token with invalid credentials.
        
        Verifies that a user cannot obtain a JWT token with invalid credentials.
        """
        response = self.client.post(self.token_url, {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        
        # Check that the token was not obtained
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_token_refresh(self):
        """
        Test refreshing a JWT token.
        
        Verifies that a user can refresh a JWT token with a valid refresh token.
        """
        # First, obtain a token
        response = self.client.post(self.token_url, {
            'username': 'testuser',
            'password': 'password'
        })
        
        refresh_token = response.data['refresh']
        
        # Then, refresh the token
        response = self.client.post(self.token_refresh_url, {
            'refresh': refresh_token
        })
        
        # Check that the token was refreshed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        
    def test_token_refresh_invalid(self):
        """
        Test refreshing a JWT token with an invalid refresh token.
        
        Verifies that a user cannot refresh a JWT token with an invalid refresh token.
        """
        response = self.client.post(self.token_refresh_url, {
            'refresh': 'invalid-token'
        })
        
        # Check that the token was not refreshed
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_api_access_without_authentication(self):
        """
        Test accessing a protected API endpoint without authentication.
        
        Verifies that a user cannot access a protected API endpoint
        without authentication.
        """
        response = self.api_client.get(self.user_profile_url)
        
        # Check that access is denied
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_api_access_with_token_authentication(self):
        """
        Test accessing a protected API endpoint with token authentication.
        
        Verifies that a user can access a protected API endpoint
        with token authentication.
        """
        # Authenticate with token
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.test_user_token.key}')
        
        response = self.api_client.get(self.user_profile_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        
    def test_api_access_with_jwt_authentication(self):
        """
        Test accessing a protected API endpoint with JWT authentication.
        
        Verifies that a user can access a protected API endpoint
        with JWT authentication.
        """
        # Obtain a JWT token
        response = self.client.post(self.token_url, {
            'username': 'testuser',
            'password': 'password'
        })
        
        access_token = response.data['access']
        
        # Authenticate with JWT
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = self.api_client.get(self.user_profile_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        
    def test_api_access_with_session_authentication(self):
        """
        Test accessing a protected API endpoint with session authentication.
        
        Verifies that a user can access a protected API endpoint
        with session authentication.
        """
        # Log in
        self.api_client.login(username='testuser', password='password')
        
        response = self.api_client.get(self.user_profile_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        
    def test_public_api_access_without_authentication(self):
        """
        Test accessing a public API endpoint without authentication.
        
        Verifies that a user can access a public API endpoint
        without authentication.
        """
        response = self.api_client.get(self.destinations_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class APIPermissionTests(TravelGuideBaseTestCase):
    """
    Tests for API permissions in the TravelGuide application.
    
    These tests verify that API permissions work correctly for different
    user roles and resource types.
    """
    
    def setUp(self):
        """
        Set up test data for API permission tests.
        
        Extends the base setUp method to include additional users, resources,
        and API clients.
        """
        super().setUp()
        
        # Create additional users with different roles
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='password',
            is_staff=True
        )
        
        self.another_user = User.objects.create_user(
            username='anotheruser',
            email='another@example.com',
            password='password'
        )
        
        # Create API clients
        self.api_client = APIClient()
        self.staff_api_client = APIClient()
        self.another_api_client = APIClient()
        
        # Authenticate API clients
        self.staff_api_client.force_authenticate(user=self.staff_user)
        self.api_client.force_authenticate(user=self.test_user)
        self.another_api_client.force_authenticate(user=self.another_user)
        
        # Create test resources
        self.test_region = Region.objects.create(
            name="Test Region",
            description="A test region"
        )
        
        self.test_destination = Destination.objects.create(
            name="Test Destination",
            description="A test destination",
            region=self.test_region
        )
        
        self.test_attraction = Attraction.objects.create(
            name="Test Attraction",
            description="A test attraction",
            destination=self.test_destination
        )
        
        self.test_category = TourCategory.objects.create(
            name="Test Category",
            description="A test category"
        )
        
        self.test_tour = Tour.objects.create(
            title="Test Tour",
            description="A test tour",
            destination=self.test_destination,
            duration=5,
            price=1000.00
        )
        self.test_tour.categories.add(self.test_category)
        
        # Create user-owned resources
        self.test_user_itinerary = Itinerary.objects.create(
            user=self.test_user,
            title="Test User's Itinerary",
            description="An itinerary owned by the test user",
            start_date='2023-06-15',
            end_date='2023-06-20',
            is_public=False
        )
        
        self.another_user_itinerary = Itinerary.objects.create(
            user=self.another_user,
            title="Another User's Itinerary",
            description="An itinerary owned by another user",
            start_date='2023-07-10',
            end_date='2023-07-15',
            is_public=False
        )
        
        self.public_itinerary = Itinerary.objects.create(
            user=self.another_user,
            title="Public Itinerary",
            description="A public itinerary that anyone can view",
            start_date='2023-08-05',
            end_date='2023-08-10',
            is_public=True
        )
        
        # URLs for testing
        self.destinations_url = reverse('api:destination-list')
        self.destination_detail_url = reverse('api:destination-detail', kwargs={'pk': self.test_destination.pk})
        self.tours_url = reverse('api:tour-list')
        self.tour_detail_url = reverse('api:tour-detail', kwargs={'pk': self.test_tour.pk})
        self.itineraries_url = reverse('api:itinerary-list')
        self.test_user_itinerary_url = reverse('api:itinerary-detail', kwargs={'pk': self.test_user_itinerary.pk})
        self.another_user_itinerary_url = reverse('api:itinerary-detail', kwargs={'pk': self.another_user_itinerary.pk})
        self.public_itinerary_url = reverse('api:itinerary-detail', kwargs={'pk': self.public_itinerary.pk})
        
    def test_destination_list_public_access(self):
        """
        Test that the destination list API is publicly accessible.
        
        Verifies that anonymous users can access the destination list API.
        """
        client = APIClient()  # Unauthenticated client
        response = client.get(self.destinations_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_destination_create_anonymous(self):
        """
        Test that anonymous users cannot create destinations via API.
        
        Verifies that anonymous users are denied access when trying
        to create a destination via the API.
        """
        client = APIClient()  # Unauthenticated client
        response = client.post(self.destinations_url, {
            'name': 'New Destination',
            'description': 'A new destination',
            'region': self.test_region.pk
        })
        
        # Check that access is denied
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_destination_create_regular_user(self):
        """
        Test that regular users cannot create destinations via API.
        
        Verifies that regular authenticated users are denied access
        when trying to create a destination via the API.
        """
        response = self.api_client.post(self.destinations_url, {
            'name': 'New Destination',
            'description': 'A new destination',
            'region': self.test_region.pk
        })
        
        # Check that access is denied
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_destination_create_staff(self):
        """
        Test that staff users can create destinations via API.
        
        Verifies that staff users can create destinations via the API.
        """
        response = self.staff_api_client.post(self.destinations_url, {
            'name': 'New Destination',
            'description': 'A new destination',
            'region': self.test_region.pk
        })
        
        # Check that the destination was created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Destination')
        
    def test_destination_update_staff(self):
        """
        Test that staff users can update destinations via API.
        
        Verifies that staff users can update destinations via the API.
        """
        response = self.staff_api_client.patch(self.destination_detail_url, {
            'name': 'Updated Destination'
        })
        
        # Check that the destination was updated
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Destination')
        
    def test_destination_update_regular_user(self):
        """
        Test that regular users cannot update destinations via API.
        
        Verifies that regular authenticated users are denied access
        when trying to update a destination via the API.
        """
        response = self.api_client.patch(self.destination_detail_url, {
            'name': 'Updated Destination'
        })
        
        # Check that access is denied
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_destination_delete_staff(self):
        """
        Test that staff users can delete destinations via API.
        
        Verifies that staff users can delete destinations via the API.
        """
        response = self.staff_api_client.delete(self.destination_detail_url)
        
        # Check that the destination was deleted
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Destination.objects.filter(pk=self.test_destination.pk).exists())
        
    def test_destination_delete_regular_user(self):
        """
        Test that regular users cannot delete destinations via API.
        
        Verifies that regular authenticated users are denied access
        when trying to delete a destination via the API.
        """
        response = self.api_client.delete(self.destination_detail_url)
        
        # Check that access is denied
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_itinerary_list_anonymous(self):
        """
        Test that anonymous users can only see public itineraries via API.
        
        Verifies that anonymous users can only see public itineraries
        when accessing the itinerary list API.
        """
        client = APIClient()  # Unauthenticated client
        response = client.get(self.itineraries_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that only public itineraries are returned
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Public Itinerary')
        
    def test_itinerary_list_authenticated(self):
        """
        Test that authenticated users can see public and own itineraries via API.
        
        Verifies that authenticated users can see public itineraries and
        their own private itineraries when accessing the itinerary list API.
        """
        response = self.api_client.get(self.itineraries_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that public and own itineraries are returned
        self.assertEqual(len(response.data), 2)
        titles = [item['title'] for item in response.data]
        self.assertIn("Test User's Itinerary", titles)
        self.assertIn('Public Itinerary', titles)
        
    def test_itinerary_list_staff(self):
        """
        Test that staff users can see all itineraries via API.
        
        Verifies that staff users can see all itineraries
        when accessing the itinerary list API.
        """
        response = self.staff_api_client.get(self.itineraries_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that all itineraries are returned
        self.assertEqual(len(response.data), 3)
        
    def test_private_itinerary_owner_access(self):
        """
        Test that owners can access their private itineraries via API.
        
        Verifies that users can access their own private itineraries via the API.
        """
        response = self.api_client.get(self.test_user_itinerary_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Test User's Itinerary")
        
    def test_private_itinerary_other_user_access(self):
        """
        Test that users cannot access other users' private itineraries via API.
        
        Verifies that users are denied access to private itineraries
        owned by other users via the API.
        """
        response = self.api_client.get(self.another_user_itinerary_url)
        
        # Check that access is denied
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_private_itinerary_anonymous_access(self):
        """
        Test that anonymous users cannot access private itineraries via API.
        
        Verifies that anonymous users are denied access when trying
        to access a private itinerary via the API.
        """
        client = APIClient()  # Unauthenticated client
        response = client.get(self.test_user_itinerary_url)
        
        # Check that access is denied
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_public_itinerary_anonymous_access(self):
        """
        Test that anonymous users can access public itineraries via API.
        
        Verifies that anonymous users can access public itineraries via the API.
        """
        client = APIClient()  # Unauthenticated client
        response = client.get(self.public_itinerary_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Public Itinerary')
        
    def test_itinerary_create_authenticated(self):
        """
        Test that authenticated users can create itineraries via API.
        
        Verifies that authenticated users can create itineraries via the API.
        """
        response = self.api_client.post(self.itineraries_url, {
            'title': 'New Itinerary',
            'description': 'A new itinerary',
            'start_date': '2023-09-01',
            'end_date': '2023-09-05',
            'is_public': True
        })
        
        # Check that the itinerary was created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Itinerary')
        self.assertEqual(response.data['user'], self.test_user.pk)
        
    def test_itinerary_create_anonymous(self):
        """
        Test that anonymous users cannot create itineraries via API.
        
        Verifies that anonymous users are denied access when trying
        to create an itinerary via the API.
        """
        client = APIClient()  # Unauthenticated client
        response = client.post(self.itineraries_url, {
            'title': 'New Itinerary',
            'description': 'A new itinerary',
            'start_date': '2023-09-01',
            'end_date': '2023-09-05',
            'is_public': True
        })
        
        # Check that access is denied
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_itinerary_update_owner(self):
        """
        Test that owners can update their itineraries via API.
        
        Verifies that users can update their own itineraries via the API.
        """
        response = self.api_client.patch(self.test_user_itinerary_url, {
            'title': 'Updated Itinerary'
        })
        
        # Check that the itinerary was updated
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Itinerary')
        
    def test_itinerary_update_other_user(self):
        """
        Test that users cannot update other users' itineraries via API.
        
        Verifies that users are denied access when trying to update
        itineraries owned by other users via the API.
        """
        response = self.api_client.patch(self.another_user_itinerary_url, {
            'title': 'Updated Itinerary'
        })
        
        # Check that access is denied
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_itinerary_delete_owner(self):
        """
        Test that owners can delete their itineraries via API.
        
        Verifies that users can delete their own itineraries via the API.
        """
        response = self.api_client.delete(self.test_user_itinerary_url)
        
        # Check that the itinerary was deleted
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Itinerary.objects.filter(pk=self.test_user_itinerary.pk).exists())
        
    def test_itinerary_delete_other_user(self):
        """
        Test that users cannot delete other users' itineraries via API.
        
        Verifies that users are denied access when trying to delete
        itineraries owned by other users via the API.
        """
        response = self.api_client.delete(self.another_user_itinerary_url)
        
        # Check that access is denied
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_itinerary_delete_staff(self):
        """
        Test that staff users can delete any itinerary via API.
        
        Verifies that staff users can delete any itinerary via the API,
        regardless of ownership.
        """
        response = self.staff_api_client.delete(self.test_user_itinerary_url)
        
        # Check that the itinerary was deleted
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Itinerary.objects.filter(pk=self.test_user_itinerary.pk).exists())
