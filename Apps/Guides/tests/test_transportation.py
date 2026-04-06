"""
Test cases for the transportation app.

This module contains comprehensive test cases for all functionality
in the transportation app, including models, views, and transportation booking features.
Every test function is thoroughly documented to make understanding
the tests easier for programmers.
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
import datetime

from transportation.models import TransportationType, TransportationProvider, TransportationOption, TransportationBooking
from destinations.models import Destination
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class TransportationTypeModelTests(TravelGuideBaseTestCase):
    """
    Tests for the TransportationType model in the transportation app.
    
    These tests verify that TransportationType objects can be created correctly,
    and that their methods work as expected. Each test focuses on a 
    specific aspect of the TransportationType model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for TransportationType tests.
        
        Extends the base setUp method to include transportation types for testing.
        """
        super().setUp()
        
        # Create transportation types
        self.air_type = TransportationType.objects.create(
            name="Air",
            icon="airplane",
            description="Air transportation including flights and helicopters"
        )
        
        self.rail_type = TransportationType.objects.create(
            name="Rail",
            icon="train",
            description="Rail transportation including trains and subways"
        )
    
    def test_transportation_type_creation(self):
        """
        Test that a TransportationType can be created with the expected attributes.
        
        Verifies that the TransportationType model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new transportation type
        transport_type = TransportationType.objects.create(
            name="Road",
            icon="car",
            description="Road transportation including buses, taxis, and car rentals"
        )
        
        # Verify the transportation type was created with the correct attributes
        self.assertEqual(transport_type.name, "Road")
        self.assertEqual(transport_type.icon, "car")
        self.assertEqual(transport_type.description, "Road transportation including buses, taxis, and car rentals")
        
    def test_transportation_type_str_method(self):
        """
        Test the string representation of a TransportationType object.
        
        Verifies that the __str__ method returns the expected string,
        which should be the transportation type name.
        """
        self.assertEqual(str(self.air_type), "Air")
        self.assertEqual(str(self.rail_type), "Rail")


class TransportationProviderModelTests(TravelGuideBaseTestCase):
    """
    Tests for the TransportationProvider model in the transportation app.
    
    These tests verify that TransportationProvider objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the TransportationProvider model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for TransportationProvider tests.
        
        Extends the base setUp method to include transportation types and providers for testing.
        """
        super().setUp()
        
        # Create transportation types
        self.air_type = TransportationType.objects.create(
            name="Air",
            icon="airplane",
            description="Air transportation including flights and helicopters"
        )
        
        self.rail_type = TransportationType.objects.create(
            name="Rail",
            icon="train",
            description="Rail transportation including trains and subways"
        )
        
        # Create transportation providers
        self.airline_provider = TransportationProvider.objects.create(
            name="Global Airways",
            transportation_type=self.air_type,
            website="https://globalairways.example.com",
            contact_phone="+1-800-123-4567",
            contact_email="info@globalairways.example.com",
            logo="providers/global_airways_logo.png"
        )
        
        self.rail_provider = TransportationProvider.objects.create(
            name="Express Rail",
            transportation_type=self.rail_type,
            website="https://expressrail.example.com",
            contact_phone="+1-800-765-4321",
            contact_email="info@expressrail.example.com",
            logo="providers/express_rail_logo.png"
        )
    
    def test_transportation_provider_creation(self):
        """
        Test that a TransportationProvider can be created with the expected attributes.
        
        Verifies that the TransportationProvider model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new transportation type
        road_type = TransportationType.objects.create(
            name="Road",
            icon="car",
            description="Road transportation including buses, taxis, and car rentals"
        )
        
        # Create a new transportation provider
        bus_provider = TransportationProvider.objects.create(
            name="City Bus Lines",
            transportation_type=road_type,
            website="https://citybuslines.example.com",
            contact_phone="+1-800-555-1234",
            contact_email="info@citybuslines.example.com",
            logo="providers/city_bus_lines_logo.png"
        )
        
        # Verify the transportation provider was created with the correct attributes
        self.assertEqual(bus_provider.name, "City Bus Lines")
        self.assertEqual(bus_provider.transportation_type, road_type)
        self.assertEqual(bus_provider.website, "https://citybuslines.example.com")
        self.assertEqual(bus_provider.contact_phone, "+1-800-555-1234")
        self.assertEqual(bus_provider.contact_email, "info@citybuslines.example.com")
        self.assertEqual(bus_provider.logo, "providers/city_bus_lines_logo.png")
        
    def test_transportation_provider_str_method(self):
        """
        Test the string representation of a TransportationProvider object.
        
        Verifies that the __str__ method returns the expected string,
        which should be the provider name.
        """
        self.assertEqual(str(self.airline_provider), "Global Airways")
        self.assertEqual(str(self.rail_provider), "Express Rail")
        
    def test_transportation_provider_get_absolute_url(self):
        """
        Test the get_absolute_url method of the TransportationProvider model.
        
        Verifies that the URL generated for a provider detail page is correct
        and matches the expected URL pattern.
        """
        expected_url = reverse('transportation:provider_detail', kwargs={'pk': self.airline_provider.pk})
        self.assertEqual(self.airline_provider.get_absolute_url(), expected_url)


class TransportationOptionModelTests(TravelGuideBaseTestCase):
    """
    Tests for the TransportationOption model in the transportation app.
    
    These tests verify that TransportationOption objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the TransportationOption model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for TransportationOption tests.
        
        Extends the base setUp method to include transportation types, providers,
        and options for testing.
        """
        super().setUp()
        
        # Create transportation types
        self.air_type = TransportationType.objects.create(
            name="Air",
            icon="airplane",
            description="Air transportation including flights and helicopters"
        )
        
        # Create transportation providers
        self.airline_provider = TransportationProvider.objects.create(
            name="Global Airways",
            transportation_type=self.air_type,
            website="https://globalairways.example.com",
            contact_phone="+1-800-123-4567",
            contact_email="info@globalairways.example.com",
            logo="providers/global_airways_logo.png"
        )
        
        # Create origin and destination
        self.origin = self.create_destination("New York", self.test_region)
        self.destination = self.test_destination  # Use the destination from base setup
        
        # Create transportation options
        self.flight_option = TransportationOption.objects.create(
            provider=self.airline_provider,
            origin=self.origin,
            destination=self.destination,
            departure_time=timezone.now() + datetime.timedelta(days=30, hours=10),
            arrival_time=timezone.now() + datetime.timedelta(days=30, hours=22),
            price=Decimal('499.99'),
            currency='USD',
            reference_code='GA123',
            available_seats=50,
            class_type='economy',
            features='Wi-Fi, Meals, Entertainment',
            is_direct=True
        )
    
    def test_transportation_option_creation(self):
        """
        Test that a TransportationOption can be created with the expected attributes.
        
        Verifies that the TransportationOption model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new transportation option
        flight_option = TransportationOption.objects.create(
            provider=self.airline_provider,
            origin=self.origin,
            destination=self.destination,
            departure_time=timezone.now() + datetime.timedelta(days=31, hours=8),
            arrival_time=timezone.now() + datetime.timedelta(days=31, hours=20),
            price=Decimal('599.99'),
            currency='USD',
            reference_code='GA456',
            available_seats=30,
            class_type='business',
            features='Wi-Fi, Premium Meals, Entertainment, Lounge Access',
            is_direct=False
        )
        
        # Verify the transportation option was created with the correct attributes
        self.assertEqual(flight_option.provider, self.airline_provider)
        self.assertEqual(flight_option.origin, self.origin)
        self.assertEqual(flight_option.destination, self.destination)
        self.assertEqual(flight_option.price, Decimal('599.99'))
        self.assertEqual(flight_option.currency, 'USD')
        self.assertEqual(flight_option.reference_code, 'GA456')
        self.assertEqual(flight_option.available_seats, 30)
        self.assertEqual(flight_option.class_type, 'business')
        self.assertEqual(flight_option.features, 'Wi-Fi, Premium Meals, Entertainment, Lounge Access')
        self.assertFalse(flight_option.is_direct)
        
    def test_transportation_option_str_method(self):
        """
        Test the string representation of a TransportationOption object.
        
        Verifies that the __str__ method returns the expected string,
        which should include the origin, destination, and reference code.
        """
        expected_str = f"{self.origin.name} to {self.destination.name} (GA123)"
        self.assertEqual(str(self.flight_option), expected_str)
        
    def test_transportation_option_get_absolute_url(self):
        """
        Test the get_absolute_url method of the TransportationOption model.
        
        Verifies that the URL generated for an option detail page is correct
        and matches the expected URL pattern.
        """
        expected_url = reverse('transportation:option_detail', kwargs={'pk': self.flight_option.pk})
        self.assertEqual(self.flight_option.get_absolute_url(), expected_url)
        
    def test_transportation_option_duration(self):
        """
        Test the duration property of the TransportationOption model.
        
        Verifies that the duration property correctly calculates
        the time difference between departure and arrival.
        """
        # Calculate the expected duration in hours
        expected_duration = 12.0  # 22 - 10 = 12 hours
        
        # Get the actual duration
        actual_duration = self.flight_option.duration
        
        # Verify the duration is correct
        self.assertEqual(actual_duration, expected_duration)
        
    def test_transportation_option_formatted_price(self):
        """
        Test the formatted_price property of the TransportationOption model.
        
        Verifies that the formatted_price property correctly formats
        the price with the currency symbol.
        """
        expected_formatted_price = "$499.99"
        self.assertEqual(self.flight_option.formatted_price, expected_formatted_price)
        
    def test_transportation_option_is_available(self):
        """
        Test the is_available property of the TransportationOption model.
        
        Verifies that the is_available property correctly determines
        if the option is available based on available seats and departure time.
        """
        # Initially the option should be available
        self.assertTrue(self.flight_option.is_available)
        
        # Set available seats to 0
        self.flight_option.available_seats = 0
        self.flight_option.save()
        
        # Now the option should not be available
        self.assertFalse(self.flight_option.is_available)
        
        # Reset available seats
        self.flight_option.available_seats = 50
        
        # Set departure time to the past
        self.flight_option.departure_time = timezone.now() - datetime.timedelta(days=1)
        self.flight_option.save()
        
        # Now the option should not be available
        self.assertFalse(self.flight_option.is_available)


class TransportationBookingModelTests(TravelGuideBaseTestCase):
    """
    Tests for the TransportationBooking model in the transportation app.
    
    These tests verify that TransportationBooking objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the TransportationBooking model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for TransportationBooking tests.
        
        Extends the base setUp method to include transportation types, providers,
        options, and bookings for testing.
        """
        super().setUp()
        
        # Create transportation types
        self.air_type = TransportationType.objects.create(
            name="Air",
            icon="airplane",
            description="Air transportation including flights and helicopters"
        )
        
        # Create transportation providers
        self.airline_provider = TransportationProvider.objects.create(
            name="Global Airways",
            transportation_type=self.air_type,
            website="https://globalairways.example.com",
            contact_phone="+1-800-123-4567",
            contact_email="info@globalairways.example.com",
            logo="providers/global_airways_logo.png"
        )
        
        # Create origin and destination
        self.origin = self.create_destination("New York", self.test_region)
        self.destination = self.test_destination  # Use the destination from base setup
        
        # Create transportation options
        self.flight_option = TransportationOption.objects.create(
            provider=self.airline_provider,
            origin=self.origin,
            destination=self.destination,
            departure_time=timezone.now() + datetime.timedelta(days=30, hours=10),
            arrival_time=timezone.now() + datetime.timedelta(days=30, hours=22),
            price=Decimal('499.99'),
            currency='USD',
            reference_code='GA123',
            available_seats=50,
            class_type='economy',
            features='Wi-Fi, Meals, Entertainment',
            is_direct=True
        )
        
        # Create a transportation booking
        self.booking = TransportationBooking.objects.create(
            user=self.test_user,
            transportation_option=self.flight_option,
            booking_reference='TB12345',
            passenger_name='John Doe',
            passenger_email='john.doe@example.com',
            passenger_phone='+1234567890',
            num_passengers=2,
            total_price=Decimal('999.98'),
            status='confirmed',
            booking_date=timezone.now(),
            special_requests='Window seats preferred'
        )
    
    def test_transportation_booking_creation(self):
        """
        Test that a TransportationBooking can be created with the expected attributes.
        
        Verifies that the TransportationBooking model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new transportation booking
        booking = TransportationBooking.objects.create(
            user=self.admin_user,
            transportation_option=self.flight_option,
            booking_reference='TB67890',
            passenger_name='Jane Smith',
            passenger_email='jane.smith@example.com',
            passenger_phone='+0987654321',
            num_passengers=1,
            total_price=Decimal('499.99'),
            status='pending',
            booking_date=timezone.now(),
            special_requests='Vegetarian meal'
        )
        
        # Verify the transportation booking was created with the correct attributes
        self.assertEqual(booking.user, self.admin_user)
        self.assertEqual(booking.transportation_option, self.flight_option)
        self.assertEqual(booking.booking_reference, 'TB67890')
        self.assertEqual(booking.passenger_name, 'Jane Smith')
        self.assertEqual(booking.passenger_email, 'jane.smith@example.com')
        self.assertEqual(booking.passenger_phone, '+0987654321')
        self.assertEqual(booking.num_passengers, 1)
        self.assertEqual(booking.total_price, Decimal('499.99'))
        self.assertEqual(booking.status, 'pending')
        self.assertIsNotNone(booking.booking_date)
        self.assertEqual(booking.special_requests, 'Vegetarian meal')
        
    def test_transportation_booking_str_method(self):
        """
        Test the string representation of a TransportationBooking object.
        
        Verifies that the __str__ method returns the expected string,
        which should include the booking reference and passenger name.
        """
        expected_str = f"Booking TB12345 for John Doe"
        self.assertEqual(str(self.booking), expected_str)
        
    def test_transportation_booking_get_absolute_url(self):
        """
        Test the get_absolute_url method of the TransportationBooking model.
        
        Verifies that the URL generated for a booking detail page is correct
        and matches the expected URL pattern.
        """
        expected_url = reverse('transportation:booking_detail', kwargs={'booking_reference': self.booking.booking_reference})
        self.assertEqual(self.booking.get_absolute_url(), expected_url)
        
    def test_transportation_booking_calculate_price(self):
        """
        Test the calculate_price method of the TransportationBooking model.
        
        Verifies that the calculate_price method correctly calculates
        the total price based on the number of passengers and option price.
        """
        # Initially the total price is set to 999.98 (2 * 499.99)
        self.assertEqual(self.booking.total_price, Decimal('999.98'))
        
        # Change the number of passengers to 3
        self.booking.num_passengers = 3
        
        # Calculate the new price
        self.booking.calculate_price()
        
        # The new price should be 3 * 499.99 = 1499.97
        self.assertEqual(self.booking.total_price, Decimal('1499.97'))
        
    def test_transportation_booking_cancel(self):
        """
        Test the cancel method of the TransportationBooking model.
        
        Verifies that the cancel method correctly updates the booking status
        and increases the available seats for the transportation option.
        """
        # Initially the booking is confirmed and the option has 50 seats
        self.assertEqual(self.booking.status, 'confirmed')
        self.assertEqual(self.flight_option.available_seats, 50)
        
        # Cancel the booking
        self.booking.cancel()
        
        # The booking status should be 'cancelled'
        self.assertEqual(self.booking.status, 'cancelled')
        
        # Refresh the flight option from the database
        self.flight_option.refresh_from_db()
        
        # The available seats should be increased by the number of passengers (2)
        self.assertEqual(self.flight_option.available_seats, 52)


class TransportationViewTests(TravelGuideBaseTestCase):
    """
    Tests for the views in the transportation app.
    
    These tests verify that the views render the correct templates,
    contain the expected context data, and handle form submissions correctly.
    Each test focuses on a specific view or aspect of view functionality.
    """
    
    def setUp(self):
        """
        Set up test data for transportation view tests.
        
        Extends the base setUp method to include necessary transportation data.
        """
        super().setUp()
        
        # Create transportation types
        self.air_type = TransportationType.objects.create(
            name="Air",
            icon="airplane",
            description="Air transportation including flights and helicopters"
        )
        
        self.rail_type = TransportationType.objects.create(
            name="Rail",
            icon="train",
            description="Rail transportation including trains and subways"
        )
        
        # Create transportation providers
        self.airline_provider = TransportationProvider.objects.create(
            name="Global Airways",
            transportation_type=self.air_type,
            website="https://globalairways.example.com",
            contact_phone="+1-800-123-4567",
            contact_email="info@globalairways.example.com",
            logo="providers/global_airways_logo.png"
        )
        
        # Create origin and destination
        self.origin = self.create_destination("New York", self.test_region)
        self.destination = self.test_destination  # Use the destination from base setup
        
        # Create transportation options
        self.flight_option = TransportationOption.objects.create(
            provider=self.airline_provider,
            origin=self.origin,
            destination=self.destination,
            departure_time=timezone.now() + datetime.timedelta(days=30, hours=10),
            arrival_time=timezone.now() + datetime.timedelta(days=30, hours=22),
            price=Decimal('499.99'),
            currency='USD',
            reference_code='GA123',
            available_seats=50,
            class_type='economy',
            features='Wi-Fi, Meals, Entertainment',
            is_direct=True
        )
        
        # Create a transportation booking
        self.booking = TransportationBooking.objects.create(
            user=self.test_user,
            transportation_option=self.flight_option,
            booking_reference='TB12345',
            passenger_name='John Doe',
            passenger_email='john.doe@example.com',
            passenger_phone='+1234567890',
            num_passengers=2,
            total_price=Decimal('999.98'),
            status='confirmed',
            booking_date=timezone.now(),
            special_requests='Window seats preferred'
        )
        
        # Log in the test user
        self.login_test_user()
    
    def test_transportation_home_view(self):
        """
        Test the transportation home view.
        
        Verifies that the transportation home view returns a 200 status code,
        uses the correct template, and includes the expected context data.
        """
        response = self.client.get(reverse('transportation:home'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'transportation/home.html')
        
        # Check that the transportation types are in the context
        self.assertIn('transportation_types', response.context)
        self.assertEqual(list(response.context['transportation_types']), [self.air_type, self.rail_type])
        
    def test_transportation_search_view(self):
        """
        Test the transportation search view.
        
        Verifies that the transportation search view returns a 200 status code,
        uses the correct template, and includes the search results in the context.
        """
        # Get the search page
        response = self.client.get(reverse('transportation:search'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'transportation/search.html')
        
        # Submit a search query
        response = self.client.get(reverse('transportation:search'), {
            'origin': self.origin.id,
            'destination': self.destination.id,
            'departure_date': (timezone.now() + datetime.timedelta(days=30)).date().isoformat(),
            'transportation_type': self.air_type.id
        })
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the search results are in the context
        self.assertIn('options', response.context)
        self.assertEqual(list(response.context['options']), [self.flight_option])
        
    def test_transportation_option_detail_view(self):
        """
        Test the transportation option detail view.
        
        Verifies that the transportation option detail view returns a 200 status code,
        uses the correct template, and includes the option in the context.
        """
        response = self.client.get(reverse('transportation:option_detail', kwargs={'pk': self.flight_option.pk}))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'transportation/option_detail.html')
        
        # Check that the option is in the context
        self.assertEqual(response.context['option'], self.flight_option)
        
    def test_transportation_provider_detail_view(self):
        """
        Test the transportation provider detail view.
        
        Verifies that the transportation provider detail view returns a 200 status code,
        uses the correct template, and includes the provider in the context.
        """
        response = self.client.get(reverse('transportation:provider_detail', kwargs={'pk': self.airline_provider.pk}))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'transportation/provider_detail.html')
        
        # Check that the provider is in the context
        self.assertEqual(response.context['provider'], self.airline_provider)
        
    def test_transportation_booking_create_view(self):
        """
        Test the transportation booking create view.
        
        Verifies that the transportation booking create view returns a 200 status code,
        uses the correct template, and allows creating a booking.
        """
        response = self.client.get(reverse('transportation:booking_create', kwargs={'pk': self.flight_option.pk}))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'transportation/booking_form.html')
        
        # Check that the option is in the context
        self.assertEqual(response.context['option'], self.flight_option)
        
        # Submit the booking create form
        response = self.client.post(reverse('transportation:booking_create', kwargs={'pk': self.flight_option.pk}), {
            'passenger_name': 'Jane Smith',
            'passenger_email': 'jane.smith@example.com',
            'passenger_phone': '+0987654321',
            'num_passengers': 1,
            'special_requests': 'Vegetarian meal'
        })
        
        # Check that the booking was created and redirected
        self.assertEqual(response.status_code, 302)  # Redirect status code
        
        # Check that a new booking was created
        self.assertEqual(TransportationBooking.objects.count(), 2)
        
        # Get the newly created booking
        new_booking = TransportationBooking.objects.exclude(id=self.booking.id).first()
        
        # Check that the booking has the correct attributes
        self.assertEqual(new_booking.user, self.test_user)
        self.assertEqual(new_booking.transportation_option, self.flight_option)
        self.assertEqual(new_booking.passenger_name, 'Jane Smith')
        self.assertEqual(new_booking.passenger_email, 'jane.smith@example.com')
        self.assertEqual(new_booking.passenger_phone, '+0987654321')
        self.assertEqual(new_booking.num_passengers, 1)
        self.assertEqual(new_booking.total_price, Decimal('499.99'))
        self.assertEqual(new_booking.special_requests, 'Vegetarian meal')
        
    def test_transportation_booking_list_view(self):
        """
        Test the transportation booking list view.
        
        Verifies that the transportation booking list view returns a 200 status code,
        uses the correct template, and includes the user's bookings in the context.
        """
        response = self.client.get(reverse('transportation:booking_list'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'transportation/booking_list.html')
        
        # Check that the bookings are in the context
        self.assertIn('bookings', response.context)
        self.assertEqual(list(response.context['bookings']), [self.booking])
        
    def test_transportation_booking_detail_view(self):
        """
        Test the transportation booking detail view.
        
        Verifies that the transportation booking detail view returns a 200 status code,
        uses the correct template, and includes the booking in the context.
        """
        response = self.client.get(reverse('transportation:booking_detail', kwargs={'booking_reference': self.booking.booking_reference}))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'transportation/booking_detail.html')
        
        # Check that the booking is in the context
        self.assertEqual(response.context['booking'], self.booking)
        
    def test_transportation_booking_cancel_view(self):
        """
        Test the transportation booking cancel view.
        
        Verifies that the transportation booking cancel view returns a 200 status code,
        uses the correct template, and allows cancelling a booking.
        """
        response = self.client.get(reverse('transportation:booking_cancel', kwargs={'booking_reference': self.booking.booking_reference}))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'transportation/booking_cancel.html')
        
        # Submit the booking cancel form
        response = self.client.post(reverse('transportation:booking_cancel', kwargs={'booking_reference': self.booking.booking_reference}))
        
        # Check that the booking was cancelled and redirected
        self.assertEqual(response.status_code, 302)  # Redirect status code
        
        # Refresh the booking from the database
        self.booking.refresh_from_db()
        
        # Check that the booking status is now 'cancelled'
        self.assertEqual(self.booking.status, 'cancelled')
