"""
Test module for validating the destination submission workflow.

This module contains tests to ensure that the destination submission process
works properly from end to end, including form submission, email notifications,
success page redirection, and the approval workflow.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.conf import settings
from django.core import mail

from accounts.models import User, UserProfile, UserRole
from destinations.models import PendingDestination, Destination, Region
from destinations.utils.email_notifications import send_guide_submission_confirmation


class DestinationSubmissionFlowTest(TestCase):
    """
    Test case for the destination submission flow.
    
    Tests the complete workflow from submission by a local guide to approval
    by a manager, including email notifications and success page redirection.
    """

    def setUp(self):
        """
        Set up test data including users, profiles, and test regions.
        
        Creates a local guide user, manager user, and a test region for submissions.
        """
        # Create a local guide user
        self.guide = User.objects.create_user(
            username='testguide',
            email='guide@example.com',
            password='password123'
        )
        UserProfile.objects.create(
            user=self.guide,
            role=UserRole.LOCAL_GUIDE,
            bio='Test Guide Bio',
            location='Test Location'
        )

        # Create a manager user
        self.manager = User.objects.create_user(
            username='testmanager',
            email='manager@example.com',
            password='password123',
            is_staff=True
        )
        UserProfile.objects.create(
            user=self.manager,
            role=UserRole.MANAGER,
            bio='Test Manager Bio',
            location='Test Location'
        )

        # Create a region for destination submissions
        self.region = Region.objects.create(
            name='Test Region',
            slug='test-region',
            description='A region for testing'
        )
        
        # Set up test client
        self.client = Client()
        
        # Save original email backend
        self.original_email_backend = settings.EMAIL_BACKEND
        # Use memory email backend for testing
        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        
    def tearDown(self):
        """Restore original settings after tests."""
        settings.EMAIL_BACKEND = self.original_email_backend

    def test_guide_submission_flow(self):
        """
        Test the destination submission flow for local guides.
        
        Verifies:
        1. Guide can submit destination to pending workflow
        2. Guide is redirected to success page
        3. Destination data is correctly saved to PendingDestination
        4. Email notifications are sent to both guide and managers
        """
        # Login as the guide
        self.client.login(username='testguide', password='password123')
        
        # Prepare destination submission data
        destination_data = {
            'name': 'Test Destination',
            'slug': 'test-destination',
            'region': self.region.id,
            'description': 'A beautiful test destination',
            'latitude': 10.123456,
            'longitude': 20.123456,
            'climate': 'Moderate',
            'best_time_to_visit': 'Spring',
            'local_customs': 'Test customs',
            'transportation_tips': 'Test transportation tips',
            'safety_info': 'Test safety information'
        }
        
        # Submit the destination through the form
        response = self.client.post(
            reverse('destinations:pending_destination_create'),
            destination_data,
            follow=True
        )
        
        # Check if redirected to success page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'destinations/destination_submission_success.html')
        
        # Check if destination was created in PendingDestination
        pending_destination = PendingDestination.objects.filter(name='Test Destination').first()
        self.assertIsNotNone(pending_destination)
        self.assertEqual(pending_destination.created_by, self.guide)
        self.assertEqual(pending_destination.approval_status, PendingDestination.ApprovalStatus.PENDING)
        
        # Check if emails were sent (1 to guide, 1 to manager)
        self.assertEqual(len(mail.outbox), 2)
        guide_email_sent = any('guide@example.com' in email.to[0] for email in mail.outbox)
        manager_email_sent = any('manager@example.com' in email.to[0] for email in mail.outbox)
        self.assertTrue(guide_email_sent)
        self.assertTrue(manager_email_sent)

    def test_guide_submission_email(self):
        """
        Test the email notification to guide after destination submission.
        
        Verifies the email content and format sent to the guide.
        """
        # Create a test pending destination
        pending_destination = PendingDestination.objects.create(
            name='Email Test Destination',
            slug='email-test-destination',
            region=self.region,
            description='A destination to test email notifications',
            created_by=self.guide
        )
        
        # Send the confirmation email
        send_guide_submission_confirmation(pending_destination, self.guide)
        
        # Check if email was sent to guide
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to[0], 'guide@example.com')
        
        # Verify email content
        self.assertIn('Email Test Destination', email.subject)
        self.assertIn('Email Test Destination', email.body)
        self.assertIn('confirmation', email.subject.lower())
        
        # Check HTML content
        self.assertIn('Email Test Destination', email.alternatives[0][0])
        self.assertIn('pending review', email.alternatives[0][0].lower())
        
    def test_manager_destination_approval(self):
        """
        Test the manager approval workflow for pending destinations.
        
        Verifies:
        1. Manager can view pending submissions
        2. Manager can approve destinations
        3. Approved destinations are transferred to Destination table
        """
        # Create a pending destination
        pending_destination = PendingDestination.objects.create(
            name='Approval Test Destination',
            slug='approval-test-destination',
            region=self.region,
            description='A destination to test approval workflow',
            created_by=self.guide,
            approval_status=PendingDestination.ApprovalStatus.PENDING
        )
        
        # Login as manager
        self.client.login(username='testmanager', password='password123')
        
        # Access the pending destinations list page
        response = self.client.get(reverse('destinations:admin_pending_destinations'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Approval Test Destination')
        
        # Approve the pending destination
        response = self.client.post(
            reverse('destinations:admin_approve_pending_destination', kwargs={'pk': pending_destination.id}),
            {'approval_note': 'Approved this destination.'},
            follow=True
        )
        
        # Reload the pending destination from database
        pending_destination.refresh_from_db()
        
        # Check if approval status was updated
        self.assertEqual(pending_destination.approval_status, PendingDestination.ApprovalStatus.APPROVED)
        
        # Check if destination was created in main Destination table
        new_destination = Destination.objects.filter(name='Approval Test Destination').first()
        self.assertIsNotNone(new_destination)
        
        # Check if an email notification was sent (1 to guide for approval)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], 'guide@example.com')
        self.assertIn('approved', mail.outbox[0].subject.lower())
