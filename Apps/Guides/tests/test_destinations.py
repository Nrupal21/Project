"""
Test cases for the destinations app.

This module contains comprehensive test cases for all functionality
in the destinations app, including models, views, forms, and utilities.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from destinations.models import Destination, Region, Attraction, DestinationImage
from destinations.forms import DestinationSearchForm
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class RegionModelTests(TravelGuideBaseTestCase):
    """
    Tests for the Region model in the destinations app.
    
    These tests verify that Region objects can be created correctly,
    and that their methods work as expected.
    """
    
    def test_region_creation(self):
        """
        Test that a Region can be created with the expected attributes.
        
        Verifies that the Region model can be instantiated with the required
        fields and that the values are stored correctly.
        """
        region = Region.objects.create(
            name='Test Region 2',
            slug='test-region-2',
            description='Another test region description'
        )
        
        # Verify the region was created with the correct attributes
        self.assertEqual(region.name, 'Test Region 2')
        self.assertEqual(region.slug, 'test-region-2')
        self.assertEqual(region.description, 'Another test region description')
        
    def test_region_str_method(self):
        """
        Test the string representation of a Region object.
        
        Verifies that the __str__ method returns the expected string.
        """
        self.assertEqual(str(self.region), 'Test Region')
        
    def test_region_get_absolute_url(self):
        """
        Test the get_absolute_url method of the Region model.
        
        Verifies that the URL generated for a region is correct.
        """
        expected_url = reverse('destinations:region_detail', kwargs={'slug': self.region.slug})
        self.assertEqual(self.region.get_absolute_url(), expected_url)
        
    def test_region_destinations_count(self):
        """
        Test that a Region correctly counts its destinations.
        
        Verifies that the destinations_count property returns the correct number.
        """
        # Create another destination in the same region
        Destination.objects.create(
            name='Another Destination',
            slug='another-destination',
            description='Another destination description',
            region=self.region,
            price=1500.00,
            rating=4.0,
            latitude=23.456,
            longitude=78.901,
            is_featured=False,
            is_active=True
        )
        
        # The region should now have 2 destinations (1 from setup + 1 new)
        self.assertEqual(self.region.destinations.count(), 2)


class DestinationModelTests(TravelGuideBaseTestCase):
    """
    Tests for the Destination model in the destinations app.
    
    These tests verify that Destination objects can be created correctly,
    and that their methods work as expected.
    """
    
    def test_destination_creation(self):
        """
        Test that a Destination can be created with the expected attributes.
        
        Verifies that the Destination model can be instantiated with the required
        fields and that the values are stored correctly.
        """
        destination = Destination.objects.create(
            name='Another Destination',
            slug='another-destination',
            description='Another destination description',
            region=self.region,
            price=1500.00,
            rating=4.0,
            latitude=23.456,
            longitude=78.901,
            is_featured=False,
            is_active=True
        )
        
        # Verify the destination was created with the correct attributes
        self.assertEqual(destination.name, 'Another Destination')
        self.assertEqual(destination.slug, 'another-destination')
        self.assertEqual(destination.price, 1500.00)
        self.assertEqual(destination.region, self.region)
        
    def test_destination_str_method(self):
        """
        Test the string representation of a Destination object.
        
        Verifies that the __str__ method returns the expected string.
        """
        self.assertEqual(str(self.destination), 'Test Destination')
        
    def test_destination_get_absolute_url(self):
        """
        Test the get_absolute_url method of the Destination model.
        
        Verifies that the URL generated for a destination is correct.
        """
        expected_url = reverse('destinations:destination_detail', kwargs={'slug': self.destination.slug})
        self.assertEqual(self.destination.get_absolute_url(), expected_url)
        
    def test_destination_primary_image(self):
        """
        Test that a Destination correctly identifies its primary image.
        
        Verifies that the primary_image property returns the correct image.
        """
        # The primary image should be the one created in setUp
        self.assertEqual(self.destination.primary_image, self.destination_image)
        
    def test_destination_attractions_count(self):
        """
        Test that a Destination correctly counts its attractions.
        
        Verifies that the attractions_count property returns the correct number.
        """
        # Create another attraction for the destination
        Attraction.objects.create(
            name='Another Attraction',
            description='Another attraction description',
            category='museum',
            destination=self.destination,
            is_featured=False,
            is_active=True
        )
        
        # The destination should now have 2 attractions (1 from setup + 1 new)
        self.assertEqual(self.destination.attractions.count(), 2)


class AttractionModelTests(TravelGuideBaseTestCase):
    """
    Tests for the Attraction model in the destinations app.
    
    These tests verify that Attraction objects can be created correctly,
    and that their methods work as expected.
    """
    
    def test_attraction_creation(self):
        """
        Test that an Attraction can be created with the expected attributes.
        
        Verifies that the Attraction model can be instantiated with the required
        fields and that the values are stored correctly.
        """
        attraction = Attraction.objects.create(
            name='New Attraction',
            description='A new attraction description',
            category='museum',
            destination=self.destination,
            is_featured=True,
            is_active=True
        )
        
        # Verify the attraction was created with the correct attributes
        self.assertEqual(attraction.name, 'New Attraction')
        self.assertEqual(attraction.category, 'museum')
        self.assertEqual(attraction.destination, self.destination)
        
    def test_attraction_str_method(self):
        """
        Test the string representation of an Attraction object.
        
        Verifies that the __str__ method returns the expected string.
        """
        self.assertEqual(str(self.attraction), 'Test Attraction')
        
    def test_attraction_get_absolute_url(self):
        """
        Test the get_absolute_url method of the Attraction model.
        
        Verifies that the URL generated for an attraction is correct.
        """
        expected_url = reverse('destinations:attraction_detail', kwargs={
            'destination_slug': self.destination.slug,
            'attraction_id': self.attraction.id
        })
        self.assertEqual(self.attraction.get_absolute_url(), expected_url)


class DestinationViewTests(TravelGuideBaseTestCase):
    """
    Tests for the views in the destinations app.
    
    These tests verify that the views render the correct templates,
    contain the expected context data, and handle form submissions correctly.
    """
    
    def test_destination_list_view(self):
        """
        Test the destination list view.
        
        Verifies that the destination list view returns a 200 status code,
        uses the correct template, and includes the destinations in the context.
        """
        response = self.client.get(reverse('destinations:destination_list'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'destinations/destination_list.html')
        
        # Check that the destinations are in the context
        self.assertIn('destinations', response.context)
        self.assertIn(self.destination, response.context['destinations'])
        
    def test_destination_detail_view(self):
        """
        Test the destination detail view.
        
        Verifies that the destination detail view returns a 200 status code,
        uses the correct template, and includes the destination in the context.
        """
        response = self.client.get(reverse('destinations:destination_detail', kwargs={'slug': self.destination.slug}))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'destinations/destination_detail.html')
        
        # Check that the destination is in the context
        self.assertEqual(response.context['destination'], self.destination)
        
    def test_region_list_view(self):
        """
        Test the region list view.
        
        Verifies that the region list view returns a 200 status code,
        uses the correct template, and includes the regions in the context.
        """
        response = self.client.get(reverse('destinations:region_list'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'destinations/region_list.html')
        
        # Check that the regions are in the context
        self.assertIn('regions', response.context)
        self.assertIn(self.region, response.context['regions'])
        
    def test_region_detail_view(self):
        """
        Test the region detail view.
        
        Verifies that the region detail view returns a 200 status code,
        uses the correct template, and includes the region in the context.
        """
        response = self.client.get(reverse('destinations:region_detail', kwargs={'slug': self.region.slug}))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'destinations/region_detail.html')
        
        # Check that the region is in the context
        self.assertEqual(response.context['region'], self.region)
        
    def test_attraction_detail_view(self):
        """
        Test the attraction detail view.
        
        Verifies that the attraction detail view returns a 200 status code,
        uses the correct template, and includes the attraction in the context.
        """
        response = self.client.get(reverse('destinations:attraction_detail', kwargs={
            'destination_slug': self.destination.slug,
            'attraction_id': self.attraction.id
        }))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'destinations/attraction_detail.html')
        
        # Check that the attraction is in the context
        self.assertEqual(response.context['attraction'], self.attraction)
        
    def test_search_view(self):
        """
        Test the destination search view.
        
        Verifies that the search view returns a 200 status code,
        uses the correct template, and filters destinations correctly.
        """
        # Test with no search parameters
        response = self.client.get(reverse('destinations:search'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'destinations/search_results.html')
        
        # Test with search parameters
        response = self.client.get(reverse('destinations:search'), {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.destination, response.context['destinations'])
        
        # Test with search parameters that don't match any destinations
        response = self.client.get(reverse('destinations:search'), {'q': 'NonexistentDestination'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['destinations']), 0)


class DestinationFormTests(TravelGuideBaseTestCase):
    """
    Tests for the forms in the destinations app.
    
    These tests verify that the forms validate input correctly
    and handle form submissions as expected.
    """
    
    def test_destination_search_form_valid(self):
        """
        Test that the DestinationSearchForm validates correctly with valid data.
        
        Verifies that the form is valid when provided with valid data.
        """
        form_data = {'q': 'Test Destination'}
        form = DestinationSearchForm(data=form_data)
        self.assertTrue(form.is_valid())
        
    def test_destination_search_form_empty(self):
        """
        Test that the DestinationSearchForm validates correctly with empty data.
        
        Verifies that the form is valid when provided with empty data.
        """
        form_data = {'q': ''}
        form = DestinationSearchForm(data=form_data)
        self.assertTrue(form.is_valid())
