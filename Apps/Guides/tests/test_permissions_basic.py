"""
Test cases for basic permission functionality in the TravelGuide application.

This module contains comprehensive test cases for the permission system,
focusing on basic access control for different user roles.
Every test function is thoroughly documented to make understanding
the tests easier for programmers.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType

from destinations.models import Destination, Region
from tours.models import Tour
from itineraries.models import Itinerary
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class BasicPermissionTests(TravelGuideBaseTestCase):
    """
    Tests for basic permission functionality in the TravelGuide application.
    
    These tests verify that basic permissions work correctly for different
    user roles, including anonymous users, authenticated users, and staff.
    """
    
    def setUp(self):
        """
        Set up test data for basic permission tests.
        
        Extends the base setUp method to include additional users with different roles.
        """
        super().setUp()
        
        # Create additional users with different roles
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='password',
            is_staff=True
        )
        
        self.editor_user = User.objects.create_user(
            username='editor',
            email='editor@example.com',
            password='password'
        )
        
        # Create editor group with specific permissions
        self.editor_group = Group.objects.create(name='Editors')
        
        # Add destination permissions to editor group
        content_type = ContentType.objects.get_for_model(Destination)
        destination_permissions = Permission.objects.filter(
            content_type=content_type,
            codename__in=['add_destination', 'change_destination']
        )
        self.editor_group.permissions.add(*destination_permissions)
        
        # Add editor user to editor group
        self.editor_user.groups.add(self.editor_group)
        
        # Create client for making requests
        self.client = Client()
        
        # URLs for testing
        self.admin_url = reverse('admin:index')
        self.destination_list_url = reverse('destinations:destination_list')
        self.destination_create_url = reverse('destinations:destination_create')
        self.tour_list_url = reverse('tours:tour_list')
        self.tour_create_url = reverse('tours:tour_create')
        
    def test_admin_access_anonymous(self):
        """
        Test that anonymous users cannot access the admin site.
        
        Verifies that anonymous users are redirected to the login page
        when trying to access the admin site.
        """
        response = self.client.get(self.admin_url)
        
        # Check that the user is redirected to the login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        
    def test_admin_access_regular_user(self):
        """
        Test that regular users cannot access the admin site.
        
        Verifies that regular authenticated users are denied access
        to the admin site.
        """
        # Log in as regular user
        self.client.login(username='testuser', password='password')
        
        response = self.client.get(self.admin_url)
        
        # Check that access is denied
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        
    def test_admin_access_staff_user(self):
        """
        Test that staff users can access the admin site.
        
        Verifies that staff users can access the admin site.
        """
        # Log in as staff user
        self.client.login(username='staffuser', password='password')
        
        response = self.client.get(self.admin_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Site administration')
        
    def test_admin_access_superuser(self):
        """
        Test that superusers can access the admin site.
        
        Verifies that superusers can access the admin site.
        """
        # Log in as admin user (superuser)
        self.client.login(username='admin', password='password')
        
        response = self.client.get(self.admin_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Site administration')
        
    def test_destination_list_public_access(self):
        """
        Test that the destination list is publicly accessible.
        
        Verifies that anonymous users can access the destination list page.
        """
        response = self.client.get(self.destination_list_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'destinations/destination_list.html')
        
    def test_destination_create_anonymous(self):
        """
        Test that anonymous users cannot create destinations.
        
        Verifies that anonymous users are redirected to the login page
        when trying to create a destination.
        """
        response = self.client.get(self.destination_create_url)
        
        # Check that the user is redirected to the login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        
    def test_destination_create_regular_user(self):
        """
        Test that regular users cannot create destinations.
        
        Verifies that regular authenticated users are denied access
        to the destination creation page.
        """
        # Log in as regular user
        self.client.login(username='testuser', password='password')
        
        response = self.client.get(self.destination_create_url)
        
        # Check that access is denied
        self.assertEqual(response.status_code, 403)
        
    def test_destination_create_editor(self):
        """
        Test that editors can create destinations.
        
        Verifies that users in the editor group can access
        the destination creation page.
        """
        # Log in as editor
        self.client.login(username='editor', password='password')
        
        response = self.client.get(self.destination_create_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'destinations/destination_form.html')
        
    def test_destination_create_staff(self):
        """
        Test that staff users can create destinations.
        
        Verifies that staff users can access the destination creation page.
        """
        # Log in as staff user
        self.client.login(username='staffuser', password='password')
        
        response = self.client.get(self.destination_create_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'destinations/destination_form.html')
        
    def test_tour_list_public_access(self):
        """
        Test that the tour list is publicly accessible.
        
        Verifies that anonymous users can access the tour list page.
        """
        response = self.client.get(self.tour_list_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tours/tour_list.html')
        
    def test_tour_create_anonymous(self):
        """
        Test that anonymous users cannot create tours.
        
        Verifies that anonymous users are redirected to the login page
        when trying to create a tour.
        """
        response = self.client.get(self.tour_create_url)
        
        # Check that the user is redirected to the login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        
    def test_tour_create_regular_user(self):
        """
        Test that regular users cannot create tours.
        
        Verifies that regular authenticated users are denied access
        to the tour creation page.
        """
        # Log in as regular user
        self.client.login(username='testuser', password='password')
        
        response = self.client.get(self.tour_create_url)
        
        # Check that access is denied
        self.assertEqual(response.status_code, 403)
        
    def test_tour_create_staff(self):
        """
        Test that staff users can create tours.
        
        Verifies that staff users can access the tour creation page.
        """
        # Log in as staff user
        self.client.login(username='staffuser', password='password')
        
        response = self.client.get(self.tour_create_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tours/tour_form.html')


class ObjectLevelPermissionTests(TravelGuideBaseTestCase):
    """
    Tests for object-level permission functionality in the TravelGuide application.
    
    These tests verify that object-level permissions work correctly,
    particularly for user-owned resources like itineraries.
    """
    
    def setUp(self):
        """
        Set up test data for object-level permission tests.
        
        Extends the base setUp method to include additional users and resources.
        """
        super().setUp()
        
        # Create another user
        self.another_user = User.objects.create_user(
            username='anotheruser',
            email='another@example.com',
            password='password'
        )
        
        # Create itineraries owned by different users
        self.test_user_itinerary = Itinerary.objects.create(
            user=self.test_user,
            title="Test User's Itinerary",
            description="An itinerary owned by the test user.",
            start_date='2023-06-15',
            end_date='2023-06-20',
            is_public=False
        )
        
        self.another_user_itinerary = Itinerary.objects.create(
            user=self.another_user,
            title="Another User's Itinerary",
            description="An itinerary owned by another user.",
            start_date='2023-07-10',
            end_date='2023-07-15',
            is_public=False
        )
        
        self.public_itinerary = Itinerary.objects.create(
            user=self.another_user,
            title="Public Itinerary",
            description="A public itinerary that anyone can view.",
            start_date='2023-08-05',
            end_date='2023-08-10',
            is_public=True
        )
        
        # Create client for making requests
        self.client = Client()
        
        # URLs for testing
        self.test_user_itinerary_url = reverse('itineraries:itinerary_detail', kwargs={'pk': self.test_user_itinerary.pk})
        self.another_user_itinerary_url = reverse('itineraries:itinerary_detail', kwargs={'pk': self.another_user_itinerary.pk})
        self.public_itinerary_url = reverse('itineraries:itinerary_detail', kwargs={'pk': self.public_itinerary.pk})
        
    def test_private_itinerary_owner_access(self):
        """
        Test that owners can access their private itineraries.
        
        Verifies that users can access their own private itineraries.
        """
        # Log in as test user
        self.client.login(username='testuser', password='password')
        
        response = self.client.get(self.test_user_itinerary_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'itineraries/itinerary_detail.html')
        self.assertContains(response, "Test User's Itinerary")
        
    def test_private_itinerary_other_user_access(self):
        """
        Test that users cannot access other users' private itineraries.
        
        Verifies that users are denied access to private itineraries
        owned by other users.
        """
        # Log in as test user
        self.client.login(username='testuser', password='password')
        
        response = self.client.get(self.another_user_itinerary_url)
        
        # Check that access is denied
        self.assertEqual(response.status_code, 403)
        
    def test_private_itinerary_anonymous_access(self):
        """
        Test that anonymous users cannot access private itineraries.
        
        Verifies that anonymous users are redirected to the login page
        when trying to access a private itinerary.
        """
        response = self.client.get(self.test_user_itinerary_url)
        
        # Check that the user is redirected to the login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        
    def test_public_itinerary_anonymous_access(self):
        """
        Test that anonymous users can access public itineraries.
        
        Verifies that anonymous users can access public itineraries.
        """
        response = self.client.get(self.public_itinerary_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'itineraries/itinerary_detail.html')
        self.assertContains(response, "Public Itinerary")
        
    def test_public_itinerary_other_user_access(self):
        """
        Test that users can access other users' public itineraries.
        
        Verifies that users can access public itineraries owned by other users.
        """
        # Log in as test user
        self.client.login(username='testuser', password='password')
        
        response = self.client.get(self.public_itinerary_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'itineraries/itinerary_detail.html')
        self.assertContains(response, "Public Itinerary")
        
    def test_itinerary_edit_owner(self):
        """
        Test that owners can edit their itineraries.
        
        Verifies that users can access the edit page for their own itineraries.
        """
        # Log in as test user
        self.client.login(username='testuser', password='password')
        
        edit_url = reverse('itineraries:itinerary_update', kwargs={'pk': self.test_user_itinerary.pk})
        response = self.client.get(edit_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'itineraries/itinerary_form.html')
        
    def test_itinerary_edit_other_user(self):
        """
        Test that users cannot edit other users' itineraries.
        
        Verifies that users are denied access to the edit page for
        itineraries owned by other users.
        """
        # Log in as test user
        self.client.login(username='testuser', password='password')
        
        edit_url = reverse('itineraries:itinerary_update', kwargs={'pk': self.another_user_itinerary.pk})
        response = self.client.get(edit_url)
        
        # Check that access is denied
        self.assertEqual(response.status_code, 403)
        
    def test_itinerary_delete_owner(self):
        """
        Test that owners can delete their itineraries.
        
        Verifies that users can access the delete page for their own itineraries.
        """
        # Log in as test user
        self.client.login(username='testuser', password='password')
        
        delete_url = reverse('itineraries:itinerary_delete', kwargs={'pk': self.test_user_itinerary.pk})
        response = self.client.get(delete_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'itineraries/itinerary_confirm_delete.html')
        
    def test_itinerary_delete_other_user(self):
        """
        Test that users cannot delete other users' itineraries.
        
        Verifies that users are denied access to the delete page for
        itineraries owned by other users.
        """
        # Log in as test user
        self.client.login(username='testuser', password='password')
        
        delete_url = reverse('itineraries:itinerary_delete', kwargs={'pk': self.another_user_itinerary.pk})
        response = self.client.get(delete_url)
        
        # Check that access is denied
        self.assertEqual(response.status_code, 403)
        
    def test_itinerary_delete_staff(self):
        """
        Test that staff users can delete any itinerary.
        
        Verifies that staff users can access the delete page for
        any itinerary, regardless of ownership.
        """
        # Create staff user
        staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='password',
            is_staff=True
        )
        
        # Log in as staff user
        self.client.login(username='staffuser', password='password')
        
        delete_url = reverse('itineraries:itinerary_delete', kwargs={'pk': self.test_user_itinerary.pk})
        response = self.client.get(delete_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'itineraries/itinerary_confirm_delete.html')
