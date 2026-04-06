"""
Test cases for admin permissions in the TravelGuide application.

This module contains comprehensive test cases for the Django admin interface,
focusing on authentication, authorization, and access control for admin pages.
Every test function is thoroughly documented to make understanding
the tests easier for programmers.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.sites import AdminSite

from destinations.models import Destination, Region, Attraction
from tours.models import Tour, TourCategory
from itineraries.models import Itinerary
from reviews.models import Review
from bookings.models import Booking
from core.models import SiteSettings, FAQ, Testimonial
from accounts.models import Profile, UserPreference
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class AdminAccessTests(TravelGuideBaseTestCase):
    """
    Tests for admin access in the TravelGuide application.
    
    These tests verify that admin access is properly restricted
    to authorized users and that different user roles have
    appropriate access to admin pages.
    """
    
    def setUp(self):
        """
        Set up test data for admin access tests.
        
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
        
        self.staff_superuser = User.objects.create_user(
            username='staffsuperuser',
            email='staffsuper@example.com',
            password='password',
            is_staff=True,
            is_superuser=True
        )
        
        # Create a staff user with limited permissions
        self.limited_staff = User.objects.create_user(
            username='limitedstaff',
            email='limited@example.com',
            password='password',
            is_staff=True
        )
        
        # Add specific permissions to limited staff
        content_type = ContentType.objects.get_for_model(Destination)
        destination_permissions = Permission.objects.filter(
            content_type=content_type
        )
        self.limited_staff.user_permissions.add(*destination_permissions)
        
        # Create client for making requests
        self.client = Client()
        
        # URLs for testing
        self.admin_url = reverse('admin:index')
        self.admin_login_url = reverse('admin:login')
        self.admin_logout_url = reverse('admin:logout')
        
        # Admin model URLs
        self.admin_user_url = reverse('admin:auth_user_changelist')
        self.admin_destination_url = reverse('admin:destinations_destination_changelist')
        self.admin_tour_url = reverse('admin:tours_tour_changelist')
        self.admin_itinerary_url = reverse('admin:itineraries_itinerary_changelist')
        self.admin_sitesettings_url = reverse('admin:core_sitesettings_changelist')
        
    def test_admin_login_page_access(self):
        """
        Test that the admin login page is accessible to anyone.
        
        Verifies that anonymous users can access the admin login page.
        """
        response = self.client.get(self.admin_login_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Log in')
        
    def test_admin_index_anonymous(self):
        """
        Test that anonymous users cannot access the admin index page.
        
        Verifies that anonymous users are redirected to the login page
        when trying to access the admin index page.
        """
        response = self.client.get(self.admin_url)
        
        # Check that the user is redirected to the login page
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.admin_login_url, response.url)
        
    def test_admin_index_regular_user(self):
        """
        Test that regular users cannot access the admin index page.
        
        Verifies that regular authenticated users are redirected to the login page
        when trying to access the admin index page.
        """
        # Log in as regular user
        self.client.login(username='testuser', password='password')
        
        response = self.client.get(self.admin_url)
        
        # Check that the user is redirected to the login page
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.admin_login_url, response.url)
        
    def test_admin_index_staff(self):
        """
        Test that staff users can access the admin index page.
        
        Verifies that staff users can access the admin index page.
        """
        # Log in as staff user
        self.client.login(username='staffuser', password='password')
        
        response = self.client.get(self.admin_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Site administration')
        
    def test_admin_index_superuser(self):
        """
        Test that superusers can access the admin index page.
        
        Verifies that superusers can access the admin index page.
        """
        # Log in as admin user (superuser)
        self.client.login(username='admin', password='password')
        
        response = self.client.get(self.admin_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Site administration')
        
    def test_admin_user_model_limited_staff(self):
        """
        Test that limited staff users cannot access user admin.
        
        Verifies that staff users with limited permissions cannot
        access the user admin page.
        """
        # Log in as limited staff user
        self.client.login(username='limitedstaff', password='password')
        
        response = self.client.get(self.admin_user_url)
        
        # Check that access is denied
        self.assertEqual(response.status_code, 403)
        
    def test_admin_user_model_staff(self):
        """
        Test that regular staff users cannot access user admin.
        
        Verifies that regular staff users without specific permissions
        cannot access the user admin page.
        """
        # Log in as staff user
        self.client.login(username='staffuser', password='password')
        
        response = self.client.get(self.admin_user_url)
        
        # Check that access is denied
        self.assertEqual(response.status_code, 403)
        
    def test_admin_user_model_superuser(self):
        """
        Test that superusers can access user admin.
        
        Verifies that superusers can access the user admin page.
        """
        # Log in as admin user (superuser)
        self.client.login(username='admin', password='password')
        
        response = self.client.get(self.admin_user_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Select user to change')
        
    def test_admin_destination_model_limited_staff(self):
        """
        Test that limited staff users can access destination admin.
        
        Verifies that staff users with destination permissions can
        access the destination admin page.
        """
        # Log in as limited staff user
        self.client.login(username='limitedstaff', password='password')
        
        response = self.client.get(self.admin_destination_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Select destination to change')
        
    def test_admin_tour_model_limited_staff(self):
        """
        Test that limited staff users cannot access tour admin.
        
        Verifies that staff users without tour permissions cannot
        access the tour admin page.
        """
        # Log in as limited staff user
        self.client.login(username='limitedstaff', password='password')
        
        response = self.client.get(self.admin_tour_url)
        
        # Check that access is denied
        self.assertEqual(response.status_code, 403)
        
    def test_admin_tour_model_superuser(self):
        """
        Test that superusers can access tour admin.
        
        Verifies that superusers can access the tour admin page.
        """
        # Log in as admin user (superuser)
        self.client.login(username='admin', password='password')
        
        response = self.client.get(self.admin_tour_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Select tour to change')


class AdminModelPermissionTests(TravelGuideBaseTestCase):
    """
    Tests for admin model permissions in the TravelGuide application.
    
    These tests verify that admin model permissions work correctly,
    including add, change, delete, and view permissions.
    """
    
    def setUp(self):
        """
        Set up test data for admin model permission tests.
        
        Extends the base setUp method to include additional users with different permissions.
        """
        super().setUp()
        
        # Create a staff user with view-only permissions
        self.view_only_staff = User.objects.create_user(
            username='viewonly',
            email='viewonly@example.com',
            password='password',
            is_staff=True
        )
        
        # Add view permissions to view-only staff
        content_type = ContentType.objects.get_for_model(Destination)
        view_permission = Permission.objects.get(
            content_type=content_type,
            codename='view_destination'
        )
        self.view_only_staff.user_permissions.add(view_permission)
        
        # Create a staff user with add/change permissions
        self.editor_staff = User.objects.create_user(
            username='editorstaff',
            email='editor@example.com',
            password='password',
            is_staff=True
        )
        
        # Add add/change permissions to editor staff
        content_type = ContentType.objects.get_for_model(Destination)
        add_permission = Permission.objects.get(
            content_type=content_type,
            codename='add_destination'
        )
        change_permission = Permission.objects.get(
            content_type=content_type,
            codename='change_destination'
        )
        self.editor_staff.user_permissions.add(add_permission, change_permission)
        
        # Create test destination
        self.test_region = Region.objects.create(
            name="Test Region",
            description="A test region"
        )
        
        self.test_destination = Destination.objects.create(
            name="Test Destination",
            description="A test destination",
            region=self.test_region
        )
        
        # Create client for making requests
        self.client = Client()
        
        # URLs for testing
        self.admin_destination_url = reverse('admin:destinations_destination_changelist')
        self.admin_destination_add_url = reverse('admin:destinations_destination_add')
        self.admin_destination_change_url = reverse('admin:destinations_destination_change', args=[self.test_destination.pk])
        self.admin_destination_delete_url = reverse('admin:destinations_destination_delete', args=[self.test_destination.pk])
        
    def test_admin_destination_view_permission(self):
        """
        Test that staff users with view permission can view destinations.
        
        Verifies that staff users with view permission can access
        the destination changelist page.
        """
        # Log in as view-only staff
        self.client.login(username='viewonly', password='password')
        
        response = self.client.get(self.admin_destination_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Select destination to change')
        
    def test_admin_destination_view_detail_permission(self):
        """
        Test that staff users with view permission can view destination details.
        
        Verifies that staff users with view permission can access
        the destination change page (in read-only mode).
        """
        # Log in as view-only staff
        self.client.login(username='viewonly', password='password')
        
        response = self.client.get(self.admin_destination_change_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Destination')
        
        # Check that the form is read-only
        self.assertContains(response, 'readonly')
        
    def test_admin_destination_add_view_only(self):
        """
        Test that staff users with view-only permission cannot add destinations.
        
        Verifies that staff users with only view permission are denied access
        when trying to add a destination.
        """
        # Log in as view-only staff
        self.client.login(username='viewonly', password='password')
        
        response = self.client.get(self.admin_destination_add_url)
        
        # Check that access is denied
        self.assertEqual(response.status_code, 403)
        
    def test_admin_destination_change_view_only(self):
        """
        Test that staff users with view-only permission cannot change destinations.
        
        Verifies that staff users with only view permission cannot
        submit changes to a destination.
        """
        # Log in as view-only staff
        self.client.login(username='viewonly', password='password')
        
        response = self.client.post(self.admin_destination_change_url, {
            'name': 'Updated Destination',
            'description': 'An updated destination',
            'region': self.test_region.pk
        })
        
        # Check that access is denied
        self.assertEqual(response.status_code, 403)
        
    def test_admin_destination_delete_view_only(self):
        """
        Test that staff users with view-only permission cannot delete destinations.
        
        Verifies that staff users with only view permission are denied access
        when trying to delete a destination.
        """
        # Log in as view-only staff
        self.client.login(username='viewonly', password='password')
        
        response = self.client.get(self.admin_destination_delete_url)
        
        # Check that access is denied
        self.assertEqual(response.status_code, 403)
        
    def test_admin_destination_add_editor(self):
        """
        Test that staff users with add permission can add destinations.
        
        Verifies that staff users with add permission can access
        the destination add page and create a new destination.
        """
        # Log in as editor staff
        self.client.login(username='editorstaff', password='password')
        
        # First, check that the add page is accessible
        response = self.client.get(self.admin_destination_add_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add destination')
        
        # Then, try to add a new destination
        response = self.client.post(self.admin_destination_add_url, {
            'name': 'New Destination',
            'description': 'A new destination',
            'region': self.test_region.pk
        }, follow=True)
        
        # Check that the destination was added
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Destination.objects.filter(name='New Destination').exists())
        
    def test_admin_destination_change_editor(self):
        """
        Test that staff users with change permission can change destinations.
        
        Verifies that staff users with change permission can access
        the destination change page and update a destination.
        """
        # Log in as editor staff
        self.client.login(username='editorstaff', password='password')
        
        # First, check that the change page is accessible
        response = self.client.get(self.admin_destination_change_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Change destination')
        
        # Then, try to update the destination
        response = self.client.post(self.admin_destination_change_url, {
            'name': 'Updated Destination',
            'description': 'An updated destination',
            'region': self.test_region.pk
        }, follow=True)
        
        # Check that the destination was updated
        self.assertEqual(response.status_code, 200)
        self.test_destination.refresh_from_db()
        self.assertEqual(self.test_destination.name, 'Updated Destination')
        
    def test_admin_destination_delete_editor(self):
        """
        Test that staff users without delete permission cannot delete destinations.
        
        Verifies that staff users without delete permission are denied access
        when trying to delete a destination.
        """
        # Log in as editor staff (who doesn't have delete permission)
        self.client.login(username='editorstaff', password='password')
        
        response = self.client.get(self.admin_destination_delete_url)
        
        # Check that access is denied
        self.assertEqual(response.status_code, 403)


class AdminSiteConfigTests(TravelGuideBaseTestCase):
    """
    Tests for admin site configuration in the TravelGuide application.
    
    These tests verify that the admin site is properly configured,
    including custom admin views, admin actions, and admin filters.
    """
    
    def setUp(self):
        """
        Set up test data for admin site configuration tests.
        
        Extends the base setUp method to include additional resources for testing.
        """
        super().setUp()
        
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
        
        # Create multiple testimonials for testing list filters
        self.approved_testimonial = Testimonial.objects.create(
            name="Approved User",
            content="This is an approved testimonial",
            rating=5,
            is_approved=True
        )
        
        self.pending_testimonial = Testimonial.objects.create(
            name="Pending User",
            content="This is a pending testimonial",
            rating=4,
            is_approved=False
        )
        
        # Create client for making requests
        self.client = Client()
        
        # Log in as admin user
        self.client.login(username='admin', password='password')
        
        # URLs for testing
        self.admin_testimonial_url = reverse('admin:core_testimonial_changelist')
        self.admin_tour_url = reverse('admin:tours_tour_changelist')
        
    def test_admin_list_filter(self):
        """
        Test that admin list filters work correctly.
        
        Verifies that admin list filters can be used to filter the list of objects.
        """
        # Access testimonial changelist with filter for approved testimonials
        response = self.client.get(f"{self.admin_testimonial_url}?is_approved__exact=1")
        
        # Check that only approved testimonials are shown
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Approved User")
        self.assertNotContains(response, "Pending User")
        
        # Access testimonial changelist with filter for pending testimonials
        response = self.client.get(f"{self.admin_testimonial_url}?is_approved__exact=0")
        
        # Check that only pending testimonials are shown
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pending User")
        self.assertNotContains(response, "Approved User")
        
    def test_admin_search(self):
        """
        Test that admin search works correctly.
        
        Verifies that admin search can be used to find objects.
        """
        # Access tour changelist with search for "Test Tour"
        response = self.client.get(f"{self.admin_tour_url}?q=Test+Tour")
        
        # Check that the search results are correct
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Tour")
        
        # Access tour changelist with search for non-existent tour
        response = self.client.get(f"{self.admin_tour_url}?q=Nonexistent+Tour")
        
        # Check that no results are found
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Test Tour")
        self.assertContains(response, "0 tours")
        
    def test_admin_actions(self):
        """
        Test that admin actions work correctly.
        
        Verifies that admin actions can be used to perform bulk operations.
        """
        # Approve the pending testimonial using admin action
        response = self.client.post(self.admin_testimonial_url, {
            'action': 'approve_testimonials',
            '_selected_action': [self.pending_testimonial.pk],
        }, follow=True)
        
        # Check that the testimonial was approved
        self.assertEqual(response.status_code, 200)
        self.pending_testimonial.refresh_from_db()
        self.assertTrue(self.pending_testimonial.is_approved)
        
        # Check that success message is displayed
        self.assertContains(response, "1 testimonial was successfully approved")
        
    def test_admin_readonly_fields(self):
        """
        Test that admin readonly fields work correctly.
        
        Verifies that readonly fields cannot be modified in the admin.
        """
        # Access the change page for a testimonial
        change_url = reverse('admin:core_testimonial_change', args=[self.approved_testimonial.pk])
        response = self.client.get(change_url)
        
        # Check that the created_at field is readonly
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'field-created_at')
        
        # Try to update the testimonial with a new created_at value
        import datetime
        new_date = datetime.datetime.now() - datetime.timedelta(days=30)
        response = self.client.post(change_url, {
            'name': 'Approved User',
            'content': 'This is an approved testimonial',
            'rating': 5,
            'is_approved': True,
            'created_at': new_date.strftime('%Y-%m-%d %H:%M:%S')
        }, follow=True)
        
        # Check that the testimonial was updated but created_at was not changed
        self.assertEqual(response.status_code, 200)
        self.approved_testimonial.refresh_from_db()
        self.assertNotEqual(self.approved_testimonial.created_at.date(), new_date.date())
