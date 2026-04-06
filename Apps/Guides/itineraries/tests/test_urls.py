"""
Tests for the itineraries app URL configurations.

This module contains test cases for URL routing and resolution
to ensure all URL patterns are correctly configured.
"""

from django.test import SimpleTestCase
from django.urls import reverse, resolve

from itineraries.views import (
    ItineraryListView, MyItinerariesView, ItineraryDetailView,
    ItineraryCreateView, ItineraryUpdateView, ItineraryDeleteView,
    add_activity, edit_activity, delete_activity, edit_day,
    share_itinerary
)


class ItineraryUrlsTest(SimpleTestCase):
    """
    Test case for URL pattern resolution in the itineraries app.
    
    Verifies that URLs correctly resolve to their intended view functions/classes
    and that URL name reversing works properly.
    """
    
    def test_itinerary_list_url_resolves(self):
        """
        Test that the itinerary list URL resolves to the ItineraryListView.
        
        Verifies URL pattern for public itinerary listing works correctly.
        """
        url = reverse('itineraries:itinerary_list')
        self.assertEqual(url, '/itineraries/')
        self.assertEqual(
            resolve(url).func.view_class,
            ItineraryListView
        )
    
    def test_my_itineraries_url_resolves(self):
        """
        Test that the my itineraries URL resolves to the MyItinerariesView.
        
        Verifies URL pattern for user's personal itinerary listing works correctly.
        """
        url = reverse('itineraries:my_itineraries')
        self.assertEqual(url, '/itineraries/my/')
        self.assertEqual(
            resolve(url).func.view_class,
            MyItinerariesView
        )
    
    def test_itinerary_detail_url_resolves(self):
        """
        Test that the itinerary detail URL resolves to the ItineraryDetailView.
        
        Verifies URL pattern with primary key parameter works correctly.
        """
        url = reverse('itineraries:itinerary_detail', args=[1])
        self.assertEqual(url, '/itineraries/1/')
        self.assertEqual(
            resolve(url).func.view_class,
            ItineraryDetailView
        )
    
    def test_itinerary_create_url_resolves(self):
        """
        Test that the itinerary create URL resolves to the ItineraryCreateView.
        
        Verifies URL pattern for creating new itineraries works correctly.
        """
        url = reverse('itineraries:itinerary_create')
        self.assertEqual(url, '/itineraries/create/')
        self.assertEqual(
            resolve(url).func.view_class,
            ItineraryCreateView
        )
    
    def test_itinerary_update_url_resolves(self):
        """
        Test that the itinerary update URL resolves to the ItineraryUpdateView.
        
        Verifies URL pattern for editing itineraries works correctly.
        """
        url = reverse('itineraries:itinerary_update', args=[1])
        self.assertEqual(url, '/itineraries/1/edit/')
        self.assertEqual(
            resolve(url).func.view_class,
            ItineraryUpdateView
        )
    
    def test_itinerary_delete_url_resolves(self):
        """
        Test that the itinerary delete URL resolves to the ItineraryDeleteView.
        
        Verifies URL pattern for deleting itineraries works correctly.
        """
        url = reverse('itineraries:itinerary_delete', args=[1])
        self.assertEqual(url, '/itineraries/1/delete/')
        self.assertEqual(
            resolve(url).func.view_class,
            ItineraryDeleteView
        )
    
    def test_edit_day_url_resolves(self):
        """
        Test that the edit day URL resolves to the edit_day function view.
        
        Verifies URL pattern for editing a specific itinerary day works correctly.
        """
        url = reverse('itineraries:edit_day', args=[1])
        self.assertEqual(url, '/itineraries/day/1/edit/')
        self.assertEqual(resolve(url).func, edit_day)
    
    def test_add_activity_url_resolves(self):
        """
        Test that the add activity URL resolves to the add_activity function view.
        
        Verifies URL pattern for adding activities to an itinerary day works correctly.
        """
        url = reverse('itineraries:add_activity', args=[1])
        self.assertEqual(url, '/itineraries/day/1/add_activity/')
        self.assertEqual(resolve(url).func, add_activity)
    
    def test_edit_activity_url_resolves(self):
        """
        Test that the edit activity URL resolves to the edit_activity function view.
        
        Verifies URL pattern for editing an activity works correctly.
        """
        url = reverse('itineraries:edit_activity', args=[1])
        self.assertEqual(url, '/itineraries/activity/1/edit/')
        self.assertEqual(resolve(url).func, edit_activity)
    
    def test_delete_activity_url_resolves(self):
        """
        Test that the delete activity URL resolves to the delete_activity function view.
        
        Verifies URL pattern for deleting an activity works correctly.
        """
        url = reverse('itineraries:delete_activity', args=[1])
        self.assertEqual(url, '/itineraries/activity/1/delete/')
        self.assertEqual(resolve(url).func, delete_activity)
    
    def test_share_itinerary_url_resolves(self):
        """
        Test that the share itinerary URL resolves to the share_itinerary function view.
        
        Verifies URL pattern for sharing an itinerary works correctly.
        """
        url = reverse('itineraries:itinerary_share', args=[1])
        self.assertEqual(url, '/itineraries/1/share/')
        self.assertEqual(resolve(url).func, share_itinerary)
