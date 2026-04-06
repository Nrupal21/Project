"""
Test cases for two-factor authentication in the TravelGuide application.

This module contains comprehensive test cases for the two-factor authentication (2FA)
system, including setup, verification, backup codes, and integration with login flow.
Every test function is thoroughly documented to make understanding
the tests easier for programmers.
"""

from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
import pyotp
import re
import json
from unittest.mock import patch, MagicMock

from accounts.models import Profile, TwoFactorAuth, BackupCode
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class TwoFactorSetupTests(TravelGuideBaseTestCase):
    """
    Tests for two-factor authentication setup in the TravelGuide application.
    
    These tests verify that users can set up two-factor authentication,
    including generating and validating TOTP secrets.
    """
    
    def setUp(self):
        """
        Set up test data for two-factor authentication setup tests.
        
        Extends the base setUp method to include a client and URLs for testing.
        """
        super().setUp()
        
        # Create client for making requests
        self.client = Client()
        
        # URLs for testing
        self.login_url = reverse('accounts:login')
        self.two_factor_setup_url = reverse('accounts:two_factor_setup')
        self.two_factor_confirm_url = reverse('accounts:two_factor_confirm')
        self.two_factor_disable_url = reverse('accounts:two_factor_disable')
        self.profile_url = reverse('accounts:profile')
        
        # Log in as test user
        self.client.login(username='testuser', password='password')
        
    def test_two_factor_setup_page_access(self):
        """
        Test that the two-factor setup page is accessible to authenticated users.
        
        Verifies that authenticated users can access the two-factor setup page.
        """
        response = self.client.get(self.two_factor_setup_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/two_factor_setup.html')
        self.assertContains(response, 'Set Up Two-Factor Authentication')
        
    def test_two_factor_setup_page_unauthenticated(self):
        """
        Test that unauthenticated users cannot access the two-factor setup page.
        
        Verifies that unauthenticated users are redirected to the login page
        when trying to access the two-factor setup page.
        """
        # Log out
        self.client.logout()
        
        response = self.client.get(self.two_factor_setup_url)
        
        # Check that the user is redirected to the login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        
    def test_two_factor_setup_generate_secret(self):
        """
        Test generating a TOTP secret for two-factor authentication.
        
        Verifies that a TOTP secret is generated and stored in the session
        when a user accesses the two-factor setup page.
        """
        response = self.client.get(self.two_factor_setup_url)
        
        # Check that a secret was generated and stored in the session
        self.assertIn('totp_secret', self.client.session)
        secret = self.client.session['totp_secret']
        self.assertEqual(len(secret), 32)  # Standard TOTP secret length
        
        # Check that the QR code URL is included in the response
        self.assertContains(response, 'qrcode')
        self.assertContains(response, secret)
        
    def test_two_factor_confirm_valid_code(self):
        """
        Test confirming two-factor setup with a valid code.
        
        Verifies that a user can confirm two-factor setup with a valid TOTP code.
        """
        # First, access the setup page to generate a secret
        self.client.get(self.two_factor_setup_url)
        secret = self.client.session['totp_secret']
        
        # Generate a valid TOTP code
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()
        
        # Confirm with the valid code
        response = self.client.post(self.two_factor_confirm_url, {
            'code': valid_code
        }, follow=True)
        
        # Check that the setup was successful
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, self.profile_url)
        
        # Check that success message is displayed
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn('two-factor authentication has been enabled', str(messages[0]).lower())
        
        # Check that two-factor auth was enabled for the user
        self.test_user.refresh_from_db()
        self.assertTrue(hasattr(self.test_user, 'twofactorauth'))
        self.assertEqual(self.test_user.twofactorauth.secret, secret)
        
        # Check that backup codes were generated
        self.assertTrue(BackupCode.objects.filter(user=self.test_user).exists())
        self.assertEqual(BackupCode.objects.filter(user=self.test_user).count(), 10)  # Standard number of backup codes
        
    def test_two_factor_confirm_invalid_code(self):
        """
        Test confirming two-factor setup with an invalid code.
        
        Verifies that a user cannot confirm two-factor setup with an invalid TOTP code.
        """
        # First, access the setup page to generate a secret
        self.client.get(self.two_factor_setup_url)
        
        # Use an invalid code
        invalid_code = '123456'  # Not a valid TOTP code for the generated secret
        
        # Confirm with the invalid code
        response = self.client.post(self.two_factor_confirm_url, {
            'code': invalid_code
        })
        
        # Check that the setup failed
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/two_factor_setup.html')
        self.assertContains(response, 'Invalid verification code')
        
        # Check that two-factor auth was not enabled for the user
        self.test_user.refresh_from_db()
        self.assertFalse(hasattr(self.test_user, 'twofactorauth'))
        
    def test_two_factor_confirm_no_secret(self):
        """
        Test confirming two-factor setup without a secret.
        
        Verifies that a user cannot confirm two-factor setup if no secret
        has been generated.
        """
        # Skip the setup page, so no secret is generated
        
        # Try to confirm with a code
        response = self.client.post(self.two_factor_confirm_url, {
            'code': '123456'
        })
        
        # Check that the user is redirected to the setup page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.two_factor_setup_url)
        
    def test_two_factor_disable(self):
        """
        Test disabling two-factor authentication.
        
        Verifies that a user can disable two-factor authentication.
        """
        # First, set up two-factor auth
        self.client.get(self.two_factor_setup_url)
        secret = self.client.session['totp_secret']
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()
        self.client.post(self.two_factor_confirm_url, {'code': valid_code})
        
        # Now disable it
        response = self.client.post(self.two_factor_disable_url, follow=True)
        
        # Check that the disable was successful
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, self.profile_url)
        
        # Check that success message is displayed
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn('two-factor authentication has been disabled', str(messages[0]).lower())
        
        # Check that two-factor auth was disabled for the user
        self.test_user.refresh_from_db()
        self.assertFalse(hasattr(self.test_user, 'twofactorauth'))
        
        # Check that backup codes were deleted
        self.assertFalse(BackupCode.objects.filter(user=self.test_user).exists())


class TwoFactorLoginTests(TravelGuideBaseTestCase):
    """
    Tests for two-factor authentication login flow in the TravelGuide application.
    
    These tests verify that the two-factor authentication login flow works correctly,
    including TOTP verification and backup code usage.
    """
    
    def setUp(self):
        """
        Set up test data for two-factor authentication login tests.
        
        Extends the base setUp method to include a client, URLs, and 2FA setup.
        """
        super().setUp()
        
        # Create client for making requests
        self.client = Client()
        
        # URLs for testing
        self.login_url = reverse('accounts:login')
        self.two_factor_verify_url = reverse('accounts:two_factor_verify')
        self.home_url = reverse('core:home')
        
        # Set up two-factor auth for test user
        self.totp_secret = pyotp.random_base32()
        self.totp = pyotp.TOTP(self.totp_secret)
        
        self.two_factor_auth = TwoFactorAuth.objects.create(
            user=self.test_user,
            secret=self.totp_secret,
            is_active=True
        )
        
        # Generate backup codes
        for _ in range(10):
            BackupCode.objects.create(
                user=self.test_user,
                code=pyotp.random_base32()[:16],
                used=False
            )
        
        # Save one backup code for testing
        self.backup_code = BackupCode.objects.filter(user=self.test_user).first().code
        
    def test_login_with_two_factor(self):
        """
        Test login flow with two-factor authentication.
        
        Verifies that a user with two-factor authentication enabled is
        redirected to the verification page after entering valid credentials.
        """
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'password'
        }, follow=True)
        
        # Check that the user is redirected to the two-factor verification page
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, self.two_factor_verify_url)
        self.assertTemplateUsed(response, 'accounts/two_factor_verify.html')
        
        # Check that the user is not fully authenticated yet
        self.assertFalse(response.context['user'].is_authenticated)
        
        # Check that the user ID is stored in the session for verification
        self.assertIn('two_factor_user_id', self.client.session)
        self.assertEqual(self.client.session['two_factor_user_id'], self.test_user.id)
        
    def test_two_factor_verify_valid_code(self):
        """
        Test two-factor verification with a valid TOTP code.
        
        Verifies that a user can complete the login process by providing
        a valid TOTP code during two-factor verification.
        """
        # First, start the login process
        self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'password'
        })
        
        # Generate a valid TOTP code
        valid_code = self.totp.now()
        
        # Verify with the valid code
        response = self.client.post(self.two_factor_verify_url, {
            'code': valid_code
        }, follow=True)
        
        # Check that the verification was successful
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, self.home_url)
        
        # Check that the user is now fully authenticated
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertEqual(response.context['user'], self.test_user)
        
    def test_two_factor_verify_invalid_code(self):
        """
        Test two-factor verification with an invalid TOTP code.
        
        Verifies that a user cannot complete the login process by providing
        an invalid TOTP code during two-factor verification.
        """
        # First, start the login process
        self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'password'
        })
        
        # Use an invalid code
        invalid_code = '123456'  # Not a valid TOTP code for the user's secret
        
        # Verify with the invalid code
        response = self.client.post(self.two_factor_verify_url, {
            'code': invalid_code
        })
        
        # Check that the verification failed
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/two_factor_verify.html')
        self.assertContains(response, 'Invalid verification code')
        
        # Check that the user is still not fully authenticated
        self.assertFalse('_auth_user_id' in self.client.session)
        
    def test_two_factor_verify_backup_code(self):
        """
        Test two-factor verification with a backup code.
        
        Verifies that a user can complete the login process by providing
        a valid backup code during two-factor verification.
        """
        # First, start the login process
        self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'password'
        })
        
        # Verify with a backup code
        response = self.client.post(self.two_factor_verify_url, {
            'code': self.backup_code
        }, follow=True)
        
        # Check that the verification was successful
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, self.home_url)
        
        # Check that the user is now fully authenticated
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertEqual(response.context['user'], self.test_user)
        
        # Check that the backup code was marked as used
        backup_code = BackupCode.objects.get(user=self.test_user, code=self.backup_code)
        self.assertTrue(backup_code.used)
        
    def test_two_factor_verify_used_backup_code(self):
        """
        Test two-factor verification with a used backup code.
        
        Verifies that a user cannot complete the login process by providing
        a backup code that has already been used.
        """
        # Mark the backup code as used
        backup_code = BackupCode.objects.get(user=self.test_user, code=self.backup_code)
        backup_code.used = True
        backup_code.save()
        
        # First, start the login process
        self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'password'
        })
        
        # Verify with the used backup code
        response = self.client.post(self.two_factor_verify_url, {
            'code': self.backup_code
        })
        
        # Check that the verification failed
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/two_factor_verify.html')
        self.assertContains(response, 'Invalid verification code')
        
        # Check that the user is still not fully authenticated
        self.assertFalse('_auth_user_id' in self.client.session)
        
    def test_two_factor_verify_no_session(self):
        """
        Test two-factor verification without a session.
        
        Verifies that a user cannot access the two-factor verification page
        without first starting the login process.
        """
        # Skip the login step
        
        # Try to access the verification page directly
        response = self.client.get(self.two_factor_verify_url)
        
        # Check that the user is redirected to the login page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.login_url)
        
    def test_two_factor_verify_session_timeout(self):
        """
        Test two-factor verification with a timed-out session.
        
        Verifies that a user is redirected to the login page if the
        two-factor verification session has timed out.
        """
        # First, start the login process
        self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'password'
        })
        
        # Simulate session timeout by clearing the session
        session = self.client.session
        del session['two_factor_user_id']
        session.save()
        
        # Try to access the verification page
        response = self.client.get(self.two_factor_verify_url)
        
        # Check that the user is redirected to the login page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.login_url)


class BackupCodesTests(TravelGuideBaseTestCase):
    """
    Tests for backup codes in the TravelGuide application.
    
    These tests verify that backup codes work correctly for two-factor authentication,
    including generation, regeneration, and usage tracking.
    """
    
    def setUp(self):
        """
        Set up test data for backup codes tests.
        
        Extends the base setUp method to include a client, URLs, and 2FA setup.
        """
        super().setUp()
        
        # Create client for making requests
        self.client = Client()
        
        # URLs for testing
        self.backup_codes_url = reverse('accounts:backup_codes')
        self.regenerate_backup_codes_url = reverse('accounts:regenerate_backup_codes')
        self.profile_url = reverse('accounts:profile')
        
        # Set up two-factor auth for test user
        self.totp_secret = pyotp.random_base32()
        
        self.two_factor_auth = TwoFactorAuth.objects.create(
            user=self.test_user,
            secret=self.totp_secret,
            is_active=True
        )
        
        # Generate backup codes
        for _ in range(10):
            BackupCode.objects.create(
                user=self.test_user,
                code=pyotp.random_base32()[:16],
                used=False
            )
        
        # Log in as test user
        self.client.login(username='testuser', password='password')
        
    def test_backup_codes_page_access(self):
        """
        Test that the backup codes page is accessible to users with 2FA enabled.
        
        Verifies that users with two-factor authentication enabled can
        access the backup codes page.
        """
        response = self.client.get(self.backup_codes_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/backup_codes.html')
        self.assertContains(response, 'Backup Codes')
        
        # Check that all backup codes are displayed
        backup_codes = BackupCode.objects.filter(user=self.test_user)
        for backup_code in backup_codes:
            self.assertContains(response, backup_code.code)
        
    def test_backup_codes_page_no_2fa(self):
        """
        Test that the backup codes page is not accessible to users without 2FA.
        
        Verifies that users without two-factor authentication enabled are
        redirected to the profile page when trying to access the backup codes page.
        """
        # Disable 2FA for the test user
        self.two_factor_auth.delete()
        
        response = self.client.get(self.backup_codes_url)
        
        # Check that the user is redirected to the profile page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.profile_url)
        
    def test_regenerate_backup_codes(self):
        """
        Test regenerating backup codes.
        
        Verifies that a user can regenerate their backup codes,
        replacing all existing codes with new ones.
        """
        # Get the current backup codes
        old_backup_codes = list(BackupCode.objects.filter(user=self.test_user).values_list('code', flat=True))
        
        # Regenerate backup codes
        response = self.client.post(self.regenerate_backup_codes_url, follow=True)
        
        # Check that the regeneration was successful
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, self.backup_codes_url)
        
        # Check that success message is displayed
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn('backup codes have been regenerated', str(messages[0]).lower())
        
        # Check that new backup codes were generated
        new_backup_codes = list(BackupCode.objects.filter(user=self.test_user).values_list('code', flat=True))
        self.assertEqual(len(new_backup_codes), 10)  # Should still have 10 codes
        
        # Check that the new codes are different from the old ones
        self.assertNotEqual(set(old_backup_codes), set(new_backup_codes))
        
    def test_regenerate_backup_codes_no_2fa(self):
        """
        Test regenerating backup codes without 2FA enabled.
        
        Verifies that users without two-factor authentication enabled cannot
        regenerate backup codes.
        """
        # Disable 2FA for the test user
        self.two_factor_auth.delete()
        
        response = self.client.post(self.regenerate_backup_codes_url)
        
        # Check that the user is redirected to the profile page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.profile_url)
        
    def test_backup_code_usage_tracking(self):
        """
        Test that backup code usage is tracked correctly.
        
        Verifies that backup codes are marked as used when they are used
        for two-factor verification.
        """
        # Get a backup code
        backup_code = BackupCode.objects.filter(user=self.test_user, used=False).first()
        
        # Use the backup code for verification
        factory = RequestFactory()
        request = factory.post('/two-factor/verify/', {'code': backup_code.code})
        request.session = {'two_factor_user_id': self.test_user.id}
        
        # Import the view function
        from accounts.views import two_factor_verify
        
        # Call the view function directly
        response = two_factor_verify(request)
        
        # Check that the backup code was marked as used
        backup_code.refresh_from_db()
        self.assertTrue(backup_code.used)


class TwoFactorAPITests(TravelGuideBaseTestCase):
    """
    Tests for two-factor authentication with API access in the TravelGuide application.
    
    These tests verify that two-factor authentication works correctly with API access,
    including token-based authentication and API key verification.
    """
    
    def setUp(self):
        """
        Set up test data for two-factor API tests.
        
        Extends the base setUp method to include API clients and 2FA setup.
        """
        super().setUp()
        
        # Create API client
        self.api_client = APIClient()
        
        # URLs for testing
        self.token_url = reverse('api:token_obtain_pair')
        self.token_verify_url = reverse('api:token_verify')
        self.user_profile_url = reverse('api:user-profile')
        
        # Set up two-factor auth for test user
        self.totp_secret = pyotp.random_base32()
        self.totp = pyotp.TOTP(self.totp_secret)
        
        self.two_factor_auth = TwoFactorAuth.objects.create(
            user=self.test_user,
            secret=self.totp_secret,
            is_active=True
        )
        
        # Generate backup codes
        for _ in range(10):
            BackupCode.objects.create(
                user=self.test_user,
                code=pyotp.random_base32()[:16],
                used=False
            )
        
        # Save one backup code for testing
        self.backup_code = BackupCode.objects.filter(user=self.test_user).first().code
        
    def test_api_token_obtain_with_2fa(self):
        """
        Test obtaining an API token with two-factor authentication.
        
        Verifies that a user with two-factor authentication enabled must
        provide a valid TOTP code to obtain an API token.
        """
        # Try to obtain a token without a TOTP code
        response = self.api_client.post(self.token_url, {
            'username': 'testuser',
            'password': 'password'
        })
        
        # Check that the request was successful but requires 2FA
        self.assertEqual(response.status_code, 200)
        self.assertIn('two_factor_required', response.data)
        self.assertTrue(response.data['two_factor_required'])
        self.assertNotIn('access', response.data)
        
        # Try again with a valid TOTP code
        valid_code = self.totp.now()
        response = self.api_client.post(self.token_url, {
            'username': 'testuser',
            'password': 'password',
            'code': valid_code
        })
        
        # Check that the token was obtained
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
    def test_api_token_obtain_with_backup_code(self):
        """
        Test obtaining an API token with a backup code.
        
        Verifies that a user with two-factor authentication enabled can
        obtain an API token by providing a valid backup code.
        """
        # Try to obtain a token with a backup code
        response = self.api_client.post(self.token_url, {
            'username': 'testuser',
            'password': 'password',
            'code': self.backup_code
        })
        
        # Check that the token was obtained
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Check that the backup code was marked as used
        backup_code = BackupCode.objects.get(user=self.test_user, code=self.backup_code)
        self.assertTrue(backup_code.used)
        
    def test_api_token_obtain_invalid_code(self):
        """
        Test obtaining an API token with an invalid code.
        
        Verifies that a user with two-factor authentication enabled cannot
        obtain an API token by providing an invalid code.
        """
        # Try to obtain a token with an invalid code
        response = self.api_client.post(self.token_url, {
            'username': 'testuser',
            'password': 'password',
            'code': '123456'  # Invalid code
        })
        
        # Check that the token was not obtained
        self.assertEqual(response.status_code, 400)
        self.assertIn('code', response.data)
        self.assertIn('Invalid verification code', str(response.data['code']))
        
    def test_api_access_with_token(self):
        """
        Test accessing API endpoints with a token after 2FA verification.
        
        Verifies that a user can access API endpoints with a token obtained
        after two-factor verification.
        """
        # First, obtain a token with 2FA
        valid_code = self.totp.now()
        response = self.api_client.post(self.token_url, {
            'username': 'testuser',
            'password': 'password',
            'code': valid_code
        })
        
        access_token = response.data['access']
        
        # Use the token to access a protected endpoint
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.api_client.get(self.user_profile_url)
        
        # Check that access is granted
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'testuser')
        
    def test_api_token_verify(self):
        """
        Test verifying an API token obtained after 2FA.
        
        Verifies that a token obtained after two-factor verification
        can be verified using the token verify endpoint.
        """
        # First, obtain a token with 2FA
        valid_code = self.totp.now()
        response = self.api_client.post(self.token_url, {
            'username': 'testuser',
            'password': 'password',
            'code': valid_code
        })
        
        access_token = response.data['access']
        
        # Verify the token
        response = self.api_client.post(self.token_verify_url, {
            'token': access_token
        })
        
        # Check that the token is valid
        self.assertEqual(response.status_code, 200)
        
    def test_api_token_verify_invalid(self):
        """
        Test verifying an invalid API token.
        
        Verifies that an invalid token cannot be verified using
        the token verify endpoint.
        """
        # Try to verify an invalid token
        response = self.api_client.post(self.token_verify_url, {
            'token': 'invalid-token'
        })
        
        # Check that the token is invalid
        self.assertEqual(response.status_code, 401)
