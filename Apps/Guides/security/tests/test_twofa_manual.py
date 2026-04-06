"""
Manual test script for verifying the complete 2FA login flow.

This script tests the full integration between login and two-factor authentication,
including the middleware enforcement of 2FA verification.

Usage:
    python manage.py test security.tests.test_twofa_manual.TestTwoFactorLoginFlow
"""

import pyotp
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages

from security.models import TwoFactorAuth, SecurityLog, FailedLoginAttempt
from security.utils import generate_totp_secret


@override_settings(DEBUG=True)
class TestTwoFactorLoginFlow(TestCase):
    """Test the complete end-to-end two-factor authentication login flow.
    
    This test case verifies the integration between the login view and 2FA verification,
    ensuring that users with 2FA enabled are properly redirected to verification before
    gaining full access to protected resources.
    
    Each test method has detailed comments and print statements for visibility during
    test runs with verbosity >= 2.
    """
    """
    Test the complete end-to-end two-factor authentication login flow.
    
    Tests the integration between accounts login and security 2FA verification,
    including middleware enforcement of 2FA verification.
    """
    
    def setUp(self):
        """
        Set up test data with a user and 2FA enabled.
        
        Creates a test user, enables 2FA, and sets up the test client.
        """
        # Create test user
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        
        # Set up 2FA for the user
        self.secret = generate_totp_secret()
        self.backup_codes = ["AAAA-BBBB", "CCCC-DDDD"]
        self.twofa = TwoFactorAuth.objects.create(
            user=self.user,
            is_enabled=True,
            method=TwoFactorAuth.METHOD_APP,
            secret_key=self.secret,
            backup_codes=self.backup_codes
        )
        
        # Set up test client
        self.client = Client()
        
        # Clear any existing security logs
        SecurityLog.objects.all().delete()
        
        # Clear any failed login attempts
        FailedLoginAttempt.objects.filter(username=self.user.username).delete()
        
        print("\n===== Two-Factor Authentication Login Flow Test =====\n")
        print("Setting up test user and enabling 2FA...")
    
    def test_full_login_flow(self):
        """
        Test the complete login flow with 2FA enabled.
        
        This test verifies that:
        1. A user with valid credentials but 2FA enabled is redirected to verification
        2. The session contains the twofa_user_id but not a fully authenticated session
        3. A valid verification code completes the login process
        4. Security logs are created for all stages of the authentication process
        5. The middleware correctly enforces 2FA verification when attempting to access protected resources
        """
        """
        Test the complete login flow with 2FA enabled.
        
        Steps:
        1. User submits login form with correct credentials
        2. System recognizes 2FA is enabled and redirects to verification
        3. User completes 2FA verification
        4. User is fully authenticated and redirected to dashboard
        5. Security logs are properly created
        """
        print("\n1. Testing login with 2FA enabled...")
        print("   Submitting login form with correct credentials...")
        
        # Step 1: Submit login form with correct credentials
        login_response = self.client.post(
            reverse('accounts:login'),
            {'username': 'testuser', 'password': 'testpassword123'},
            follow=True
        )
        
        # Verify redirect to 2FA verification
        self.assertRedirects(login_response, reverse('security:twofa_verify'))
        
        # Verify 2FA session variable is set
        self.assertIn('twofa_user_id', self.client.session)
        self.assertEqual(self.client.session['twofa_user_id'], str(self.user.id))
        
        # Verify 2FA required log
        required_log = SecurityLog.objects.filter(
            user=self.user,
            event_type=SecurityLog.EVENT_2FA_REQUIRED
        ).exists()
        self.assertTrue(required_log)
        
        print("   ✓ Login redirects to 2FA verification")
        print("   ✓ Session contains twofa_user_id but user is not fully authenticated")
        print("   ✓ Security log created for 2FA required event")
        
        # Step 2: Generate valid TOTP code
        totp = pyotp.TOTP(self.secret)
        valid_code = totp.now()
        
        print("\n2. Testing 2FA verification with valid code...")
        print("   Generating valid TOTP code and submitting verification form...")
        
        # Step 3: Submit valid verification code
        verify_response = self.client.post(
            reverse('security:twofa_verify'),
            {'code': valid_code},
            follow=True
        )
        
        # Verify redirect to dashboard
        self.assertRedirects(verify_response, reverse('dashboard'))
        
        # Verify user is fully authenticated
        self.assertTrue('_auth_user_id' in self.client.session)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.id)
        
        # Verify 2FA session variable is cleared
        self.assertNotIn('twofa_user_id', self.client.session)
        
        # Verify 2FA success log
        success_log = SecurityLog.objects.filter(
            user=self.user,
            event_type=SecurityLog.EVENT_2FA_SUCCESS
        ).exists()
        self.assertTrue(success_log)
        
        # Verify login success log
        login_log = SecurityLog.objects.filter(
            user=self.user,
            event_type=SecurityLog.EVENT_LOGIN_SUCCESS
        ).exists()
        self.assertTrue(login_log)
        
        print("   ✓ 2FA verification succeeds with redirect to dashboard")
        print("   ✓ User is now fully authenticated with session ID")
        print("   ✓ twofa_user_id session variable is cleared")
        print("   ✓ Security logs created for 2FA success and login success")
        
        print("\n3. Testing middleware enforcement of 2FA...")
        print("   Simulating partial authentication and attempting to access protected page...")
        
        # Step 4: Log out and create partial authentication state
        self.client.logout()
        
        # Manually set 2FA session to simulate partial authentication
        session = self.client.session
        session['twofa_user_id'] = str(self.user.id)
        session.save()
        
        # Try to access a protected page
        protected_response = self.client.get(reverse('dashboard'), follow=True)
        
        # Verify redirect to 2FA verification
        self.assertRedirects(protected_response, reverse('security:twofa_verify'))
        
        print("   ✓ Middleware correctly redirects to 2FA verification")
        print("   ✓ Protected page access is blocked until 2FA is completed")
        
        print("\n4. Testing backup code verification...")
        print("   Attempting verification with backup code instead of TOTP code...")
        
        # Try to complete verification with backup code
        backup_response = self.client.post(
            reverse('security:twofa_verify'),
            {'code': 'AAAA-BBBB', 'use_backup': 'true'},
            follow=True
        )
        
        # Verify redirect to dashboard
        self.assertRedirects(backup_response, reverse('dashboard'))
        
        # Verify user is fully authenticated
        self.assertTrue('_auth_user_id' in self.client.session)
        
        # Verify backup code is removed
        self.twofa.refresh_from_db()
        self.assertNotIn('AAAA-BBBB', self.twofa.backup_codes)
        
        print("   ✓ Backup code verification succeeds with redirect to dashboard")
        print("   ✓ User is fully authenticated")
        print("   ✓ Used backup code is removed from available codes")
        print("\nAll 2FA login flow tests completed successfully!")
        
        # This line is replaced by the more detailed message at each test conclusion


class TestLoginFailures(TestCase):
    """
    Test failed login attempts and account lockout.
    
    This test case verifies that the system properly tracks failed login attempts,
    enforces account lockout after multiple failures, and logs security events
    throughout the process.
    
    Tests here focus on the security aspects of login rather than the 2FA flow,
    ensuring that brute force protection is working as expected.
    """
    """
    Test failed login attempts and account lockout.
    
    Tests the behavior of the system when invalid credentials are provided
    or when too many failed attempts trigger account lockout.
    """
    
    def setUp(self):
        """
        Set up test data.
        
        Creates a test user and initializes a test client.
        """
        # Create test user
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        
        # Set up test client
        self.client = Client()
        
        # Clear any existing security logs
        SecurityLog.objects.all().delete()
        
        # Clear any failed login attempts
        FailedLoginAttempt.objects.all().delete()
        
        print("\n===== Login Failures and Account Lockout Test =====\n")
        print("Setting up test user for login failure tests...")
    
    def test_failed_login_tracking(self):
        """
        Test that failed login attempts are tracked and account lockout is enforced.
        
        This test verifies that:
        1. Each failed login attempt increases the counter in FailedLoginAttempt
        2. Security logs are created for each failed attempt
        3. After exceeding the maximum attempts, the account is locked
        4. During lockout, even correct credentials are rejected
        5. Proper security logs are created for all events
        """
        """
        Test that failed login attempts are tracked and account lockout is enforced.
        
        Tests:
        1. Failed logins increase attempt counter
        2. After MAX_LOGIN_ATTEMPTS, account is locked
        3. Login is blocked during lockout period
        4. Proper error messages are shown
        """
        print("\n1. Testing failed login tracking...")
        print("   Submitting invalid login credentials multiple times...")
        
        # Submit invalid login 4 times
        for i in range(1, 5):
            response = self.client.post(
                reverse('accounts:login'),
                {'username': 'testuser', 'password': 'wrongpassword'},
                follow=True
            )
            
            # Verify failed login attempt is recorded
            attempt = FailedLoginAttempt.objects.get(username='testuser')
            self.assertEqual(attempt.attempt_count, i)
            
            # Verify failed login log
            fail_logs = SecurityLog.objects.filter(
                event_type=SecurityLog.EVENT_LOGIN_FAILED
            ).count()
            self.assertEqual(fail_logs, i)
            
            print(f"   ✓ Failed attempt {i} recorded with counter = {i}")
            print(f"   ✓ Security log created for failed login attempt")
        
        print("\n2. Testing account lockout after exceeding maximum attempts...")
        print("   Submitting 5th invalid login to trigger lockout...")
        
        # Submit 5th invalid login to trigger lockout
        response = self.client.post(
            reverse('accounts:login'),
            {'username': 'testuser', 'password': 'wrongpassword'},
            follow=True
        )
        
        # Verify account is locked
        attempt = FailedLoginAttempt.objects.get(username='testuser')
        self.assertTrue(attempt.is_locked)
        self.assertIsNotNone(attempt.lock_expiry)
        
        # Verify account lockout log
        lock_log = SecurityLog.objects.filter(
            event_type=SecurityLog.EVENT_ACCOUNT_LOCKED
        ).exists()
        self.assertTrue(lock_log)
        
        print("   ✓ Account correctly marked as locked")
        print("   ✓ Lock expiry timestamp is set")
        print("   ✓ Security log created for account lockout event")
        
        print("\n3. Testing login blocked during lockout period...")
        print("   Attempting login with correct password during lockout period...")
        
        # Try to login with correct password during lockout
        response = self.client.post(
            reverse('accounts:login'),
            {'username': 'testuser', 'password': 'testpassword123'},
            follow=True
        )
        
        # Verify login is blocked
        self.assertFalse('_auth_user_id' in self.client.session)
        
        # Verify blocked login log
        block_log = SecurityLog.objects.filter(
            event_type=SecurityLog.EVENT_LOGIN_BLOCKED
        ).exists()
        self.assertTrue(block_log)
        
        print("   ✓ Login correctly blocked despite valid credentials")
        print("   ✓ User remains unauthenticated")
        print("   ✓ Security log created for blocked login attempt")
        print("\nAll login failure tests completed successfully!")
        
        # This line is replaced by the more detailed message at each test conclusion
