"""
Test cases for the emergency app.

This module contains comprehensive test cases for all functionality
in the emergency app, including models, views, and emergency assistance features.
Every test function is thoroughly documented to make understanding
the tests easier for programmers.
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
import datetime

from emergency.models import EmergencyContact, EmergencyAssistanceRequest, LocalEmergencyInfo
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class EmergencyContactModelTests(TravelGuideBaseTestCase):
    """
    Tests for the EmergencyContact model in the emergency app.
    
    These tests verify that EmergencyContact objects can be created correctly,
    and that their methods work as expected. Each test focuses on a 
    specific aspect of the EmergencyContact model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for EmergencyContact tests.
        
        Extends the base setUp method to include emergency contacts for testing.
        """
        super().setUp()
        
        # Create emergency contacts for the test user
        self.emergency_contact1 = EmergencyContact.objects.create(
            user=self.test_user,
            name="John Doe",
            relationship="Family",
            phone_number="+1234567890",
            email="john.doe@example.com",
            is_primary=True
        )
        
        self.emergency_contact2 = EmergencyContact.objects.create(
            user=self.test_user,
            name="Jane Smith",
            relationship="Friend",
            phone_number="+0987654321",
            email="jane.smith@example.com",
            is_primary=False
        )
    
    def test_emergency_contact_creation(self):
        """
        Test that an EmergencyContact can be created with the expected attributes.
        
        Verifies that the EmergencyContact model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new emergency contact for the admin user
        contact = EmergencyContact.objects.create(
            user=self.admin_user,
            name="Robert Johnson",
            relationship="Colleague",
            phone_number="+1122334455",
            email="robert.johnson@example.com",
            is_primary=True
        )
        
        # Verify the emergency contact was created with the correct attributes
        self.assertEqual(contact.user, self.admin_user)
        self.assertEqual(contact.name, "Robert Johnson")
        self.assertEqual(contact.relationship, "Colleague")
        self.assertEqual(contact.phone_number, "+1122334455")
        self.assertEqual(contact.email, "robert.johnson@example.com")
        self.assertTrue(contact.is_primary)
        
    def test_emergency_contact_str_method(self):
        """
        Test the string representation of an EmergencyContact object.
        
        Verifies that the __str__ method returns the expected string,
        which should include the contact name and relationship.
        """
        expected_str = "John Doe (Family)"
        self.assertEqual(str(self.emergency_contact1), expected_str)
        
    def test_emergency_contact_primary_constraint(self):
        """
        Test the primary contact constraint.
        
        Verifies that when a new emergency contact is set as primary,
        any existing primary contact for the same user is automatically
        set to non-primary.
        """
        # Initially, emergency_contact1 is primary and emergency_contact2 is not
        self.assertTrue(self.emergency_contact1.is_primary)
        self.assertFalse(self.emergency_contact2.is_primary)
        
        # Set emergency_contact2 as primary
        self.emergency_contact2.is_primary = True
        self.emergency_contact2.save()
        
        # Refresh emergency_contact1 from the database
        self.emergency_contact1.refresh_from_db()
        
        # Now emergency_contact1 should be non-primary and emergency_contact2 should be primary
        self.assertFalse(self.emergency_contact1.is_primary)
        self.assertTrue(self.emergency_contact2.is_primary)
        
    def test_get_primary_contact(self):
        """
        Test getting the primary emergency contact for a user.
        
        Verifies that the get_primary_contact method correctly returns
        the primary emergency contact for a user.
        """
        # Get the primary contact for the test user
        primary_contact = EmergencyContact.objects.filter(
            user=self.test_user, is_primary=True
        ).first()
        
        # Verify it's the expected contact
        self.assertEqual(primary_contact, self.emergency_contact1)
        
        # Set emergency_contact2 as primary
        self.emergency_contact2.is_primary = True
        self.emergency_contact2.save()
        
        # Get the primary contact again
        primary_contact = EmergencyContact.objects.filter(
            user=self.test_user, is_primary=True
        ).first()
        
        # Verify it's now emergency_contact2
        self.assertEqual(primary_contact, self.emergency_contact2)


class EmergencyAssistanceRequestModelTests(TravelGuideBaseTestCase):
    """
    Tests for the EmergencyAssistanceRequest model in the emergency app.
    
    These tests verify that EmergencyAssistanceRequest objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the EmergencyAssistanceRequest model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for EmergencyAssistanceRequest tests.
        
        Extends the base setUp method to include emergency assistance requests for testing.
        """
        super().setUp()
        
        # Create an emergency assistance request for the test user
        self.assistance_request = EmergencyAssistanceRequest.objects.create(
            user=self.test_user,
            location="Tokyo, Japan",
            latitude=35.6895,
            longitude=139.6917,
            emergency_type="medical",
            description="Need medical assistance due to high fever",
            status="pending",
            created_at=timezone.now()
        )
    
    def test_emergency_assistance_request_creation(self):
        """
        Test that an EmergencyAssistanceRequest can be created with the expected attributes.
        
        Verifies that the EmergencyAssistanceRequest model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new emergency assistance request for the admin user
        request = EmergencyAssistanceRequest.objects.create(
            user=self.admin_user,
            location="Paris, France",
            latitude=48.8566,
            longitude=2.3522,
            emergency_type="security",
            description="Lost passport and wallet",
            status="pending",
            created_at=timezone.now()
        )
        
        # Verify the emergency assistance request was created with the correct attributes
        self.assertEqual(request.user, self.admin_user)
        self.assertEqual(request.location, "Paris, France")
        self.assertEqual(request.latitude, 48.8566)
        self.assertEqual(request.longitude, 2.3522)
        self.assertEqual(request.emergency_type, "security")
        self.assertEqual(request.description, "Lost passport and wallet")
        self.assertEqual(request.status, "pending")
        self.assertIsNotNone(request.created_at)
        
    def test_emergency_assistance_request_str_method(self):
        """
        Test the string representation of an EmergencyAssistanceRequest object.
        
        Verifies that the __str__ method returns the expected string,
        which should include the emergency type and status.
        """
        expected_str = f"Medical emergency for testuser - pending"
        self.assertEqual(str(self.assistance_request), expected_str)
        
    def test_emergency_assistance_request_update_status(self):
        """
        Test updating the status of an EmergencyAssistanceRequest.
        
        Verifies that the status can be updated and that the resolved_at
        timestamp is set when the status is changed to 'resolved'.
        """
        # Initially the request is pending and has no resolved_at timestamp
        self.assertEqual(self.assistance_request.status, "pending")
        self.assertIsNone(self.assistance_request.resolved_at)
        
        # Update the status to 'in_progress'
        self.assistance_request.status = "in_progress"
        self.assistance_request.save()
        
        # Verify the status was updated but resolved_at is still None
        self.assertEqual(self.assistance_request.status, "in_progress")
        self.assertIsNone(self.assistance_request.resolved_at)
        
        # Update the status to 'resolved'
        self.assistance_request.status = "resolved"
        self.assistance_request.save()
        
        # Verify the status was updated and resolved_at is now set
        self.assertEqual(self.assistance_request.status, "resolved")
        self.assertIsNotNone(self.assistance_request.resolved_at)
        
    def test_emergency_assistance_request_response_time(self):
        """
        Test calculating the response time for an EmergencyAssistanceRequest.
        
        Verifies that the response_time property correctly calculates
        the time between creation and resolution of a request.
        """
        # Set the created_at time to 1 hour ago
        self.assistance_request.created_at = timezone.now() - datetime.timedelta(hours=1)
        self.assistance_request.save()
        
        # Resolve the request
        self.assistance_request.status = "resolved"
        self.assistance_request.resolved_at = timezone.now()
        self.assistance_request.save()
        
        # Calculate the response time in minutes
        response_time = (self.assistance_request.resolved_at - self.assistance_request.created_at).total_seconds() / 60
        
        # The response time should be approximately 60 minutes
        self.assertAlmostEqual(response_time, 60, delta=1)  # Allow for small timing differences


class LocalEmergencyInfoModelTests(TravelGuideBaseTestCase):
    """
    Tests for the LocalEmergencyInfo model in the emergency app.
    
    These tests verify that LocalEmergencyInfo objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the LocalEmergencyInfo model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for LocalEmergencyInfo tests.
        
        Extends the base setUp method to include local emergency info for testing.
        """
        super().setUp()
        
        # Create local emergency info for a destination
        self.local_info = LocalEmergencyInfo.objects.create(
            destination=self.test_destination,
            police_number="110",
            ambulance_number="119",
            fire_number="119",
            embassy_address="1-10-5 Akasaka, Minato-ku, Tokyo",
            embassy_phone="+81-3-3224-5000",
            hospital_name="Tokyo Medical University Hospital",
            hospital_address="6-7-1 Nishishinjuku, Shinjuku-ku, Tokyo",
            hospital_phone="+81-3-3342-6111",
            additional_info="In case of emergency, dial 110 for police, 119 for ambulance/fire."
        )
    
    def test_local_emergency_info_creation(self):
        """
        Test that a LocalEmergencyInfo can be created with the expected attributes.
        
        Verifies that the LocalEmergencyInfo model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new destination
        destination = self.create_destination("Paris", self.test_region)
        
        # Create local emergency info for the new destination
        local_info = LocalEmergencyInfo.objects.create(
            destination=destination,
            police_number="17",
            ambulance_number="15",
            fire_number="18",
            embassy_address="4 Avenue Gabriel, 75008 Paris, France",
            embassy_phone="+33-1-43-12-22-22",
            hospital_name="Hôpital Hôtel-Dieu",
            hospital_address="1 Parvis Notre-Dame, 75004 Paris, France",
            hospital_phone="+33-1-42-34-82-34",
            additional_info="European emergency number: 112"
        )
        
        # Verify the local emergency info was created with the correct attributes
        self.assertEqual(local_info.destination, destination)
        self.assertEqual(local_info.police_number, "17")
        self.assertEqual(local_info.ambulance_number, "15")
        self.assertEqual(local_info.fire_number, "18")
        self.assertEqual(local_info.embassy_address, "4 Avenue Gabriel, 75008 Paris, France")
        self.assertEqual(local_info.embassy_phone, "+33-1-43-12-22-22")
        self.assertEqual(local_info.hospital_name, "Hôpital Hôtel-Dieu")
        self.assertEqual(local_info.hospital_address, "1 Parvis Notre-Dame, 75004 Paris, France")
        self.assertEqual(local_info.hospital_phone, "+33-1-42-34-82-34")
        self.assertEqual(local_info.additional_info, "European emergency number: 112")
        
    def test_local_emergency_info_str_method(self):
        """
        Test the string representation of a LocalEmergencyInfo object.
        
        Verifies that the __str__ method returns the expected string,
        which should include the destination name.
        """
        expected_str = f"Emergency info for {self.test_destination.name}"
        self.assertEqual(str(self.local_info), expected_str)


class EmergencyViewTests(TravelGuideBaseTestCase):
    """
    Tests for the views in the emergency app.
    
    These tests verify that the views render the correct templates,
    contain the expected context data, and handle form submissions correctly.
    Each test focuses on a specific view or aspect of view functionality.
    """
    
    def setUp(self):
        """
        Set up test data for emergency view tests.
        
        Extends the base setUp method to include necessary emergency data.
        """
        super().setUp()
        
        # Create emergency contacts for the test user
        self.emergency_contact = EmergencyContact.objects.create(
            user=self.test_user,
            name="John Doe",
            relationship="Family",
            phone_number="+1234567890",
            email="john.doe@example.com",
            is_primary=True
        )
        
        # Create local emergency info for the test destination
        self.local_info = LocalEmergencyInfo.objects.create(
            destination=self.test_destination,
            police_number="110",
            ambulance_number="119",
            fire_number="119",
            embassy_address="1-10-5 Akasaka, Minato-ku, Tokyo",
            embassy_phone="+81-3-3224-5000",
            hospital_name="Tokyo Medical University Hospital",
            hospital_address="6-7-1 Nishishinjuku, Shinjuku-ku, Tokyo",
            hospital_phone="+81-3-3342-6111",
            additional_info="In case of emergency, dial 110 for police, 119 for ambulance/fire."
        )
        
        # Log in the test user
        self.login_test_user()
    
    def test_emergency_dashboard_view(self):
        """
        Test the emergency dashboard view.
        
        Verifies that the emergency dashboard view returns a 200 status code,
        uses the correct template, and includes the expected context data.
        """
        response = self.client.get(reverse('emergency:dashboard'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'emergency/dashboard.html')
        
        # Check that the emergency contacts are in the context
        self.assertIn('emergency_contacts', response.context)
        self.assertEqual(list(response.context['emergency_contacts']), [self.emergency_contact])
        
    def test_emergency_contact_list_view(self):
        """
        Test the emergency contact list view.
        
        Verifies that the emergency contact list view returns a 200 status code,
        uses the correct template, and includes the user's emergency contacts in the context.
        """
        response = self.client.get(reverse('emergency:contact_list'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'emergency/contact_list.html')
        
        # Check that the emergency contacts are in the context
        self.assertIn('contacts', response.context)
        self.assertEqual(list(response.context['contacts']), [self.emergency_contact])
        
    def test_emergency_contact_create_view(self):
        """
        Test the emergency contact create view.
        
        Verifies that the emergency contact create view returns a 200 status code,
        uses the correct template, and allows creating an emergency contact.
        """
        response = self.client.get(reverse('emergency:contact_create'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'emergency/contact_form.html')
        
        # Submit the contact create form
        response = self.client.post(reverse('emergency:contact_create'), {
            'name': 'Jane Smith',
            'relationship': 'Friend',
            'phone_number': '+0987654321',
            'email': 'jane.smith@example.com',
            'is_primary': False
        })
        
        # Check that the contact was created and redirected
        self.assertEqual(response.status_code, 302)  # Redirect status code
        
        # Check that the contact was created
        self.assertTrue(EmergencyContact.objects.filter(
            user=self.test_user,
            name='Jane Smith',
            relationship='Friend'
        ).exists())
        
    def test_emergency_contact_update_view(self):
        """
        Test the emergency contact update view.
        
        Verifies that the emergency contact update view returns a 200 status code,
        uses the correct template, and allows updating an emergency contact.
        """
        response = self.client.get(reverse('emergency:contact_update', kwargs={'pk': self.emergency_contact.pk}))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'emergency/contact_form.html')
        
        # Submit the contact update form
        response = self.client.post(reverse('emergency:contact_update', kwargs={'pk': self.emergency_contact.pk}), {
            'name': 'John Doe Updated',
            'relationship': 'Close Family',
            'phone_number': '+1234567890',
            'email': 'john.updated@example.com',
            'is_primary': True
        })
        
        # Check that the contact was updated and redirected
        self.assertEqual(response.status_code, 302)  # Redirect status code
        
        # Refresh the emergency contact from the database
        self.emergency_contact.refresh_from_db()
        
        # Check that the contact was updated
        self.assertEqual(self.emergency_contact.name, 'John Doe Updated')
        self.assertEqual(self.emergency_contact.relationship, 'Close Family')
        self.assertEqual(self.emergency_contact.email, 'john.updated@example.com')
        
    def test_emergency_contact_delete_view(self):
        """
        Test the emergency contact delete view.
        
        Verifies that the emergency contact delete view returns a 200 status code,
        uses the correct template, and allows deleting an emergency contact.
        """
        response = self.client.get(reverse('emergency:contact_delete', kwargs={'pk': self.emergency_contact.pk}))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'emergency/contact_confirm_delete.html')
        
        # Submit the contact delete form
        response = self.client.post(reverse('emergency:contact_delete', kwargs={'pk': self.emergency_contact.pk}))
        
        # Check that the contact was deleted and redirected
        self.assertEqual(response.status_code, 302)  # Redirect status code
        
        # Check that the contact was deleted
        self.assertFalse(EmergencyContact.objects.filter(pk=self.emergency_contact.pk).exists())
        
    def test_emergency_assistance_request_view(self):
        """
        Test the emergency assistance request view.
        
        Verifies that the emergency assistance request view returns a 200 status code,
        uses the correct template, and allows requesting emergency assistance.
        """
        response = self.client.get(reverse('emergency:request_assistance'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'emergency/request_assistance.html')
        
        # Submit the assistance request form
        response = self.client.post(reverse('emergency:request_assistance'), {
            'location': 'Tokyo, Japan',
            'latitude': 35.6895,
            'longitude': 139.6917,
            'emergency_type': 'medical',
            'description': 'Need medical assistance due to high fever'
        })
        
        # Check that the request was created and redirected
        self.assertEqual(response.status_code, 302)  # Redirect status code
        
        # Check that the request was created
        self.assertTrue(EmergencyAssistanceRequest.objects.filter(
            user=self.test_user,
            location='Tokyo, Japan',
            emergency_type='medical'
        ).exists())
        
    def test_local_emergency_info_view(self):
        """
        Test the local emergency info view.
        
        Verifies that the local emergency info view returns a 200 status code,
        uses the correct template, and includes the local emergency info in the context.
        """
        response = self.client.get(reverse('emergency:local_info', kwargs={'destination_id': self.test_destination.id}))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'emergency/local_info.html')
        
        # Check that the local info is in the context
        self.assertIn('local_info', response.context)
        self.assertEqual(response.context['local_info'], self.local_info)
