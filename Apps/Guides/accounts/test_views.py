from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import GuideApplication

class GuideApplicationEmailTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.application = GuideApplication.objects.create(
            user=self.user,
            bio='Test bio',
            experience='5 years',
            specialties='Hiking, History',
            phone_number='+1234567890',
            status='PENDING'
        )

    def test_guide_application_email(self):
        """Test that guide application email is sent correctly."""
        from django.core import mail
        
        # Send the email
        from accounts.utils import send_guide_application_confirmation
        result = send_guide_application_confirmation(self.user, self.application)
        
        # Check that the email was sent
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        # Verify email content
        email = mail.outbox[0]
        self.assertEqual(email.subject, 'Your Local Guide Application Submitted Successfully!')
        self.assertIn(self.user.get_full_name(), email.body)
        self.assertEqual(email.to, [self.user.email])
