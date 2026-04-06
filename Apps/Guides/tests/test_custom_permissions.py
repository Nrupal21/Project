"""
Test cases for custom permissions in the TravelGuide application.

This module contains comprehensive test cases for custom permission classes,
decorators, and middleware components used for access control.
Every test function is thoroughly documented to make understanding
the tests easier for programmers.
"""

from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.views import View
from django.utils.decorators import method_decorator
from rest_framework.test import APIClient
from rest_framework import status
from functools import wraps

from destinations.models import Destination, Region
from tours.models import Tour
from itineraries.models import Itinerary
from accounts.models import Profile, UserPreference
from core.permissions import (
    IsOwnerOrReadOnly,
    IsAdminOrReadOnly,
    IsStaffOrReadOnly,
    IsPremiumUser
)
from core.decorators import (
    staff_required,
    premium_required,
    maintenance_exempt
)
from core.middleware import MaintenanceModeMiddleware
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class CustomPermissionDecoratorsTests(TravelGuideBaseTestCase):
    """
    Tests for custom permission decorators in the TravelGuide application.
    
    These tests verify that custom permission decorators work correctly,
    including staff_required, premium_required, and maintenance_exempt.
    """
    
    def setUp(self):
        """
        Set up test data for custom permission decorator tests.
        
        Extends the base setUp method to include a request factory and test views.
        """
        super().setUp()
        
        # Create a request factory
        self.factory = RequestFactory()
        
        # Create additional users with different roles
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='password',
            is_staff=True
        )
        
        self.premium_user = User.objects.create_user(
            username='premiumuser',
            email='premium@example.com',
            password='password'
        )
        
        # Set premium status for premium user
        profile = Profile.objects.get(user=self.premium_user)
        profile.is_premium = True
        profile.save()
        
        # Define test views with decorators
        
        # Staff required view
        @staff_required
        def staff_view(request):
            """Test view that requires staff access."""
            return HttpResponse("Staff access granted")
        
        # Premium required view
        @premium_required
        def premium_view(request):
            """Test view that requires premium access."""
            return HttpResponse("Premium access granted")
        
        # Maintenance exempt view
        @maintenance_exempt
        def maintenance_exempt_view(request):
            """Test view that is exempt from maintenance mode."""
            return HttpResponse("Maintenance exempt access granted")
        
        # Class-based view with staff required decorator
        class StaffView(View):
            """Test class-based view that requires staff access."""
            
            @method_decorator(staff_required)
            def dispatch(self, request, *args, **kwargs):
                return super().dispatch(request, *args, **kwargs)
                
            def get(self, request):
                return HttpResponse("Staff access granted")
        
        # Store the test views
        self.staff_view = staff_view
        self.premium_view = premium_view
        self.maintenance_exempt_view = maintenance_exempt_view
        self.staff_class_view = StaffView.as_view()
        
    def test_staff_required_decorator_staff_user(self):
        """
        Test that staff_required decorator allows staff users.
        
        Verifies that staff users can access views decorated with staff_required.
        """
        request = self.factory.get('/test-staff/')
        request.user = self.staff_user
        
        response = self.staff_view(request)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Staff access granted")
        
    def test_staff_required_decorator_regular_user(self):
        """
        Test that staff_required decorator denies regular users.
        
        Verifies that regular users are denied access to views
        decorated with staff_required.
        """
        request = self.factory.get('/test-staff/')
        request.user = self.test_user
        
        response = self.staff_view(request)
        
        # Check that access is denied
        self.assertEqual(response.status_code, 403)
        self.assertIn("Staff access required", response.content.decode())
        
    def test_staff_required_decorator_anonymous(self):
        """
        Test that staff_required decorator redirects anonymous users.
        
        Verifies that anonymous users are redirected to the login page
        when trying to access views decorated with staff_required.
        """
        request = self.factory.get('/test-staff/')
        request.user = self.anonymous_user
        
        # Add session and messages attributes required by the decorator
        request.session = {}
        request._messages = self.get_messages_storage(request)
        
        response = self.staff_view(request)
        
        # Check that the user is redirected to the login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])
        
    def test_staff_required_decorator_class_based_view(self):
        """
        Test that staff_required decorator works with class-based views.
        
        Verifies that the staff_required decorator works correctly
        when applied to class-based views.
        """
        # Test with staff user
        request = self.factory.get('/test-staff-class/')
        request.user = self.staff_user
        
        response = self.staff_class_view(request)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Staff access granted")
        
        # Test with regular user
        request = self.factory.get('/test-staff-class/')
        request.user = self.test_user
        
        response = self.staff_class_view(request)
        
        # Check that access is denied
        self.assertEqual(response.status_code, 403)
        self.assertIn("Staff access required", response.content.decode())
        
    def test_premium_required_decorator_premium_user(self):
        """
        Test that premium_required decorator allows premium users.
        
        Verifies that premium users can access views decorated with premium_required.
        """
        request = self.factory.get('/test-premium/')
        request.user = self.premium_user
        
        response = self.premium_view(request)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Premium access granted")
        
    def test_premium_required_decorator_regular_user(self):
        """
        Test that premium_required decorator denies regular users.
        
        Verifies that regular users are denied access to views
        decorated with premium_required.
        """
        request = self.factory.get('/test-premium/')
        request.user = self.test_user
        
        response = self.premium_view(request)
        
        # Check that access is denied
        self.assertEqual(response.status_code, 403)
        self.assertIn("Premium access required", response.content.decode())
        
    def test_premium_required_decorator_anonymous(self):
        """
        Test that premium_required decorator redirects anonymous users.
        
        Verifies that anonymous users are redirected to the login page
        when trying to access views decorated with premium_required.
        """
        request = self.factory.get('/test-premium/')
        request.user = self.anonymous_user
        
        # Add session and messages attributes required by the decorator
        request.session = {}
        request._messages = self.get_messages_storage(request)
        
        response = self.premium_view(request)
        
        # Check that the user is redirected to the login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])
        
    def test_maintenance_exempt_decorator(self):
        """
        Test that maintenance_exempt decorator works correctly.
        
        Verifies that views decorated with maintenance_exempt can be
        accessed even when maintenance mode is enabled.
        """
        # Create a request
        request = self.factory.get('/test-maintenance-exempt/')
        request.user = self.test_user
        
        # Create a maintenance mode middleware
        middleware = MaintenanceModeMiddleware(lambda r: HttpResponse("Normal response"))
        
        # Enable maintenance mode
        from django.conf import settings
        original_setting = getattr(settings, 'MAINTENANCE_MODE', False)
        settings.MAINTENANCE_MODE = True
        
        try:
            # Process the request with the middleware
            response = middleware(request)
            
            # Check that maintenance mode is enforced
            self.assertEqual(response.status_code, 503)
            self.assertIn("Maintenance", response.content.decode())
            
            # Now test with the exempt view
            response = self.maintenance_exempt_view(request)
            
            # Check that the exempt view is accessible
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content.decode(), "Maintenance exempt access granted")
            
        finally:
            # Restore original setting
            settings.MAINTENANCE_MODE = original_setting
            
    def get_messages_storage(self, request):
        """
        Helper method to create a messages storage for testing.
        
        Returns a simple object that mimics the messages framework storage.
        """
        class MessagesStorage:
            """Simple messages storage for testing."""
            
            def __init__(self):
                self.messages = []
                
            def add(self, level, message, extra_tags=''):
                """Add a message to the storage."""
                self.messages.append((level, message, extra_tags))
                
        return MessagesStorage()


class DRFPermissionClassesTests(TravelGuideBaseTestCase):
    """
    Tests for DRF permission classes in the TravelGuide application.
    
    These tests verify that custom DRF permission classes work correctly,
    including IsOwnerOrReadOnly, IsAdminOrReadOnly, IsStaffOrReadOnly,
    and IsPremiumUser.
    """
    
    def setUp(self):
        """
        Set up test data for DRF permission class tests.
        
        Extends the base setUp method to include additional users and resources.
        """
        super().setUp()
        
        # Create additional users with different roles
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='password',
            is_staff=True
        )
        
        self.premium_user = User.objects.create_user(
            username='premiumuser',
            email='premium@example.com',
            password='password'
        )
        
        # Set premium status for premium user
        profile = Profile.objects.get(user=self.premium_user)
        profile.is_premium = True
        profile.save()
        
        self.another_user = User.objects.create_user(
            username='anotheruser',
            email='another@example.com',
            password='password'
        )
        
        # Create test resources
        self.test_itinerary = Itinerary.objects.create(
            user=self.test_user,
            title="Test User's Itinerary",
            description="An itinerary owned by the test user",
            start_date='2023-06-15',
            end_date='2023-06-20',
            is_public=False
        )
        
        # Create API clients
        self.api_client = APIClient()
        self.staff_api_client = APIClient()
        self.premium_api_client = APIClient()
        self.another_api_client = APIClient()
        
        # Authenticate API clients
        self.api_client.force_authenticate(user=self.test_user)
        self.staff_api_client.force_authenticate(user=self.staff_user)
        self.premium_api_client.force_authenticate(user=self.premium_user)
        self.another_api_client.force_authenticate(user=self.another_user)
        
        # Create a request factory
        self.factory = RequestFactory()
        
    def test_is_owner_or_readonly_permission(self):
        """
        Test that IsOwnerOrReadOnly permission works correctly.
        
        Verifies that the IsOwnerOrReadOnly permission allows read access
        to all users but write access only to the owner.
        """
        permission = IsOwnerOrReadOnly()
        
        # Create a mock object with an owner
        class MockObject:
            """Mock object for testing ownership permissions."""
            
            def __init__(self, user):
                self.user = user
                
        obj = MockObject(self.test_user)
        
        # Test GET request (read)
        request = self.factory.get('/test/')
        request.user = self.another_user
        request.method = 'GET'
        
        # Check that read access is granted to non-owner
        self.assertTrue(permission.has_object_permission(request, None, obj))
        
        # Test PUT request (write) from owner
        request = self.factory.put('/test/')
        request.user = self.test_user
        request.method = 'PUT'
        
        # Check that write access is granted to owner
        self.assertTrue(permission.has_object_permission(request, None, obj))
        
        # Test PUT request (write) from non-owner
        request = self.factory.put('/test/')
        request.user = self.another_user
        request.method = 'PUT'
        
        # Check that write access is denied to non-owner
        self.assertFalse(permission.has_object_permission(request, None, obj))
        
    def test_is_admin_or_readonly_permission(self):
        """
        Test that IsAdminOrReadOnly permission works correctly.
        
        Verifies that the IsAdminOrReadOnly permission allows read access
        to all users but write access only to admin users.
        """
        permission = IsAdminOrReadOnly()
        
        # Test GET request (read) from regular user
        request = self.factory.get('/test/')
        request.user = self.test_user
        request.method = 'GET'
        
        # Check that read access is granted to regular user
        self.assertTrue(permission.has_permission(request, None))
        
        # Test POST request (write) from regular user
        request = self.factory.post('/test/')
        request.user = self.test_user
        request.method = 'POST'
        
        # Check that write access is denied to regular user
        self.assertFalse(permission.has_permission(request, None))
        
        # Test POST request (write) from admin user
        request = self.factory.post('/test/')
        request.user = self.admin_user
        request.method = 'POST'
        
        # Check that write access is granted to admin user
        self.assertTrue(permission.has_permission(request, None))
        
    def test_is_staff_or_readonly_permission(self):
        """
        Test that IsStaffOrReadOnly permission works correctly.
        
        Verifies that the IsStaffOrReadOnly permission allows read access
        to all users but write access only to staff users.
        """
        permission = IsStaffOrReadOnly()
        
        # Test GET request (read) from regular user
        request = self.factory.get('/test/')
        request.user = self.test_user
        request.method = 'GET'
        
        # Check that read access is granted to regular user
        self.assertTrue(permission.has_permission(request, None))
        
        # Test POST request (write) from regular user
        request = self.factory.post('/test/')
        request.user = self.test_user
        request.method = 'POST'
        
        # Check that write access is denied to regular user
        self.assertFalse(permission.has_permission(request, None))
        
        # Test POST request (write) from staff user
        request = self.factory.post('/test/')
        request.user = self.staff_user
        request.method = 'POST'
        
        # Check that write access is granted to staff user
        self.assertTrue(permission.has_permission(request, None))
        
    def test_is_premium_user_permission(self):
        """
        Test that IsPremiumUser permission works correctly.
        
        Verifies that the IsPremiumUser permission allows access
        only to premium users.
        """
        permission = IsPremiumUser()
        
        # Test request from regular user
        request = self.factory.get('/test/')
        request.user = self.test_user
        
        # Check that access is denied to regular user
        self.assertFalse(permission.has_permission(request, None))
        
        # Test request from premium user
        request = self.factory.get('/test/')
        request.user = self.premium_user
        
        # Check that access is granted to premium user
        self.assertTrue(permission.has_permission(request, None))
        
        # Test request from staff user (who is not premium)
        request = self.factory.get('/test/')
        request.user = self.staff_user
        
        # Check that access is denied to staff user who is not premium
        self.assertFalse(permission.has_permission(request, None))
        
        # Test request from admin user (who is not premium but is admin)
        request = self.factory.get('/test/')
        request.user = self.admin_user
        
        # Check that access is granted to admin user regardless of premium status
        self.assertTrue(permission.has_permission(request, None))


class PermissionIntegrationTests(TravelGuideBaseTestCase):
    """
    Integration tests for permissions in the TravelGuide application.
    
    These tests verify that permissions work correctly in real-world scenarios,
    combining multiple permission checks and middleware components.
    """
    
    def setUp(self):
        """
        Set up test data for permission integration tests.
        
        Extends the base setUp method to include additional users, resources,
        and clients.
        """
        super().setUp()
        
        # Create additional users with different roles
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='password',
            is_staff=True
        )
        
        self.premium_user = User.objects.create_user(
            username='premiumuser',
            email='premium@example.com',
            password='password'
        )
        
        # Set premium status for premium user
        profile = Profile.objects.get(user=self.premium_user)
        profile.is_premium = True
        profile.save()
        
        self.another_user = User.objects.create_user(
            username='anotheruser',
            email='another@example.com',
            password='password'
        )
        
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
        
        self.test_itinerary = Itinerary.objects.create(
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
        
        # Create clients
        self.client = Client()
        self.api_client = APIClient()
        
        # URLs for testing
        self.premium_content_url = reverse('core:premium_content')
        self.staff_dashboard_url = reverse('core:staff_dashboard')
        self.itinerary_detail_url = reverse('itineraries:itinerary_detail', kwargs={'pk': self.test_itinerary.pk})
        self.another_itinerary_detail_url = reverse('itineraries:itinerary_detail', kwargs={'pk': self.another_user_itinerary.pk})
        self.public_itinerary_detail_url = reverse('itineraries:itinerary_detail', kwargs={'pk': self.public_itinerary.pk})
        
    def test_premium_content_access(self):
        """
        Test access to premium content.
        
        Verifies that only premium users and admins can access premium content.
        """
        # Test access by anonymous user
        response = self.client.get(self.premium_content_url)
        
        # Check that the user is redirected to the login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        
        # Test access by regular user
        self.client.login(username='testuser', password='password')
        response = self.client.get(self.premium_content_url)
        
        # Check that access is denied
        self.assertEqual(response.status_code, 403)
        self.assertIn("Premium access required", response.content.decode())
        
        # Test access by premium user
        self.client.login(username='premiumuser', password='password')
        response = self.client.get(self.premium_content_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertIn("Premium Content", response.content.decode())
        
        # Test access by admin user
        self.client.login(username='admin', password='password')
        response = self.client.get(self.premium_content_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertIn("Premium Content", response.content.decode())
        
    def test_staff_dashboard_access(self):
        """
        Test access to staff dashboard.
        
        Verifies that only staff users can access the staff dashboard.
        """
        # Test access by anonymous user
        response = self.client.get(self.staff_dashboard_url)
        
        # Check that the user is redirected to the login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        
        # Test access by regular user
        self.client.login(username='testuser', password='password')
        response = self.client.get(self.staff_dashboard_url)
        
        # Check that access is denied
        self.assertEqual(response.status_code, 403)
        self.assertIn("Staff access required", response.content.decode())
        
        # Test access by staff user
        self.client.login(username='staffuser', password='password')
        response = self.client.get(self.staff_dashboard_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertIn("Staff Dashboard", response.content.decode())
        
    def test_itinerary_access_permissions(self):
        """
        Test access to itineraries with different permission levels.
        
        Verifies that access to itineraries is properly controlled based
        on ownership and public status.
        """
        # Test access to private itinerary by owner
        self.client.login(username='testuser', password='password')
        response = self.client.get(self.itinerary_detail_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertIn("Test User's Itinerary", response.content.decode())
        
        # Test access to private itinerary by another user
        self.client.login(username='anotheruser', password='password')
        response = self.client.get(self.itinerary_detail_url)
        
        # Check that access is denied
        self.assertEqual(response.status_code, 403)
        self.assertIn("You do not have permission", response.content.decode())
        
        # Test access to public itinerary by any user
        response = self.client.get(self.public_itinerary_detail_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertIn("Public Itinerary", response.content.decode())
        
        # Test access to private itinerary by admin user
        self.client.login(username='admin', password='password')
        response = self.client.get(self.itinerary_detail_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertIn("Test User's Itinerary", response.content.decode())
        
    def test_maintenance_mode_access(self):
        """
        Test access during maintenance mode.
        
        Verifies that access is properly controlled during maintenance mode,
        with only admin users and exempt views being accessible.
        """
        # Enable maintenance mode
        from django.conf import settings
        original_setting = getattr(settings, 'MAINTENANCE_MODE', False)
        settings.MAINTENANCE_MODE = True
        
        try:
            # Test access by anonymous user
            response = self.client.get(reverse('core:home'))
            
            # Check that maintenance page is shown
            self.assertEqual(response.status_code, 503)
            self.assertIn("Maintenance", response.content.decode())
            
            # Test access by regular user
            self.client.login(username='testuser', password='password')
            response = self.client.get(reverse('core:home'))
            
            # Check that maintenance page is shown
            self.assertEqual(response.status_code, 503)
            self.assertIn("Maintenance", response.content.decode())
            
            # Test access by admin user
            self.client.login(username='admin', password='password')
            response = self.client.get(reverse('core:home'))
            
            # Check that access is granted to admin user
            self.assertEqual(response.status_code, 200)
            self.assertIn("Home", response.content.decode())
            
            # Test access to exempt view
            response = self.client.get(reverse('core:maintenance'))
            
            # Check that access is granted to exempt view
            self.assertEqual(response.status_code, 200)
            self.assertIn("Maintenance", response.content.decode())
            
        finally:
            # Restore original setting
            settings.MAINTENANCE_MODE = original_setting
