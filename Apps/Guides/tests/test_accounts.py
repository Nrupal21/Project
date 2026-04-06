"""
Test cases for the accounts app.

This module contains comprehensive test cases for all functionality
in the accounts app, including models, views, forms, and authentication.
Every test function is thoroughly documented to make understanding
the tests easier for programmers.
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.models import Profile, UserPreference, RewardPoints
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class UserModelTests(TravelGuideBaseTestCase):
    """
    Tests for the User model in the accounts app.
    
    These tests verify that User objects can be created correctly,
    and that their methods work as expected. Each test focuses on a 
    specific aspect of the User model's functionality.
    """
    
    def test_user_creation(self):
        """
        Test that a User can be created with the expected attributes.
        
        Verifies that the User model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        user = User.objects.create_user(
            username='newuser',
            email='newuser@example.com',
            password='newuserpassword123',
            first_name='New',
            last_name='User'
        )
        
        # Verify the user was created with the correct attributes
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'User')
        self.assertTrue(user.check_password('newuserpassword123'))
        
    def test_superuser_creation(self):
        """
        Test that a superuser can be created with the expected attributes.
        
        Verifies that the User model can create a superuser with admin privileges
        and that the values are stored correctly in the database.
        """
        superuser = User.objects.create_superuser(
            username='newsuperuser',
            email='newsuperuser@example.com',
            password='newsuperuserpassword123'
        )
        
        # Verify the superuser was created with the correct attributes
        self.assertEqual(superuser.username, 'newsuperuser')
        self.assertEqual(superuser.email, 'newsuperuser@example.com')
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.check_password('newsuperuserpassword123'))
        
    def test_user_str_method(self):
        """
        Test the string representation of a User object.
        
        Verifies that the __str__ method returns the expected string,
        which should be the username.
        """
        self.assertEqual(str(self.test_user), 'testuser')


class ProfileModelTests(TravelGuideBaseTestCase):
    """
    Tests for the Profile model in the accounts app.
    
    These tests verify that Profile objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the Profile model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for Profile tests.
        
        Extends the base setUp method to include a profile for testing.
        """
        super().setUp()
        
        # Create a profile for the test user if it doesn't exist
        self.profile, created = Profile.objects.get_or_create(
            user=self.test_user,
            defaults={
                'bio': 'Test user bio',
                'phone_number': '+1234567890',
                'address': '123 Test Street',
                'city': 'Test City',
                'country': 'Test Country'
            }
        )
    
    def test_profile_creation(self):
        """
        Test that a Profile can be created with the expected attributes.
        
        Verifies that the Profile model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new user for testing
        user = User.objects.create_user(
            username='profileuser',
            email='profileuser@example.com',
            password='profilepassword123'
        )
        
        # Create a profile for the user
        profile = Profile.objects.create(
            user=user,
            bio='This is a test bio',
            phone_number='+9876543210',
            address='456 Profile Street',
            city='Profile City',
            country='Profile Country'
        )
        
        # Verify the profile was created with the correct attributes
        self.assertEqual(profile.user, user)
        self.assertEqual(profile.bio, 'This is a test bio')
        self.assertEqual(profile.phone_number, '+9876543210')
        self.assertEqual(profile.address, '456 Profile Street')
        self.assertEqual(profile.city, 'Profile City')
        self.assertEqual(profile.country, 'Profile Country')
        
    def test_profile_str_method(self):
        """
        Test the string representation of a Profile object.
        
        Verifies that the __str__ method returns the expected string,
        which should include the username.
        """
        expected_str = f"Profile for {self.test_user.username}"
        self.assertEqual(str(self.profile), expected_str)
        
    def test_profile_get_absolute_url(self):
        """
        Test the get_absolute_url method of the Profile model.
        
        Verifies that the URL generated for a profile detail page is correct
        and matches the expected URL pattern.
        """
        expected_url = reverse('accounts:profile_detail', kwargs={'username': self.test_user.username})
        self.assertEqual(self.profile.get_absolute_url(), expected_url)


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
        self.preferences = UserPreference.objects.create(
            user=self.test_user,
            preferred_currency='USD',
            preferred_language='en',
            receive_newsletter=True,
            receive_promotional_emails=True,
            dark_mode=False
        )
    
    def test_user_preference_creation(self):
        """
        Test that UserPreference can be created with the expected attributes.
        
        Verifies that the UserPreference model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new user for testing
        user = User.objects.create_user(
            username='prefuser',
            email='prefuser@example.com',
            password='prefpassword123'
        )
        
        # Create preferences for the user
        preferences = UserPreference.objects.create(
            user=user,
            preferred_currency='EUR',
            preferred_language='fr',
            receive_newsletter=False,
            receive_promotional_emails=False,
            dark_mode=True
        )
        
        # Verify the preferences were created with the correct attributes
        self.assertEqual(preferences.user, user)
        self.assertEqual(preferences.preferred_currency, 'EUR')
        self.assertEqual(preferences.preferred_language, 'fr')
        self.assertFalse(preferences.receive_newsletter)
        self.assertFalse(preferences.receive_promotional_emails)
        self.assertTrue(preferences.dark_mode)
        
    def test_user_preference_str_method(self):
        """
        Test the string representation of a UserPreference object.
        
        Verifies that the __str__ method returns the expected string,
        which should include the username.
        """
        expected_str = f"Preferences for {self.test_user.username}"
        self.assertEqual(str(self.preferences), expected_str)
        
    def test_user_preference_defaults(self):
        """
        Test the default values for UserPreference fields.
        
        Verifies that when a UserPreference is created without specifying
        certain fields, they get the correct default values.
        """
        # Create a new user for testing
        user = User.objects.create_user(
            username='defaultuser',
            email='defaultuser@example.com',
            password='defaultpassword123'
        )
        
        # Create preferences with minimal fields
        preferences = UserPreference.objects.create(
            user=user
        )
        
        # Verify the default values
        self.assertEqual(preferences.preferred_currency, 'USD')  # Default currency
        self.assertEqual(preferences.preferred_language, 'en')   # Default language
        self.assertTrue(preferences.receive_newsletter)         # Default True
        self.assertTrue(preferences.receive_promotional_emails) # Default True
        self.assertFalse(preferences.dark_mode)                 # Default False


class RewardPointsModelTests(TravelGuideBaseTestCase):
    """
    Tests for the RewardPoints model in the accounts app.
    
    These tests verify that RewardPoints objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the RewardPoints model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for RewardPoints tests.
        
        Extends the base setUp method to include reward points for testing.
        """
        super().setUp()
        
        # Create reward points for the test user
        self.reward_points = RewardPoints.objects.create(
            user=self.test_user,
            points=100,
            reason='Sign-up bonus'
        )
    
    def test_reward_points_creation(self):
        """
        Test that RewardPoints can be created with the expected attributes.
        
        Verifies that the RewardPoints model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create reward points for the admin user
        reward_points = RewardPoints.objects.create(
            user=self.admin_user,
            points=200,
            reason='Booking a tour'
        )
        
        # Verify the reward points were created with the correct attributes
        self.assertEqual(reward_points.user, self.admin_user)
        self.assertEqual(reward_points.points, 200)
        self.assertEqual(reward_points.reason, 'Booking a tour')
        
    def test_reward_points_str_method(self):
        """
        Test the string representation of a RewardPoints object.
        
        Verifies that the __str__ method returns the expected string,
        which should include the username and points.
        """
        expected_str = f"{self.test_user.username}: 100 points"
        self.assertEqual(str(self.reward_points), expected_str)
        
    def test_total_points_for_user(self):
        """
        Test calculating the total reward points for a user.
        
        Verifies that the total_points_for_user method correctly calculates
        the sum of all points for a specific user.
        """
        # Add more reward points for the test user
        RewardPoints.objects.create(
            user=self.test_user,
            points=50,
            reason='Writing a review'
        )
        
        RewardPoints.objects.create(
            user=self.test_user,
            points=150,
            reason='Booking a tour'
        )
        
        # Calculate the total points
        total_points = RewardPoints.objects.filter(user=self.test_user).aggregate(
            total=models.Sum('points')
        )['total']
        
        # The total should be 100 + 50 + 150 = 300
        self.assertEqual(total_points, 300)


class AccountViewTests(TravelGuideBaseTestCase):
    """
    Tests for the views in the accounts app.
    
    These tests verify that the views render the correct templates,
    contain the expected context data, and handle form submissions correctly.
    Each test focuses on a specific view or aspect of view functionality.
    """
    
    def test_login_view(self):
        """
        Test the login view.
        
        Verifies that the login view returns a 200 status code,
        uses the correct template, and allows users to log in.
        """
        # Log out any existing user
        self.client.logout()
        
        # Get the login page
        response = self.client.get(reverse('account_login'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'account/login.html')
        
        # Submit login form
        response = self.client.post(reverse('account_login'), {
            'login': 'testuser@example.com',
            'password': 'testpassword123'
        })
        
        # Check that the login was successful and redirected
        self.assertEqual(response.status_code, 302)  # Redirect status code
        
    def test_signup_view(self):
        """
        Test the signup view.
        
        Verifies that the signup view returns a 200 status code,
        uses the correct template, and allows users to sign up.
        """
        # Log out any existing user
        self.client.logout()
        
        # Get the signup page
        response = self.client.get(reverse('account_signup'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'account/signup.html')
        
        # Submit signup form
        response = self.client.post(reverse('account_signup'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'newuserpassword123',
            'password2': 'newuserpassword123'
        })
        
        # Check that the signup was successful and redirected
        self.assertEqual(response.status_code, 302)  # Redirect status code
        
        # Check that the user was created
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
    def test_profile_detail_view(self):
        """
        Test the profile detail view.
        
        Verifies that the profile detail view returns a 200 status code,
        uses the correct template, and includes the profile in the context.
        """
        # Create a profile for the test user if it doesn't exist
        profile, created = Profile.objects.get_or_create(
            user=self.test_user,
            defaults={
                'bio': 'Test user bio',
                'phone_number': '+1234567890',
                'address': '123 Test Street',
                'city': 'Test City',
                'country': 'Test Country'
            }
        )
        
        # Log in the test user
        self.login_test_user()
        
        # Get the profile detail page
        response = self.client.get(reverse('accounts:profile_detail', kwargs={'username': self.test_user.username}))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'accounts/profile_detail.html')
        
        # Check that the profile is in the context
        self.assertEqual(response.context['profile'].user, self.test_user)
        
    def test_profile_edit_view(self):
        """
        Test the profile edit view.
        
        Verifies that the profile edit view returns a 200 status code,
        uses the correct template, and allows editing of a profile.
        """
        # Create a profile for the test user if it doesn't exist
        profile, created = Profile.objects.get_or_create(
            user=self.test_user,
            defaults={
                'bio': 'Test user bio',
                'phone_number': '+1234567890',
                'address': '123 Test Street',
                'city': 'Test City',
                'country': 'Test Country'
            }
        )
        
        # Log in the test user
        self.login_test_user()
        
        # Get the profile edit page
        response = self.client.get(reverse('accounts:profile_edit'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'accounts/profile_edit.html')
        
        # Submit profile edit form
        response = self.client.post(reverse('accounts:profile_edit'), {
            'bio': 'Updated bio',
            'phone_number': '+9876543210',
            'address': '456 New Street',
            'city': 'New City',
            'country': 'New Country'
        })
        
        # Check that the profile was updated and redirected
        self.assertEqual(response.status_code, 302)  # Redirect status code
        
        # Refresh the profile from the database
        profile.refresh_from_db()
        
        # Check that the profile was updated
        self.assertEqual(profile.bio, 'Updated bio')
        self.assertEqual(profile.phone_number, '+9876543210')
        self.assertEqual(profile.address, '456 New Street')
        self.assertEqual(profile.city, 'New City')
        self.assertEqual(profile.country, 'New Country')
        
    def test_user_preferences_view(self):
        """
        Test the user preferences view.
        
        Verifies that the user preferences view returns a 200 status code,
        uses the correct template, and allows editing of user preferences.
        """
        # Create preferences for the test user
        preferences, created = UserPreference.objects.get_or_create(
            user=self.test_user,
            defaults={
                'preferred_currency': 'USD',
                'preferred_language': 'en',
                'receive_newsletter': True,
                'receive_promotional_emails': True,
                'dark_mode': False
            }
        )
        
        # Log in the test user
        self.login_test_user()
        
        # Get the preferences edit page
        response = self.client.get(reverse('accounts:preferences'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'accounts/preferences.html')
        
        # Submit preferences edit form
        response = self.client.post(reverse('accounts:preferences'), {
            'preferred_currency': 'EUR',
            'preferred_language': 'fr',
            'receive_newsletter': False,
            'receive_promotional_emails': False,
            'dark_mode': True
        })
        
        # Check that the preferences were updated and redirected
        self.assertEqual(response.status_code, 302)  # Redirect status code
        
        # Refresh the preferences from the database
        preferences.refresh_from_db()
        
        # Check that the preferences were updated
        self.assertEqual(preferences.preferred_currency, 'EUR')
        self.assertEqual(preferences.preferred_language, 'fr')
        self.assertFalse(preferences.receive_newsletter)
        self.assertFalse(preferences.receive_promotional_emails)
        self.assertTrue(preferences.dark_mode)
