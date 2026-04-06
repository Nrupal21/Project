"""
Test cases for the middleware components of the TravelGuide application.

This module contains comprehensive test cases for all middleware components
used in the application. Every test function is thoroughly documented
to make understanding the tests easier for programmers.
"""

from django.test import TestCase, RequestFactory
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.urls import reverse
import time
import re

from core.middleware import (
    MaintenanceModeMiddleware,
    SecurityHeadersMiddleware,
    RequestTimingMiddleware,
    UserActivityMiddleware,
    MobileDetectionMiddleware
)
from core.models import SiteSettings
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class MiddlewareTestCase(TestCase):
    """
    Base test case for middleware tests.
    
    Provides common setup and utility methods for testing middleware components.
    """
    
    def setUp(self):
        """
        Set up test data for middleware tests.
        
        Creates a request factory and other common test data.
        """
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password'
        )
        
    def get_response_mock(self, request):
        """
        Mock get_response function for middleware testing.
        
        This simulates the view function that would normally be called
        by the middleware chain.
        
        Args:
            request: The request object being processed.
            
        Returns:
            HttpResponse: A simple HTTP response object.
        """
        return HttpResponse("Test response")
    
    def process_request(self, request, middleware):
        """
        Process a request through a middleware component.
        
        Args:
            request: The request object to process.
            middleware: The middleware instance to test.
            
        Returns:
            HttpResponse: The response after middleware processing.
        """
        # Add session to request
        session_middleware = SessionMiddleware(self.get_response_mock)
        session_middleware.process_request(request)
        request.session.save()
        
        # Add auth to request
        auth_middleware = AuthenticationMiddleware(self.get_response_mock)
        auth_middleware.process_request(request)
        
        # Process the request through the middleware being tested
        response = middleware(request)
        
        return response


class MaintenanceModeMiddlewareTests(MiddlewareTestCase):
    """
    Tests for the MaintenanceModeMiddleware.
    
    These tests verify that the maintenance mode middleware correctly
    redirects users to the maintenance page when maintenance mode is enabled.
    """
    
    def setUp(self):
        """
        Set up test data for maintenance mode middleware tests.
        
        Extends the base setUp method to include site settings with maintenance mode.
        """
        super().setUp()
        
        # Create site settings with maintenance mode disabled
        self.site_settings = SiteSettings.objects.create(
            site_name="TravelGuide",
            maintenance_mode=False,
            maintenance_message="Site is under maintenance"
        )
        
        # Create middleware instance
        self.middleware = MaintenanceModeMiddleware(self.get_response_mock)
        
    def test_maintenance_mode_disabled(self):
        """
        Test that requests are processed normally when maintenance mode is disabled.
        
        Verifies that the middleware allows requests to proceed to the view
        when maintenance mode is disabled.
        """
        request = self.factory.get('/')
        response = self.process_request(request, self.middleware)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Test response")
        
    def test_maintenance_mode_enabled(self):
        """
        Test that requests are redirected when maintenance mode is enabled.
        
        Verifies that the middleware redirects requests to the maintenance page
        when maintenance mode is enabled.
        """
        # Enable maintenance mode
        self.site_settings.maintenance_mode = True
        self.site_settings.save()
        
        request = self.factory.get('/')
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 503)  # Service Unavailable
        self.assertIn("Site is under maintenance", response.content.decode())
        
    def test_maintenance_mode_admin_access(self):
        """
        Test that admin users can access the site even when maintenance mode is enabled.
        
        Verifies that the middleware allows admin users to bypass the maintenance page.
        """
        # Enable maintenance mode
        self.site_settings.maintenance_mode = True
        self.site_settings.save()
        
        # Create admin user
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password'
        )
        
        # Create request with admin user
        request = self.factory.get('/')
        request.user = admin_user
        
        # Process request
        response = self.process_request(request, self.middleware)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Test response")
        
    def test_maintenance_mode_api_access(self):
        """
        Test that API requests receive a proper JSON response when maintenance mode is enabled.
        
        Verifies that the middleware returns a JSON response for API requests
        when maintenance mode is enabled.
        """
        # Enable maintenance mode
        self.site_settings.maintenance_mode = True
        self.site_settings.save()
        
        # Create API request
        request = self.factory.get('/api/destinations/')
        request.path_info = '/api/destinations/'  # Explicitly set path_info
        
        # Process request
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 503)  # Service Unavailable
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertIn('"status": "error"', response.content.decode())
        self.assertIn('"message": "Site is under maintenance"', response.content.decode())


class SecurityHeadersMiddlewareTests(MiddlewareTestCase):
    """
    Tests for the SecurityHeadersMiddleware.
    
    These tests verify that the security headers middleware correctly
    adds security headers to responses.
    """
    
    def setUp(self):
        """
        Set up test data for security headers middleware tests.
        
        Creates a middleware instance for testing.
        """
        super().setUp()
        
        # Create middleware instance
        self.middleware = SecurityHeadersMiddleware(self.get_response_mock)
        
    def test_security_headers_added(self):
        """
        Test that security headers are added to responses.
        
        Verifies that the middleware adds the expected security headers
        to HTTP responses.
        """
        request = self.factory.get('/')
        response = self.process_request(request, self.middleware)
        
        # Check that security headers are present
        self.assertIn('X-Content-Type-Options', response)
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        
        self.assertIn('X-Frame-Options', response)
        self.assertEqual(response['X-Frame-Options'], 'DENY')
        
        self.assertIn('X-XSS-Protection', response)
        self.assertEqual(response['X-XSS-Protection'], '1; mode=block')
        
        self.assertIn('Strict-Transport-Security', response)
        self.assertEqual(response['Strict-Transport-Security'], 'max-age=31536000; includeSubDomains')
        
        self.assertIn('Content-Security-Policy', response)
        # CSP header should include default-src directive
        self.assertIn("default-src 'self'", response['Content-Security-Policy'])
        
    def test_security_headers_not_added_to_static_files(self):
        """
        Test that security headers are not added to static file responses.
        
        Verifies that the middleware does not add security headers to
        responses for static files.
        """
        # Create request for a static file
        request = self.factory.get('/static/css/style.css')
        request.path_info = '/static/css/style.css'  # Explicitly set path_info
        
        # Create a response without calling process_request
        response = self.middleware(request)
        
        # Check that security headers are not present
        self.assertNotIn('Content-Security-Policy', response)
        
    def test_security_headers_not_added_to_media_files(self):
        """
        Test that security headers are not added to media file responses.
        
        Verifies that the middleware does not add security headers to
        responses for media files.
        """
        # Create request for a media file
        request = self.factory.get('/media/images/photo.jpg')
        request.path_info = '/media/images/photo.jpg'  # Explicitly set path_info
        
        # Create a response without calling process_request
        response = self.middleware(request)
        
        # Check that security headers are not present
        self.assertNotIn('Content-Security-Policy', response)


class RequestTimingMiddlewareTests(MiddlewareTestCase):
    """
    Tests for the RequestTimingMiddleware.
    
    These tests verify that the request timing middleware correctly
    measures and logs request processing time.
    """
    
    def setUp(self):
        """
        Set up test data for request timing middleware tests.
        
        Creates a middleware instance for testing.
        """
        super().setUp()
        
        # Create middleware instance
        self.middleware = RequestTimingMiddleware(self.get_response_mock)
        
    def test_request_timing_header_added(self):
        """
        Test that the request timing header is added to responses.
        
        Verifies that the middleware adds a header with the request
        processing time to HTTP responses.
        """
        request = self.factory.get('/')
        response = self.process_request(request, self.middleware)
        
        # Check that timing header is present
        self.assertIn('X-Request-Time', response)
        
        # Check that the timing value is a float
        timing_value = float(response['X-Request-Time'].replace('ms', ''))
        self.assertIsInstance(timing_value, float)
        
    def test_request_timing_slow_request_logging(self):
        """
        Test that slow requests are logged.
        
        Verifies that the middleware logs requests that take longer
        than the threshold to process.
        """
        # Create a slow get_response function
        def slow_get_response(request):
            time.sleep(0.1)  # Sleep for 100ms
            return HttpResponse("Slow response")
        
        # Create middleware with slow get_response
        middleware = RequestTimingMiddleware(slow_get_response)
        
        # Set a low threshold for testing
        middleware.SLOW_REQUEST_THRESHOLD = 0.05  # 50ms
        
        # Process request with middleware
        request = self.factory.get('/')
        response = middleware(request)
        
        # Check that timing header is present and value is greater than threshold
        self.assertIn('X-Request-Time', response)
        timing_value = float(response['X-Request-Time'].replace('ms', ''))
        self.assertGreater(timing_value, middleware.SLOW_REQUEST_THRESHOLD * 1000)


class UserActivityMiddlewareTests(TravelGuideBaseTestCase):
    """
    Tests for the UserActivityMiddleware.
    
    These tests verify that the user activity middleware correctly
    updates the last_activity timestamp for authenticated users.
    """
    
    def setUp(self):
        """
        Set up test data for user activity middleware tests.
        
        Extends the base setUp method to include a middleware instance.
        """
        super().setUp()
        
        # Create middleware instance
        self.middleware = UserActivityMiddleware(self.get_response_mock)
        self.factory = RequestFactory()
        
    def get_response_mock(self, request):
        """
        Mock get_response function for middleware testing.
        
        Args:
            request: The request object being processed.
            
        Returns:
            HttpResponse: A simple HTTP response object.
        """
        return HttpResponse("Test response")
    
    def test_user_activity_updated_for_authenticated_user(self):
        """
        Test that the last_activity timestamp is updated for authenticated users.
        
        Verifies that the middleware updates the last_activity field
        of the user's profile when they make a request.
        """
        # Record the initial last_activity timestamp
        initial_last_activity = self.test_user.profile.last_activity
        
        # Create request with authenticated user
        request = self.factory.get('/')
        request.user = self.test_user
        
        # Add session to request
        session_middleware = SessionMiddleware(self.get_response_mock)
        session_middleware.process_request(request)
        request.session.save()
        
        # Process request with middleware
        response = self.middleware(request)
        
        # Refresh the user from the database
        self.test_user.profile.refresh_from_db()
        
        # Check that last_activity was updated
        self.assertGreater(self.test_user.profile.last_activity, initial_last_activity)
        
    def test_user_activity_not_updated_for_anonymous_user(self):
        """
        Test that the middleware does nothing for anonymous users.
        
        Verifies that the middleware does not attempt to update
        the last_activity field for anonymous users.
        """
        # Create request with anonymous user
        request = self.factory.get('/')
        request.user = None
        
        # Process request with middleware
        response = self.middleware(request)
        
        # Check that the response is as expected
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Test response")
        
    def test_user_activity_not_updated_for_ajax_requests(self):
        """
        Test that the last_activity timestamp is not updated for AJAX requests.
        
        Verifies that the middleware does not update the last_activity field
        for AJAX requests to avoid unnecessary database updates.
        """
        # Record the initial last_activity timestamp
        initial_last_activity = self.test_user.profile.last_activity
        
        # Create AJAX request with authenticated user
        request = self.factory.get('/')
        request.user = self.test_user
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'  # Mark as AJAX
        
        # Add session to request
        session_middleware = SessionMiddleware(self.get_response_mock)
        session_middleware.process_request(request)
        request.session.save()
        
        # Process request with middleware
        response = self.middleware(request)
        
        # Refresh the user from the database
        self.test_user.profile.refresh_from_db()
        
        # Check that last_activity was not updated
        self.assertEqual(self.test_user.profile.last_activity, initial_last_activity)


class MobileDetectionMiddlewareTests(MiddlewareTestCase):
    """
    Tests for the MobileDetectionMiddleware.
    
    These tests verify that the mobile detection middleware correctly
    detects mobile devices and adds a flag to the request.
    """
    
    def setUp(self):
        """
        Set up test data for mobile detection middleware tests.
        
        Creates a middleware instance for testing.
        """
        super().setUp()
        
        # Create middleware instance
        self.middleware = MobileDetectionMiddleware(self.get_response_mock)
        
    def test_mobile_detection_desktop_user_agent(self):
        """
        Test that desktop user agents are correctly identified.
        
        Verifies that the middleware correctly identifies desktop
        user agents and sets is_mobile to False.
        """
        # Create request with desktop user agent
        request = self.factory.get('/')
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        
        # Process request with middleware
        response = self.middleware(request)
        
        # Check that is_mobile is False
        self.assertFalse(request.is_mobile)
        
    def test_mobile_detection_mobile_user_agent(self):
        """
        Test that mobile user agents are correctly identified.
        
        Verifies that the middleware correctly identifies mobile
        user agents and sets is_mobile to True.
        """
        # Create request with mobile user agent
        request = self.factory.get('/')
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        
        # Process request with middleware
        response = self.middleware(request)
        
        # Check that is_mobile is True
        self.assertTrue(request.is_mobile)
        
    def test_mobile_detection_tablet_user_agent(self):
        """
        Test that tablet user agents are correctly identified.
        
        Verifies that the middleware correctly identifies tablet
        user agents and sets is_mobile and is_tablet appropriately.
        """
        # Create request with tablet user agent
        request = self.factory.get('/')
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        
        # Process request with middleware
        response = self.middleware(request)
        
        # Check that is_mobile is True and is_tablet is True
        self.assertTrue(request.is_mobile)
        self.assertTrue(request.is_tablet)
        
    def test_mobile_detection_no_user_agent(self):
        """
        Test behavior when no user agent is provided.
        
        Verifies that the middleware handles requests without a user agent
        header and defaults to desktop (is_mobile=False).
        """
        # Create request without user agent
        request = self.factory.get('/')
        
        # Process request with middleware
        response = self.middleware(request)
        
        # Check that is_mobile is False
        self.assertFalse(request.is_mobile)
        
    def test_template_context_processor(self):
        """
        Test that the mobile detection context processor adds variables to the template context.
        
        Verifies that the middleware's context processor adds is_mobile and is_tablet
        variables to the template context.
        """
        # Create request with mobile user agent
        request = self.factory.get('/')
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        
        # Process request with middleware
        response = self.middleware(request)
        
        # Get context from context processor
        context = self.middleware.context_processor(request)
        
        # Check that context contains is_mobile and is_tablet
        self.assertIn('is_mobile', context)
        self.assertIn('is_tablet', context)
        self.assertTrue(context['is_mobile'])
        self.assertFalse(context['is_tablet'])
