"""
Test cases for the security app.

This module contains comprehensive test cases for all functionality
in the security app, including two-factor authentication, security settings,
and related utilities. Every test function is thoroughly documented to make 
understanding the tests easier for programmers.
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
import pyotp

from security.models import TOTPDevice, SecurityQuestion, SecurityAnswer
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class TOTPDeviceModelTests(TravelGuideBaseTestCase):
    """
    Tests for the TOTPDevice model in the security app.
    
    These tests verify that TOTPDevice objects can be created correctly,
    and that their methods work as expected. Each test focuses on a 
    specific aspect of the TOTPDevice model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for TOTPDevice tests.
        
        Extends the base setUp method to include a TOTP device for testing.
        """
        super().setUp()
        
        # Generate a secret key for TOTP
        self.secret_key = pyotp.random_base32()
        
        # Create a TOTP device for the test user
        self.totp_device = TOTPDevice.objects.create(
            user=self.test_user,
            name='Test Device',
            key=self.secret_key,
            confirmed=True
        )
    
    def test_totp_device_creation(self):
        """
        Test that a TOTPDevice can be created with the expected attributes.
        
        Verifies that the TOTPDevice model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Generate a new secret key
        secret_key = pyotp.random_base32()
        
        # Create a TOTP device for the admin user
        totp_device = TOTPDevice.objects.create(
            user=self.admin_user,
            name='Admin Device',
            key=secret_key,
            confirmed=False
        )
        
        # Verify the TOTP device was created with the correct attributes
        self.assertEqual(totp_device.user, self.admin_user)
        self.assertEqual(totp_device.name, 'Admin Device')
        self.assertEqual(totp_device.key, secret_key)
        self.assertFalse(totp_device.confirmed)
        
    def test_totp_device_str_method(self):
        """
        Test the string representation of a TOTPDevice object.
        
        Verifies that the __str__ method returns the expected string,
        which should include the device name and username.
        """
        expected_str = f"Test Device (testuser)"
        self.assertEqual(str(self.totp_device), expected_str)
        
    def test_totp_device_verify_token(self):
        """
        Test the verify_token method of the TOTPDevice model.
        
        Verifies that the verify_token method correctly validates TOTP tokens
        generated with the device's secret key.
        """
        # Create a TOTP object with the secret key
        totp = pyotp.TOTP(self.secret_key)
        
        # Generate a valid token
        valid_token = totp.now()
        
        # Verify that the token is valid
        self.assertTrue(self.totp_device.verify_token(valid_token))
        
        # Test with an invalid token
        invalid_token = '000000'
        self.assertFalse(self.totp_device.verify_token(invalid_token))
        
    def test_totp_device_generate_qr_code(self):
        """
        Test the generate_qr_code method of the TOTPDevice model.
        
        Verifies that the generate_qr_code method returns a valid QR code
        data URI that can be used for setting up 2FA in authenticator apps.
        """
        # Generate a QR code
        qr_code = self.totp_device.generate_qr_code()
        
        # Verify that the QR code is not None
        self.assertIsNotNone(qr_code)
        
        # Verify that the QR code is a data URI
        self.assertTrue(qr_code.startswith('data:image/png;base64,'))


class SecurityQuestionModelTests(TravelGuideBaseTestCase):
    """
    Tests for the SecurityQuestion model in the security app.
    
    These tests verify that SecurityQuestion objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the SecurityQuestion model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for SecurityQuestion tests.
        
        Extends the base setUp method to include security questions for testing.
        """
        super().setUp()
        
        # Create security questions
        self.question1 = SecurityQuestion.objects.create(
            question_text="What was the name of your first pet?"
        )
        
        self.question2 = SecurityQuestion.objects.create(
            question_text="In which city were you born?"
        )
    
    def test_security_question_creation(self):
        """
        Test that a SecurityQuestion can be created with the expected attributes.
        
        Verifies that the SecurityQuestion model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        question = SecurityQuestion.objects.create(
            question_text="What is your mother's maiden name?"
        )
        
        # Verify the security question was created with the correct attributes
        self.assertEqual(question.question_text, "What is your mother's maiden name?")
        
    def test_security_question_str_method(self):
        """
        Test the string representation of a SecurityQuestion object.
        
        Verifies that the __str__ method returns the expected string,
        which should be the question text.
        """
        self.assertEqual(str(self.question1), "What was the name of your first pet?")


class SecurityAnswerModelTests(TravelGuideBaseTestCase):
    """
    Tests for the SecurityAnswer model in the security app.
    
    These tests verify that SecurityAnswer objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the SecurityAnswer model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for SecurityAnswer tests.
        
        Extends the base setUp method to include security questions and answers for testing.
        """
        super().setUp()
        
        # Create security questions
        self.question1 = SecurityQuestion.objects.create(
            question_text="What was the name of your first pet?"
        )
        
        self.question2 = SecurityQuestion.objects.create(
            question_text="In which city were you born?"
        )
        
        # Create security answers for the test user
        self.answer1 = SecurityAnswer.objects.create(
            user=self.test_user,
            question=self.question1,
            answer="Fluffy"
        )
        
        self.answer2 = SecurityAnswer.objects.create(
            user=self.test_user,
            question=self.question2,
            answer="New York"
        )
    
    def test_security_answer_creation(self):
        """
        Test that a SecurityAnswer can be created with the expected attributes.
        
        Verifies that the SecurityAnswer model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a security answer for the admin user
        answer = SecurityAnswer.objects.create(
            user=self.admin_user,
            question=self.question1,
            answer="Rex"
        )
        
        # Verify the security answer was created with the correct attributes
        self.assertEqual(answer.user, self.admin_user)
        self.assertEqual(answer.question, self.question1)
        self.assertEqual(answer.answer, "Rex")
        
    def test_security_answer_str_method(self):
        """
        Test the string representation of a SecurityAnswer object.
        
        Verifies that the __str__ method returns the expected string,
        which should include the username and question.
        """
        expected_str = f"Answer by testuser for 'What was the name of your first pet?'"
        self.assertEqual(str(self.answer1), expected_str)
        
    def test_security_answer_verify(self):
        """
        Test the verify method of the SecurityAnswer model.
        
        Verifies that the verify method correctly validates answers
        by comparing them to the stored answer.
        """
        # Test with the correct answer
        self.assertTrue(self.answer1.verify("Fluffy"))
        
        # Test with an incorrect answer
        self.assertFalse(self.answer1.verify("Rex"))
        
        # Test with case-insensitive matching
        self.assertTrue(self.answer1.verify("fluffy"))
        
        # Test with extra whitespace
        self.assertTrue(self.answer1.verify(" Fluffy "))


class SecurityViewTests(TravelGuideBaseTestCase):
    """
    Tests for the views in the security app.
    
    These tests verify that the views render the correct templates,
    contain the expected context data, and handle form submissions correctly.
    Each test focuses on a specific view or aspect of view functionality.
    """
    
    def setUp(self):
        """
        Set up test data for security view tests.
        
        Extends the base setUp method to include necessary security data.
        """
        super().setUp()
        
        # Generate a secret key for TOTP
        self.secret_key = pyotp.random_base32()
        
        # Create security questions
        self.question1 = SecurityQuestion.objects.create(
            question_text="What was the name of your first pet?"
        )
        
        self.question2 = SecurityQuestion.objects.create(
            question_text="In which city were you born?"
        )
        
        # Log in the test user
        self.login_test_user()
    
    def test_security_dashboard_view(self):
        """
        Test the security dashboard view.
        
        Verifies that the security dashboard view returns a 200 status code,
        uses the correct template, and includes the expected context data.
        """
        response = self.client.get(reverse('security:dashboard'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'security/dashboard.html')
        
        # Check that the user is in the context
        self.assertEqual(response.context['user'], self.test_user)
        
    def test_setup_2fa_view(self):
        """
        Test the setup 2FA view.
        
        Verifies that the setup 2FA view returns a 200 status code,
        uses the correct template, and allows setting up 2FA.
        """
        response = self.client.get(reverse('security:setup_2fa'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'security/setup_2fa.html')
        
        # Check that a secret key is generated and in the context
        self.assertIn('secret_key', response.context)
        self.assertIn('qr_code', response.context)
        
    def test_verify_2fa_view(self):
        """
        Test the verify 2FA view.
        
        Verifies that the verify 2FA view returns a 200 status code,
        uses the correct template, and allows verifying 2FA setup.
        """
        # Create a TOTP device for the test user
        totp_device = TOTPDevice.objects.create(
            user=self.test_user,
            name='Test Device',
            key=self.secret_key,
            confirmed=False
        )
        
        # Store the device ID in the session
        session = self.client.session
        session['totp_device_id'] = totp_device.id
        session.save()
        
        # Get the verify 2FA page
        response = self.client.get(reverse('security:verify_2fa'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'security/verify_2fa.html')
        
        # Generate a valid token
        totp = pyotp.TOTP(self.secret_key)
        valid_token = totp.now()
        
        # Submit the verification form with a valid token
        response = self.client.post(reverse('security:verify_2fa'), {
            'token': valid_token
        })
        
        # Check that the verification was successful and redirected
        self.assertEqual(response.status_code, 302)  # Redirect status code
        
        # Refresh the TOTP device from the database
        totp_device.refresh_from_db()
        
        # Check that the device is now confirmed
        self.assertTrue(totp_device.confirmed)
        
    def test_disable_2fa_view(self):
        """
        Test the disable 2FA view.
        
        Verifies that the disable 2FA view allows disabling 2FA
        and redirects appropriately.
        """
        # Create a confirmed TOTP device for the test user
        totp_device = TOTPDevice.objects.create(
            user=self.test_user,
            name='Test Device',
            key=self.secret_key,
            confirmed=True
        )
        
        # Get the disable 2FA page
        response = self.client.get(reverse('security:disable_2fa'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'security/disable_2fa.html')
        
        # Submit the disable form
        response = self.client.post(reverse('security:disable_2fa'), {
            'confirm': 'yes'
        })
        
        # Check that the 2FA was disabled and redirected
        self.assertEqual(response.status_code, 302)  # Redirect status code
        
        # Check that the TOTP device was deleted
        self.assertFalse(TOTPDevice.objects.filter(id=totp_device.id).exists())
        
    def test_security_questions_view(self):
        """
        Test the security questions view.
        
        Verifies that the security questions view returns a 200 status code,
        uses the correct template, and allows setting up security questions.
        """
        response = self.client.get(reverse('security:security_questions'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'security/security_questions.html')
        
        # Check that the questions are in the context
        self.assertIn('questions', response.context)
        
        # Submit the security questions form
        response = self.client.post(reverse('security:security_questions'), {
            f'question_{self.question1.id}': 'Fluffy',
            f'question_{self.question2.id}': 'New York'
        })
        
        # Check that the security questions were saved and redirected
        self.assertEqual(response.status_code, 302)  # Redirect status code
        
        # Check that the security answers were created
        self.assertTrue(SecurityAnswer.objects.filter(
            user=self.test_user,
            question=self.question1,
            answer='Fluffy'
        ).exists())
        
        self.assertTrue(SecurityAnswer.objects.filter(
            user=self.test_user,
            question=self.question2,
            answer='New York'
        ).exists())
        
    def test_verify_security_questions_view(self):
        """
        Test the verify security questions view.
        
        Verifies that the verify security questions view returns a 200 status code,
        uses the correct template, and allows verifying security questions.
        """
        # Create security answers for the test user
        SecurityAnswer.objects.create(
            user=self.test_user,
            question=self.question1,
            answer="Fluffy"
        )
        
        SecurityAnswer.objects.create(
            user=self.test_user,
            question=self.question2,
            answer="New York"
        )
        
        # Get the verify security questions page
        response = self.client.get(reverse('security:verify_questions'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'security/verify_questions.html')
        
        # Check that the user's questions are in the context
        self.assertIn('user_questions', response.context)
        
        # Submit the verification form with correct answers
        response = self.client.post(reverse('security:verify_questions'), {
            f'answer_{self.question1.id}': 'Fluffy',
            f'answer_{self.question2.id}': 'New York'
        })
        
        # Check that the verification was successful and redirected
        self.assertEqual(response.status_code, 302)  # Redirect status code
