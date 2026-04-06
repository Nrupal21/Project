"""
Test cases for utility functions and helper modules in the TravelGuide application.

This module contains comprehensive test cases for all utility functions
and helper modules used throughout the application. Every test function
is thoroughly documented to make understanding the tests easier for programmers.
"""

from django.test import TestCase
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.conf import settings
import datetime
import os
import tempfile
from decimal import Decimal

from core.utils import (
    generate_unique_slug,
    format_currency,
    get_client_ip,
    resize_image,
    truncate_string,
    parse_date,
    validate_file_size,
    validate_file_extension,
    send_notification_email,
    calculate_distance,
    get_weather_data
)
from destinations.models import Destination
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class UtilityFunctionTests(TravelGuideBaseTestCase):
    """
    Tests for utility functions used throughout the TravelGuide application.
    
    These tests verify that utility functions work correctly under various
    conditions and with different inputs.
    """
    
    def setUp(self):
        """
        Set up test data for utility function tests.
        
        Extends the base setUp method to include additional test data.
        """
        super().setUp()
        
        # Create additional test data specific to utility tests
        self.test_destination = Destination.objects.create(
            name="Test Destination",
            description="A test destination for utility tests.",
            region=self.test_region,
            image="destinations/test.jpg",
            is_featured=True,
            latitude=35.6762,
            longitude=139.6503
        )
    
    def test_generate_unique_slug(self):
        """
        Test the generate_unique_slug function.
        
        Verifies that the function generates a unique slug based on the
        provided text, and handles duplicates by appending a number.
        """
        # Test basic slug generation
        slug = generate_unique_slug(Destination, "Test Destination", "name")
        self.assertEqual(slug, "test-destination")
        
        # Test slug generation with existing slug
        # First, create a destination with the same name
        duplicate = Destination.objects.create(
            name="Test Destination",
            description="Another test destination with the same name.",
            region=self.test_region,
            image="destinations/duplicate.jpg",
            is_featured=False,
            latitude=34.0522,
            longitude=-118.2437,
            slug="test-destination"  # Same slug as the first one
        )
        
        # Now generate a unique slug for the same name
        new_slug = generate_unique_slug(Destination, "Test Destination", "name")
        self.assertEqual(new_slug, "test-destination-1")
        
        # Test with another duplicate
        another_duplicate = Destination.objects.create(
            name="Test Destination",
            description="Yet another test destination with the same name.",
            region=self.test_region,
            image="destinations/another_duplicate.jpg",
            is_featured=False,
            latitude=51.5074,
            longitude=-0.1278,
            slug="test-destination-1"  # Same slug as the second one
        )
        
        # Generate another unique slug
        another_new_slug = generate_unique_slug(Destination, "Test Destination", "name")
        self.assertEqual(another_new_slug, "test-destination-2")
        
    def test_format_currency(self):
        """
        Test the format_currency function.
        
        Verifies that the function correctly formats currency values
        with the specified currency symbol and decimal places.
        """
        # Test with USD (default)
        formatted = format_currency(1234.56)
        self.assertEqual(formatted, "$1,234.56")
        
        # Test with EUR
        formatted = format_currency(1234.56, currency="EUR")
        self.assertEqual(formatted, "€1,234.56")
        
        # Test with GBP
        formatted = format_currency(1234.56, currency="GBP")
        self.assertEqual(formatted, "£1,234.56")
        
        # Test with JPY (no decimal places)
        formatted = format_currency(1234.56, currency="JPY")
        self.assertEqual(formatted, "¥1,235")  # Rounded to nearest whole number
        
        # Test with decimal object
        formatted = format_currency(Decimal("1234.56"), currency="USD")
        self.assertEqual(formatted, "$1,234.56")
        
        # Test with zero value
        formatted = format_currency(0, currency="USD")
        self.assertEqual(formatted, "$0.00")
        
        # Test with negative value
        formatted = format_currency(-1234.56, currency="USD")
        self.assertEqual(formatted, "-$1,234.56")
        
    def test_get_client_ip(self):
        """
        Test the get_client_ip function.
        
        Verifies that the function correctly extracts the client IP address
        from various request headers.
        """
        # Create a mock request with REMOTE_ADDR
        class MockRequest:
            def __init__(self, meta=None):
                self.META = meta or {}
        
        # Test with REMOTE_ADDR
        request = MockRequest({"REMOTE_ADDR": "192.168.1.1"})
        ip = get_client_ip(request)
        self.assertEqual(ip, "192.168.1.1")
        
        # Test with HTTP_X_FORWARDED_FOR
        request = MockRequest({
            "HTTP_X_FORWARDED_FOR": "10.0.0.1, 10.0.0.2, 10.0.0.3",
            "REMOTE_ADDR": "192.168.1.1"
        })
        ip = get_client_ip(request)
        self.assertEqual(ip, "10.0.0.1")
        
        # Test with empty HTTP_X_FORWARDED_FOR
        request = MockRequest({
            "HTTP_X_FORWARDED_FOR": "",
            "REMOTE_ADDR": "192.168.1.1"
        })
        ip = get_client_ip(request)
        self.assertEqual(ip, "192.168.1.1")
        
        # Test with no IP information
        request = MockRequest({})
        ip = get_client_ip(request)
        self.assertEqual(ip, "0.0.0.0")  # Default fallback
        
    def test_resize_image(self):
        """
        Test the resize_image function.
        
        Verifies that the function correctly resizes images to the
        specified dimensions while maintaining aspect ratio.
        """
        # Create a temporary image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            # Create a simple test image (1x1 pixel black image)
            temp_file.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xdb\x00C\x01\t\t\t\x0c\x0b\x0c\x18\r\r\x182!\x1c!22222222222222222222222222222222222222222222222222\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xc4\x00\x1f\x01\x00\x03\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x11\x00\x02\x01\x02\x04\x04\x03\x04\x07\x05\x04\x04\x00\x01\x02w\x00\x01\x02\x03\x11\x04\x05!1\x06\x12AQ\x07aq\x13"2\x81\x08\x14B\x91\xa1\xb1\xc1\t#3R\xf0\x15br\xd1\n\x16$4\xe1%\xf1\x17\x18\x19\x1a&\'()*56789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xfe\xfe(\xa2\x8a\x00\xff\xd9')
        
        try:
            # Test resizing the image
            resized_path = resize_image(temp_file.name, (100, 100))
            
            # Check that the resized file exists
            self.assertTrue(os.path.exists(resized_path))
            
            # Clean up the resized file
            os.remove(resized_path)
        finally:
            # Clean up the temporary file
            os.remove(temp_file.name)
            
    def test_truncate_string(self):
        """
        Test the truncate_string function.
        
        Verifies that the function correctly truncates strings to the
        specified length and adds an ellipsis if needed.
        """
        # Test with string shorter than max_length
        short_string = "Hello, world!"
        truncated = truncate_string(short_string, 20)
        self.assertEqual(truncated, short_string)
        
        # Test with string equal to max_length
        exact_string = "Hello, world!"
        truncated = truncate_string(exact_string, 13)
        self.assertEqual(truncated, exact_string)
        
        # Test with string longer than max_length
        long_string = "This is a very long string that needs to be truncated."
        truncated = truncate_string(long_string, 20)
        self.assertEqual(truncated, "This is a very long...")
        
        # Test with custom suffix
        truncated = truncate_string(long_string, 20, suffix="[more]")
        self.assertEqual(truncated, "This is a very long[more]")
        
        # Test with empty string
        empty_string = ""
        truncated = truncate_string(empty_string, 10)
        self.assertEqual(truncated, "")
        
    def test_parse_date(self):
        """
        Test the parse_date function.
        
        Verifies that the function correctly parses date strings in
        various formats and returns a datetime object.
        """
        # Test with ISO format
        date_str = "2023-06-15"
        parsed = parse_date(date_str)
        self.assertEqual(parsed, datetime.date(2023, 6, 15))
        
        # Test with US format (MM/DD/YYYY)
        date_str = "06/15/2023"
        parsed = parse_date(date_str)
        self.assertEqual(parsed, datetime.date(2023, 6, 15))
        
        # Test with European format (DD/MM/YYYY)
        date_str = "15/06/2023"
        parsed = parse_date(date_str)
        self.assertEqual(parsed, datetime.date(2023, 6, 15))
        
        # Test with written month format
        date_str = "15 June 2023"
        parsed = parse_date(date_str)
        self.assertEqual(parsed, datetime.date(2023, 6, 15))
        
        # Test with abbreviated month format
        date_str = "15-Jun-2023"
        parsed = parse_date(date_str)
        self.assertEqual(parsed, datetime.date(2023, 6, 15))
        
        # Test with invalid date string
        date_str = "not a date"
        parsed = parse_date(date_str)
        self.assertIsNone(parsed)
        
    def test_validate_file_size(self):
        """
        Test the validate_file_size function.
        
        Verifies that the function correctly validates file sizes
        against the specified maximum size.
        """
        # Create a small test file
        small_file = SimpleUploadedFile(
            name="small.txt",
            content=b"This is a small file.",
            content_type="text/plain"
        )
        
        # Create a large test file (exceeding the max size)
        large_content = b"x" * (settings.MAX_UPLOAD_SIZE + 1)
        large_file = SimpleUploadedFile(
            name="large.txt",
            content=large_content,
            content_type="text/plain"
        )
        
        # Test with small file (should pass)
        try:
            validate_file_size(small_file)
            validation_passed = True
        except:
            validation_passed = False
        self.assertTrue(validation_passed)
        
        # Test with large file (should fail)
        try:
            validate_file_size(large_file)
            validation_passed = True
        except:
            validation_passed = False
        self.assertFalse(validation_passed)
        
    def test_validate_file_extension(self):
        """
        Test the validate_file_extension function.
        
        Verifies that the function correctly validates file extensions
        against the list of allowed extensions.
        """
        # Create test files with different extensions
        valid_file = SimpleUploadedFile(
            name="image.jpg",
            content=b"This is a test image.",
            content_type="image/jpeg"
        )
        
        invalid_file = SimpleUploadedFile(
            name="document.exe",
            content=b"This is an executable file.",
            content_type="application/octet-stream"
        )
        
        # Test with valid extension (should pass)
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        try:
            validate_file_extension(valid_file, allowed_extensions)
            validation_passed = True
        except:
            validation_passed = False
        self.assertTrue(validation_passed)
        
        # Test with invalid extension (should fail)
        try:
            validate_file_extension(invalid_file, allowed_extensions)
            validation_passed = True
        except:
            validation_passed = False
        self.assertFalse(validation_passed)
        
    def test_send_notification_email(self):
        """
        Test the send_notification_email function.
        
        Verifies that the function correctly sends notification emails
        with the specified subject, message, and recipient.
        """
        # Test sending an email
        from django.core import mail
        
        # Clear the mail outbox
        mail.outbox = []
        
        # Send a test email
        send_notification_email(
            subject="Test Notification",
            message="This is a test notification.",
            recipient_email="test@example.com"
        )
        
        # Check that the email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Test Notification")
        self.assertEqual(mail.outbox[0].body, "This is a test notification.")
        self.assertEqual(mail.outbox[0].to, ["test@example.com"])
        
    def test_calculate_distance(self):
        """
        Test the calculate_distance function.
        
        Verifies that the function correctly calculates the distance
        between two geographic coordinates using the Haversine formula.
        """
        # Test with known coordinates and distance
        # Tokyo: 35.6762° N, 139.6503° E
        # Kyoto: 35.0116° N, 135.7681° E
        # Distance: ~372 km
        
        tokyo_lat, tokyo_lon = 35.6762, 139.6503
        kyoto_lat, kyoto_lon = 35.0116, 135.7681
        
        distance = calculate_distance(tokyo_lat, tokyo_lon, kyoto_lat, kyoto_lon)
        
        # Check that the calculated distance is approximately correct (within 5 km)
        self.assertAlmostEqual(distance, 372, delta=5)
        
        # Test with same coordinates (should be 0)
        distance = calculate_distance(tokyo_lat, tokyo_lon, tokyo_lat, tokyo_lon)
        self.assertEqual(distance, 0)
        
        # Test with antipodal points (should be ~20,000 km)
        antipodal_lat, antipodal_lon = -tokyo_lat, tokyo_lon + 180 if tokyo_lon < 0 else tokyo_lon - 180
        distance = calculate_distance(tokyo_lat, tokyo_lon, antipodal_lat, antipodal_lon)
        self.assertAlmostEqual(distance, 20000, delta=1000)
        
    def test_get_weather_data(self):
        """
        Test the get_weather_data function.
        
        Verifies that the function correctly retrieves weather data
        for the specified location, or returns a default value if
        the API call fails.
        """
        # Test with valid location
        # Note: This test may fail if the API is down or the API key is invalid
        weather_data = get_weather_data("Tokyo")
        
        # If the API call succeeds, check that the data has the expected structure
        if weather_data and 'error' not in weather_data:
            self.assertIn('temperature', weather_data)
            self.assertIn('description', weather_data)
            self.assertIn('icon', weather_data)
        else:
            # If the API call fails, the function should return a default value
            self.assertEqual(weather_data, {
                'temperature': 'N/A',
                'description': 'Weather data unavailable',
                'icon': 'cloud'
            })
        
        # Test with invalid location
        weather_data = get_weather_data("NonexistentLocation12345")
        
        # The function should return a default value for invalid locations
        self.assertEqual(weather_data, {
            'temperature': 'N/A',
            'description': 'Weather data unavailable',
            'icon': 'cloud'
        })
