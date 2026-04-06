"""
Test suite for the destination submission workflow.

This module contains tests that verify:
1. Local guides are redirected to pending submission workflow
2. Managers/admins can directly create destinations
3. Submissions by local guides are stored in PendingDestination table
4. Approval process works correctly for pending destinations
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from accounts.models import User
from destinations.models import Destination, PendingDestination
from django.core import mail

class DestinationSubmissionWorkflowTest(TestCase):
    """
    Test cases for the destination submission workflow.
    
    Verifies that the submission process works correctly for different user roles:
    - Local guides are redirected to the pending submission form
    - Managers and admins can directly create destinations
    - Submissions by local guides are properly stored for review
    """
    
    def setUp(self):
        """
        Set up test data including users with different roles and test destination data.
        """
        # Create users with different roles
        self.local_guide = User.objects.create_user(
            email='guide@example.com',
            password='testpassword',
            first_name='Local',
            last_name='Guide',
            role='LOCAL_GUIDE'
        )
        
        self.manager = User.objects.create_user(
            email='manager@example.com',
            password='testpassword',
            first_name='Manager',
            last_name='User',
            role='MANAGER'
        )
        
        self.admin = User.objects.create_user(
            email='admin@example.com',
            password='testpassword',
            first_name='Admin',
            last_name='User',
            role='ADMIN',
            is_staff=True
        )
        
        # Test destination data
        self.destination_data = {
            'name': 'Test Destination',
            'region': 'Europe',
            'short_description': 'A test destination',
            'description': 'This is a detailed description of the test destination.',
            'city': 'Test City',
            'country': 'Test Country',
            'latitude': '41.9028',
            'longitude': '12.4964',
            'is_featured': False
        }
        
        # Create clients
        self.local_guide_client = Client()
        self.manager_client = Client()
        self.admin_client = Client()
        
        # Login users
        self.local_guide_client.login(email='guide@example.com', password='testpassword')
        self.manager_client.login(email='manager@example.com', password='testpassword')
        self.admin_client.login(email='admin@example.com', password='testpassword')

    def test_local_guide_redirected_to_pending_workflow(self):
        """
        Test that local guides are redirected to the pending destination submission form.
        """
        # Local guide attempts to access the direct destination creation form
        response = self.local_guide_client.get(reverse('destinations:destination_create'))
        
        # Should be redirected to the pending destination form
        self.assertRedirects(response, reverse('destinations:pending_destination_create'))
        
        # Check that an info message was added
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('reviewed by our team' in str(message) for message in messages))

    def test_manager_can_directly_create_destination(self):
        """
        Test that managers can directly create destinations without redirection.
        """
        # Manager accesses the destination creation form
        response = self.manager_client.get(reverse('destinations:destination_create'))
        
        # Should load the form without redirection
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'destinations/destination_form.html')

    def test_admin_can_directly_create_destination(self):
        """
        Test that admins can directly create destinations without redirection.
        """
        # Admin accesses the destination creation form
        response = self.admin_client.get(reverse('destinations:destination_create'))
        
        # Should load the form without redirection
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'destinations/destination_form.html')

    def test_local_guide_submission_creates_pending_destination(self):
        """
        Test that submissions by local guides create records in PendingDestination table.
        """
        # Local guide submits a destination through the pending form
        response = self.local_guide_client.post(
            reverse('destinations:pending_destination_create'), 
            self.destination_data, 
            follow=True
        )
        
        # Check if a PendingDestination was created
        self.assertEqual(PendingDestination.objects.count(), 1)
        pending_dest = PendingDestination.objects.first()
        
        # Verify data and approval status
        self.assertEqual(pending_dest.name, self.destination_data['name'])
        self.assertEqual(pending_dest.approval_status, PendingDestination.ApprovalStatus.PENDING)
        self.assertEqual(pending_dest.created_by, self.local_guide)
        
        # Verify no Destination was created
        self.assertEqual(Destination.objects.count(), 0)

    def test_manager_submission_creates_direct_destination(self):
        """
        Test that submissions by managers create approved destinations directly.
        """
        # Manager submits a destination through the direct creation form
        response = self.manager_client.post(
            reverse('destinations:destination_create'), 
            self.destination_data, 
            follow=True
        )
        
        # Check if a Destination was created
        self.assertEqual(Destination.objects.count(), 1)
        dest = Destination.objects.first()
        
        # Verify data and approval status
        self.assertEqual(dest.name, self.destination_data['name'])
        self.assertEqual(dest.approval_status, Destination.ApprovalStatus.APPROVED)
        self.assertEqual(dest.created_by, self.manager)
        
        # No pending destination should be created
        self.assertEqual(PendingDestination.objects.count(), 0)

    def test_pending_destination_approval_process(self):
        """
        Test the approval process for pending destinations.
        """
        # Create a pending destination
        pending = PendingDestination.objects.create(
            name=self.destination_data['name'],
            region=self.destination_data['region'],
            short_description=self.destination_data['short_description'],
            description=self.destination_data['description'],
            city=self.destination_data['city'],
            country=self.destination_data['country'],
            latitude=float(self.destination_data['latitude']),
            longitude=float(self.destination_data['longitude']),
            is_featured=self.destination_data['is_featured'],
            created_by=self.local_guide,
            approval_status=PendingDestination.ApprovalStatus.PENDING
        )
        
        # Manager approves the pending destination
        pending.approve_and_transfer(reviewed_by=self.manager)
        
        # Verify approval status updated
        pending.refresh_from_db()
        self.assertEqual(pending.approval_status, PendingDestination.ApprovalStatus.APPROVED)
        
        # Verify destination was created
        self.assertEqual(Destination.objects.count(), 1)
        destination = Destination.objects.first()
        self.assertEqual(destination.name, self.destination_data['name'])
        self.assertEqual(destination.created_by, self.local_guide)
        
        # Verify approval fields
        self.assertEqual(pending.reviewed_by, self.manager)
        self.assertIsNotNone(pending.review_date)
        
        # Check if an email notification was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.local_guide.email, mail.outbox[0].to)
        self.assertIn('approved', mail.outbox[0].subject.lower())
