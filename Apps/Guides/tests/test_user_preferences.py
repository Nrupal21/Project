"""
Test cases for the user preferences functionality in the accounts app.

This module contains comprehensive test cases for the UserPreference model
and related views in the accounts app. Every test function is thoroughly
documented to make understanding the tests easier for programmers.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
import json

from accounts.models import UserPreference
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class UserPreferenceModelTests(TravelGuideBaseTestCase):
    """
    Tests for the UserPreference model in the accounts app.
    
    These tests verify that UserPreference objects can be created correctly,
    and that their methods work as expected. Each test focuses on a 
    specific aspect of the UserPreference model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for UserPreference tests.
        
        Extends the base setUp method to include user preferences for testing.
        """
        super().setUp()
        
        # Create user preferences for the test user
        self.test_preferences = UserPreference.objects.create(
            user=self.test_user,
            preferred_currency='USD',
            preferred_language='en',
            email_notifications=True,
            push_notifications=False,
            theme='light',
            timezone='America/New_York'
        )
    
    def test_user_preference_creation(self):
        """
        Test that a UserPreference can be created with the expected attributes.
        
        Verifies that the UserPreference model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create preferences for the admin user
        preferences = UserPreference.objects.create(
            user=self.admin_user,
            preferred_currency='EUR',
            preferred_language='fr',
            email_notifications=False,
            push_notifications=True,
            theme='dark',
            timezone='Europe/Paris'
        )
        
        # Verify the preferences were created with the correct attributes
        self.assertEqual(preferences.user, self.admin_user)
        self.assertEqual(preferences.preferred_currency, 'EUR')
        self.assertEqual(preferences.preferred_language, 'fr')
        self.assertFalse(preferences.email_notifications)
        self.assertTrue(preferences.push_notifications)
        self.assertEqual(preferences.theme, 'dark')
        self.assertEqual(preferences.timezone, 'Europe/Paris')
        
    def test_user_preference_str_method(self):
        """
        Test the string representation of a UserPreference object.
        
        Verifies that the __str__ method returns the expected string,
        which should include the username.
        """
        expected_str = f"Preferences for {self.test_user.username}"
        self.assertEqual(str(self.test_preferences), expected_str)
        
    def test_user_preference_defaults(self):
        """
        Test that the UserPreference model has the correct default values.
        
        Verifies that when a UserPreference is created without specifying
        certain fields, they are set to the default values.
        """
        # Create a new user
        new_user = User.objects.create_user(
            username='newuser',
            email='newuser@example.com',
            password='password'
        )
        
        # Create preferences with minimal fields
        preferences = UserPreference.objects.create(user=new_user)
        
        # Verify the default values
        self.assertEqual(preferences.preferred_currency, 'USD')  # Default currency
        self.assertEqual(preferences.preferred_language, 'en')   # Default language
        self.assertTrue(preferences.email_notifications)         # Default to True
        self.assertTrue(preferences.push_notifications)          # Default to True
        self.assertEqual(preferences.theme, 'light')             # Default theme
        self.assertEqual(preferences.timezone, 'UTC')            # Default timezone
        
    def test_user_preference_uniqueness(self):
        """
        Test that a user can only have one UserPreference object.
        
        Verifies that attempting to create a second UserPreference for the same user
        raises an integrity error.
        """
        # Try to create another preference for the test user
        with self.assertRaises(Exception):  # Should raise an integrity error
            UserPreference.objects.create(
                user=self.test_user,
                preferred_currency='EUR',
                preferred_language='fr'
            )
            
    def test_user_preference_update(self):
        """
        Test updating a UserPreference object.
        
        Verifies that a UserPreference object can be updated with new values.
        """
        # Update the test user's preferences
        self.test_preferences.preferred_currency = 'JPY'
        self.test_preferences.preferred_language = 'ja'
        self.test_preferences.theme = 'dark'
        self.test_preferences.save()
        
        # Refresh from the database
        self.test_preferences.refresh_from_db()
        
        # Verify the updated values
        self.assertEqual(self.test_preferences.preferred_currency, 'JPY')
        self.assertEqual(self.test_preferences.preferred_language, 'ja')
        self.assertEqual(self.test_preferences.theme, 'dark')
        
        # Other fields should remain unchanged
        self.assertTrue(self.test_preferences.email_notifications)
        self.assertFalse(self.test_preferences.push_notifications)
        self.assertEqual(self.test_preferences.timezone, 'America/New_York')


class UserPreferenceViewTests(TravelGuideBaseTestCase):
    """
    Tests for the UserPreference views in the accounts app.
    
    These tests verify that the views for managing user preferences work as expected,
    including viewing and updating preferences. Each test focuses on a specific view
    and its functionality.
    """
    
    def setUp(self):
        """
        Set up test data for UserPreference view tests.
        
        Extends the base setUp method to include user preferences for testing.
        """
        super().setUp()
        
        # Create user preferences for the test user
        self.test_preferences = UserPreference.objects.create(
            user=self.test_user,
            preferred_currency='USD',
            preferred_language='en',
            email_notifications=True,
            push_notifications=False,
            theme='light',
            timezone='America/New_York'
        )
        
        # URLs for testing
        self.preferences_url = reverse('accounts:preferences')
        self.preferences_update_url = reverse('accounts:update_preferences')
    
    def test_preferences_view_anonymous(self):
        """
        Test that anonymous users are redirected to the login page.
        
        Verifies that attempting to access the preferences page as an anonymous user
        redirects to the login page.
        """
        response = self.client.get(self.preferences_url)
        self.assertRedirects(
            response, 
            f'/accounts/login/?next={self.preferences_url}'
        )
        
    def test_preferences_view_authenticated(self):
        """
        Test that authenticated users can view their preferences.
        
        Verifies that an authenticated user can access their preferences page
        and that the page displays their current preferences.
        """
        # Log in the test user
        self.client.login(username='testuser', password='password')
        
        # Access the preferences page
        response = self.client.get(self.preferences_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/preferences.html')
        
        # Check that the context contains the user's preferences
        self.assertIn('preferences', response.context)
        self.assertEqual(response.context['preferences'], self.test_preferences)
        
        # Check that the page displays the current preferences
        self.assertContains(response, 'USD')
        self.assertContains(response, 'English')
        self.assertContains(response, 'America/New_York')
        
    def test_preferences_update_view_anonymous(self):
        """
        Test that anonymous users are redirected to the login page.
        
        Verifies that attempting to update preferences as an anonymous user
        redirects to the login page.
        """
        response = self.client.post(self.preferences_update_url, {})
        self.assertRedirects(
            response, 
            f'/accounts/login/?next={self.preferences_update_url}'
        )
        
    def test_preferences_update_view_authenticated(self):
        """
        Test that authenticated users can update their preferences.
        
        Verifies that an authenticated user can update their preferences
        and that the changes are saved to the database.
        """
        # Log in the test user
        self.client.login(username='testuser', password='password')
        
        # Data for updating preferences
        update_data = {
            'preferred_currency': 'EUR',
            'preferred_language': 'fr',
            'email_notifications': 'false',  # String representation of boolean
            'push_notifications': 'true',    # String representation of boolean
            'theme': 'dark',
            'timezone': 'Europe/Paris'
        }
        
        # Submit the form to update preferences
        response = self.client.post(self.preferences_update_url, update_data)
        
        # Check that we're redirected back to the preferences page
        self.assertRedirects(response, self.preferences_url)
        
        # Refresh the preferences from the database
        self.test_preferences.refresh_from_db()
        
        # Verify that the preferences were updated
        self.assertEqual(self.test_preferences.preferred_currency, 'EUR')
        self.assertEqual(self.test_preferences.preferred_language, 'fr')
        self.assertFalse(self.test_preferences.email_notifications)
        self.assertTrue(self.test_preferences.push_notifications)
        self.assertEqual(self.test_preferences.theme, 'dark')
        self.assertEqual(self.test_preferences.timezone, 'Europe/Paris')
        
    def test_preferences_update_view_partial(self):
        """
        Test that users can update only some of their preferences.
        
        Verifies that when a user submits a form with only some preference fields,
        only those fields are updated and the others remain unchanged.
        """
        # Log in the test user
        self.client.login(username='testuser', password='password')
        
        # Data for updating only some preferences
        update_data = {
            'preferred_currency': 'JPY',
            'theme': 'dark'
        }
        
        # Submit the form to update preferences
        response = self.client.post(self.preferences_update_url, update_data)
        
        # Check that we're redirected back to the preferences page
        self.assertRedirects(response, self.preferences_url)
        
        # Refresh the preferences from the database
        self.test_preferences.refresh_from_db()
        
        # Verify that only the specified preferences were updated
        self.assertEqual(self.test_preferences.preferred_currency, 'JPY')
        self.assertEqual(self.test_preferences.theme, 'dark')
        
        # Other preferences should remain unchanged
        self.assertEqual(self.test_preferences.preferred_language, 'en')
        self.assertTrue(self.test_preferences.email_notifications)
        self.assertFalse(self.test_preferences.push_notifications)
        self.assertEqual(self.test_preferences.timezone, 'America/New_York')


class UserPreferenceAPITests(TravelGuideBaseTestCase):
    """
    Tests for the UserPreference API endpoints.
    
    These tests verify that the API endpoints for managing user preferences
    work as expected, including authentication, permissions, and data manipulation.
    Each test focuses on a specific endpoint and its functionality.
    """
    
    def setUp(self):
        """
        Set up test data for UserPreference API tests.
        
        Extends the base setUp method to include user preferences for testing.
        """
        super().setUp()
        
        # Create user preferences for the test user
        self.test_preferences = UserPreference.objects.create(
            user=self.test_user,
            preferred_currency='USD',
            preferred_language='en',
            email_notifications=True,
            push_notifications=False,
            theme='light',
            timezone='America/New_York'
        )
        
        # URLs for testing
        self.api_preferences_url = reverse('api:user-preferences')
    
    def test_preferences_api_get_anonymous(self):
        """
        Test that anonymous users cannot access the preferences API.
        
        Verifies that attempting to access the preferences API as an anonymous user
        returns an authentication error.
        """
        response = self.client.get(self.api_preferences_url)
        self.assertEqual(response.status_code, 401)  # Unauthorized
        
    def test_preferences_api_get_authenticated(self):
        """
        Test that authenticated users can get their preferences via the API.
        
        Verifies that an authenticated user can access their preferences via the API
        and that the response contains their current preferences.
        """
        # Log in the test user
        self.client.login(username='testuser', password='password')
        
        # Access the preferences API
        response = self.client.get(self.api_preferences_url)
        self.assertEqual(response.status_code, 200)
        
        # Parse the JSON response
        data = json.loads(response.content)
        
        # Verify the response contains the correct preferences
        self.assertEqual(data['preferred_currency'], 'USD')
        self.assertEqual(data['preferred_language'], 'en')
        self.assertTrue(data['email_notifications'])
        self.assertFalse(data['push_notifications'])
        self.assertEqual(data['theme'], 'light')
        self.assertEqual(data['timezone'], 'America/New_York')
        
    def test_preferences_api_update_anonymous(self):
        """
        Test that anonymous users cannot update preferences via the API.
        
        Verifies that attempting to update preferences via the API as an anonymous user
        returns an authentication error.
        """
        update_data = {'preferred_currency': 'EUR'}
        response = self.client.patch(
            self.api_preferences_url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)  # Unauthorized
        
    def test_preferences_api_update_authenticated(self):
        """
        Test that authenticated users can update their preferences via the API.
        
        Verifies that an authenticated user can update their preferences via the API
        and that the changes are saved to the database.
        """
        # Log in the test user
        self.client.login(username='testuser', password='password')
        
        # Data for updating preferences
        update_data = {
            'preferred_currency': 'EUR',
            'preferred_language': 'fr',
            'theme': 'dark'
        }
        
        # Submit the update via the API
        response = self.client.patch(
            self.api_preferences_url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Parse the JSON response
        data = json.loads(response.content)
        
        # Verify the response contains the updated preferences
        self.assertEqual(data['preferred_currency'], 'EUR')
        self.assertEqual(data['preferred_language'], 'fr')
        self.assertEqual(data['theme'], 'dark')
        
        # Other preferences should remain unchanged
        self.assertTrue(data['email_notifications'])
        self.assertFalse(data['push_notifications'])
        self.assertEqual(data['timezone'], 'America/New_York')
        
        # Refresh the preferences from the database
        self.test_preferences.refresh_from_db()
        
        # Verify that the preferences were updated in the database
        self.assertEqual(self.test_preferences.preferred_currency, 'EUR')
        self.assertEqual(self.test_preferences.preferred_language, 'fr')
        self.assertEqual(self.test_preferences.theme, 'dark')
        self.assertTrue(self.test_preferences.email_notifications)
        self.assertFalse(self.test_preferences.push_notifications)
        self.assertEqual(self.test_preferences.timezone, 'America/New_York')
        
    def test_preferences_api_create_for_new_user(self):
        """
        Test that preferences are created for a new user via the API.
        
        Verifies that when a user without preferences accesses the API,
        a new UserPreference object is created with default values.
        """
        # Create a new user
        new_user = User.objects.create_user(
            username='newuser',
            email='newuser@example.com',
            password='password'
        )
        
        # Log in the new user
        self.client.login(username='newuser', password='password')
        
        # Access the preferences API
        response = self.client.get(self.api_preferences_url)
        self.assertEqual(response.status_code, 200)
        
        # Parse the JSON response
        data = json.loads(response.content)
        
        # Verify the response contains the default preferences
        self.assertEqual(data['preferred_currency'], 'USD')
        self.assertEqual(data['preferred_language'], 'en')
        self.assertTrue(data['email_notifications'])
        self.assertTrue(data['push_notifications'])
        self.assertEqual(data['theme'], 'light')
        self.assertEqual(data['timezone'], 'UTC')
        
        # Verify that a UserPreference object was created for the new user
        self.assertTrue(UserPreference.objects.filter(user=new_user).exists())
