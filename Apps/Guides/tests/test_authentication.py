"""
Test cases for authentication functionality in the TravelGuide application.

This module contains comprehensive test cases for user authentication,
including login, logout, registration, password reset, and account management.
Every test function is thoroughly documented to make understanding
the tests easier for programmers.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
import re

from accounts.forms import (
    LoginForm,
    RegistrationForm,
    PasswordResetForm,
    PasswordChangeForm,
    ProfileUpdateForm
)
from accounts.models import Profile
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class AuthenticationTests(TravelGuideBaseTestCase):
    """
    Tests for authentication functionality in the TravelGuide application.
    
    These tests verify that user authentication works correctly,
    including login, logout, and session management.
    """
    
    def setUp(self):
        """
        Set up test data for authentication tests.
        
        Extends the base setUp method to include additional test users.
        """
        super().setUp()
        
        # Create additional test users
        self.inactive_user = User.objects.create_user(
            username='inactive',
            email='inactive@example.com',
            password='password123',
            is_active=False
        )
        
        # Create client for making requests
        self.client = Client()
        
        # URLs for authentication views
        self.login_url = reverse('accounts:login')
        self.logout_url = reverse('accounts:logout')
        self.register_url = reverse('accounts:register')
        self.password_reset_url = reverse('accounts:password_reset')
        self.profile_url = reverse('accounts:profile')
        
    def test_login_view_get(self):
        """
        Test that the login page loads successfully.
        
        Verifies that the login page returns a 200 OK status code
        and contains the login form.
        """
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')
        self.assertIsInstance(response.context['form'], LoginForm)
        self.assertContains(response, '<form')
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password"')
        self.assertContains(response, 'type="submit"')
        
    def test_login_successful(self):
        """
        Test successful user login.
        
        Verifies that a user can log in with valid credentials
        and is redirected to the home page.
        """
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'password'
        }, follow=True)
        
        # Check that the login was successful
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertEqual(response.context['user'].username, 'testuser')
        
        # Check that the user was redirected to the home page
        self.assertRedirects(response, reverse('core:home'))
        
        # Check that success message is displayed
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn('successfully logged in', str(messages[0]).lower())
        
    def test_login_invalid_credentials(self):
        """
        Test login with invalid credentials.
        
        Verifies that a user cannot log in with invalid credentials
        and an appropriate error message is displayed.
        """
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        
        # Check that the login failed
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)
        
        # Check that error message is displayed
        self.assertFormError(response, 'form', None, 'Please enter a correct username and password.')
        
    def test_login_inactive_user(self):
        """
        Test login with inactive user account.
        
        Verifies that an inactive user cannot log in and
        an appropriate error message is displayed.
        """
        response = self.client.post(self.login_url, {
            'username': 'inactive',
            'password': 'password123'
        })
        
        # Check that the login failed
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)
        
        # Check that error message is displayed
        self.assertFormError(response, 'form', None, 'This account is inactive.')
        
    def test_logout(self):
        """
        Test user logout.
        
        Verifies that a logged-in user can log out and
        is redirected to the home page.
        """
        # First, log in
        self.client.login(username='testuser', password='password')
        
        # Then, log out
        response = self.client.get(self.logout_url, follow=True)
        
        # Check that the logout was successful
        self.assertFalse(response.context['user'].is_authenticated)
        
        # Check that the user was redirected to the home page
        self.assertRedirects(response, reverse('core:home'))
        
        # Check that success message is displayed
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn('successfully logged out', str(messages[0]).lower())
        
    def test_login_redirect(self):
        """
        Test login with next parameter.
        
        Verifies that a user is redirected to the specified page
        after logging in when a 'next' parameter is provided.
        """
        # Try to access a page that requires login
        response = self.client.get(self.profile_url)
        
        # Should be redirected to login page with next parameter
        self.assertRedirects(response, f"{self.login_url}?next={self.profile_url}")
        
        # Log in with next parameter
        response = self.client.post(f"{self.login_url}?next={self.profile_url}", {
            'username': 'testuser',
            'password': 'password'
        }, follow=True)
        
        # Check that the login was successful
        self.assertTrue(response.context['user'].is_authenticated)
        
        # Check that the user was redirected to the specified page
        self.assertEqual(response.redirect_chain[-1][0], self.profile_url)
        
    def test_login_remember_me(self):
        """
        Test login with remember me option.
        
        Verifies that the session expiry is set correctly when
        the remember me option is selected.
        """
        # Login with remember me unchecked (default)
        self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'password'
        })
        
        # Check session expiry (should be 0, meaning it expires when browser closes)
        self.assertEqual(self.client.session.get_expiry_age(), 0)
        
        # Clear session
        self.client.logout()
        
        # Login with remember me checked
        self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'password',
            'remember_me': True
        })
        
        # Check session expiry (should be 2 weeks = 1209600 seconds)
        self.assertEqual(self.client.session.get_expiry_age(), 1209600)


class RegistrationTests(TravelGuideBaseTestCase):
    """
    Tests for user registration functionality in the TravelGuide application.
    
    These tests verify that user registration works correctly,
    including form validation and account creation.
    """
    
    def setUp(self):
        """
        Set up test data for registration tests.
        
        Extends the base setUp method to include a client for making requests.
        """
        super().setUp()
        
        # Create client for making requests
        self.client = Client()
        
        # URLs for registration views
        self.register_url = reverse('accounts:register')
        
    def test_register_view_get(self):
        """
        Test that the registration page loads successfully.
        
        Verifies that the registration page returns a 200 OK status code
        and contains the registration form.
        """
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')
        self.assertIsInstance(response.context['form'], RegistrationForm)
        self.assertContains(response, '<form')
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'name="password1"')
        self.assertContains(response, 'name="password2"')
        self.assertContains(response, 'type="submit"')
        
    def test_register_successful(self):
        """
        Test successful user registration.
        
        Verifies that a user can register with valid information
        and is redirected to the login page.
        """
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'NewPassword123',
            'password2': 'NewPassword123'
        }, follow=True)
        
        # Check that the registration was successful
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('accounts:login'))
        
        # Check that the user was created
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
        # Check that a profile was created for the user
        user = User.objects.get(username='newuser')
        self.assertTrue(hasattr(user, 'profile'))
        
        # Check that success message is displayed
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn('successfully registered', str(messages[0]).lower())
        
    def test_register_duplicate_username(self):
        """
        Test registration with duplicate username.
        
        Verifies that a user cannot register with a username
        that is already taken.
        """
        response = self.client.post(self.register_url, {
            'username': 'testuser',  # Already exists
            'email': 'newuser@example.com',
            'password1': 'NewPassword123',
            'password2': 'NewPassword123'
        })
        
        # Check that the registration failed
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'username', 'A user with that username already exists.')
        
    def test_register_duplicate_email(self):
        """
        Test registration with duplicate email.
        
        Verifies that a user cannot register with an email
        that is already taken.
        """
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'testuser@example.com',  # Already exists
            'password1': 'NewPassword123',
            'password2': 'NewPassword123'
        })
        
        # Check that the registration failed
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email', 'This email address is already in use.')
        
    def test_register_password_mismatch(self):
        """
        Test registration with mismatched passwords.
        
        Verifies that a user cannot register when the password
        confirmation doesn't match the password.
        """
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'NewPassword123',
            'password2': 'DifferentPassword123'
        })
        
        # Check that the registration failed
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'password2', "The two password fields didn't match.")
        
    def test_register_weak_password(self):
        """
        Test registration with weak password.
        
        Verifies that a user cannot register with a password
        that doesn't meet the strength requirements.
        """
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'password',  # Too common
            'password2': 'password'
        })
        
        # Check that the registration failed
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'password1', 'This password is too common.')
        
    def test_register_invalid_email(self):
        """
        Test registration with invalid email.
        
        Verifies that a user cannot register with an email
        that is not properly formatted.
        """
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'not-an-email',
            'password1': 'NewPassword123',
            'password2': 'NewPassword123'
        })
        
        # Check that the registration failed
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email', 'Enter a valid email address.')


class PasswordResetTests(TravelGuideBaseTestCase):
    """
    Tests for password reset functionality in the TravelGuide application.
    
    These tests verify that password reset works correctly,
    including sending reset emails and setting new passwords.
    """
    
    def setUp(self):
        """
        Set up test data for password reset tests.
        
        Extends the base setUp method to include a client for making requests.
        """
        super().setUp()
        
        # Create client for making requests
        self.client = Client()
        
        # URLs for password reset views
        self.password_reset_url = reverse('accounts:password_reset')
        self.password_reset_done_url = reverse('accounts:password_reset_done')
        self.password_reset_confirm_url_name = 'accounts:password_reset_confirm'
        self.password_reset_complete_url = reverse('accounts:password_reset_complete')
        
    def test_password_reset_view_get(self):
        """
        Test that the password reset page loads successfully.
        
        Verifies that the password reset page returns a 200 OK status code
        and contains the password reset form.
        """
        response = self.client.get(self.password_reset_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/password_reset.html')
        self.assertIsInstance(response.context['form'], PasswordResetForm)
        self.assertContains(response, '<form')
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'type="submit"')
        
    def test_password_reset_valid_email(self):
        """
        Test password reset with valid email.
        
        Verifies that a password reset email is sent when a valid
        email address is provided and the user is redirected to
        the password reset done page.
        """
        response = self.client.post(self.password_reset_url, {
            'email': 'testuser@example.com'
        }, follow=True)
        
        # Check that the user was redirected to the password reset done page
        self.assertRedirects(response, self.password_reset_done_url)
        
        # Check that an email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['testuser@example.com'])
        self.assertIn('Password Reset', mail.outbox[0].subject)
        
    def test_password_reset_invalid_email(self):
        """
        Test password reset with invalid email.
        
        Verifies that no password reset email is sent when an invalid
        email address is provided and an appropriate error message is displayed.
        """
        response = self.client.post(self.password_reset_url, {
            'email': 'nonexistent@example.com'
        })
        
        # Check that the form was invalid
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email', 'There is no user registered with this email address.')
        
        # Check that no email was sent
        self.assertEqual(len(mail.outbox), 0)
        
    def test_password_reset_confirm(self):
        """
        Test password reset confirmation.
        
        Verifies that a user can reset their password using the
        link sent in the password reset email.
        """
        # Send password reset email
        self.client.post(self.password_reset_url, {
            'email': 'testuser@example.com'
        })
        
        # Get the password reset link from the email
        email_body = mail.outbox[0].body
        reset_link_match = re.search(r'http://[^/]+(/[^/\s]+/[^/\s]+/[^/\s]+/[^/\s]+/)', email_body)
        self.assertIsNotNone(reset_link_match, "Password reset link not found in email")
        reset_link = reset_link_match.group(1)
        
        # Visit the password reset confirmation page
        response = self.client.get(reset_link)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/password_reset_confirm.html')
        
        # Extract the form data
        post_data = {
            'new_password1': 'NewPassword456',
            'new_password2': 'NewPassword456'
        }
        
        # Submit the new password
        response = self.client.post(reset_link, post_data, follow=True)
        
        # Check that the user was redirected to the password reset complete page
        self.assertRedirects(response, self.password_reset_complete_url)
        
        # Check that the password was changed
        self.test_user.refresh_from_db()
        self.assertTrue(self.test_user.check_password('NewPassword456'))
        
    def test_password_reset_confirm_invalid_link(self):
        """
        Test password reset confirmation with invalid link.
        
        Verifies that a user cannot reset their password using an
        invalid or expired password reset link.
        """
        # Generate an invalid password reset link
        uid = urlsafe_base64_encode(force_bytes(999999))  # Non-existent user ID
        token = default_token_generator.make_token(self.test_user)
        invalid_link = reverse(self.password_reset_confirm_url_name, kwargs={
            'uidb64': uid,
            'token': token
        })
        
        # Visit the invalid password reset confirmation page
        response = self.client.get(invalid_link)
        
        # Check that the link is invalid
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The password reset link was invalid")


class ProfileTests(TravelGuideBaseTestCase):
    """
    Tests for user profile functionality in the TravelGuide application.
    
    These tests verify that user profile management works correctly,
    including viewing and updating profile information.
    """
    
    def setUp(self):
        """
        Set up test data for profile tests.
        
        Extends the base setUp method to include a client for making requests.
        """
        super().setUp()
        
        # Create client for making requests
        self.client = Client()
        
        # URLs for profile views
        self.profile_url = reverse('accounts:profile')
        self.password_change_url = reverse('accounts:password_change')
        
    def test_profile_view_authenticated(self):
        """
        Test that authenticated users can access their profile.
        
        Verifies that an authenticated user can view their profile page
        and it contains their profile information.
        """
        # Log in
        self.client.login(username='testuser', password='password')
        
        # Access profile page
        response = self.client.get(self.profile_url)
        
        # Check that the page loads successfully
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')
        
        # Check that the page contains the user's information
        self.assertContains(response, 'testuser')
        self.assertContains(response, 'testuser@example.com')
        
    def test_profile_view_unauthenticated(self):
        """
        Test that unauthenticated users cannot access profiles.
        
        Verifies that an unauthenticated user is redirected to the
        login page when trying to access the profile page.
        """
        response = self.client.get(self.profile_url)
        
        # Check that the user is redirected to the login page
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.profile_url}")
        
    def test_profile_update(self):
        """
        Test updating user profile information.
        
        Verifies that a user can update their profile information
        and the changes are saved correctly.
        """
        # Log in
        self.client.login(username='testuser', password='password')
        
        # Update profile
        response = self.client.post(self.profile_url, {
            'first_name': 'Updated',
            'last_name': 'User',
            'email': 'updated@example.com',
            'bio': 'This is my updated bio.',
            'preferred_currency': 'EUR',
            'preferred_language': 'fr'
        }, follow=True)
        
        # Check that the update was successful
        self.assertEqual(response.status_code, 200)
        
        # Check that success message is displayed
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn('profile updated', str(messages[0]).lower())
        
        # Check that the user information was updated
        self.test_user.refresh_from_db()
        self.assertEqual(self.test_user.first_name, 'Updated')
        self.assertEqual(self.test_user.last_name, 'User')
        self.assertEqual(self.test_user.email, 'updated@example.com')
        
        # Check that the profile information was updated
        self.test_user.profile.refresh_from_db()
        self.assertEqual(self.test_user.profile.bio, 'This is my updated bio.')
        self.assertEqual(self.test_user.profile.preferred_currency, 'EUR')
        self.assertEqual(self.test_user.profile.preferred_language, 'fr')
        
    def test_password_change(self):
        """
        Test changing user password.
        
        Verifies that a user can change their password and
        the new password is saved correctly.
        """
        # Log in
        self.client.login(username='testuser', password='password')
        
        # Change password
        response = self.client.post(self.password_change_url, {
            'old_password': 'password',
            'new_password1': 'NewPassword789',
            'new_password2': 'NewPassword789'
        }, follow=True)
        
        # Check that the password change was successful
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, self.profile_url)
        
        # Check that success message is displayed
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn('password changed', str(messages[0]).lower())
        
        # Check that the password was changed
        self.test_user.refresh_from_db()
        self.assertTrue(self.test_user.check_password('NewPassword789'))
        
        # Check that the user is still logged in
        self.assertTrue(response.context['user'].is_authenticated)
        
    def test_password_change_incorrect_old_password(self):
        """
        Test changing password with incorrect old password.
        
        Verifies that a user cannot change their password if they
        provide an incorrect old password.
        """
        # Log in
        self.client.login(username='testuser', password='password')
        
        # Try to change password with incorrect old password
        response = self.client.post(self.password_change_url, {
            'old_password': 'wrongpassword',
            'new_password1': 'NewPassword789',
            'new_password2': 'NewPassword789'
        })
        
        # Check that the password change failed
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'old_password', 'Your old password was entered incorrectly. Please enter it again.')
        
        # Check that the password was not changed
        self.test_user.refresh_from_db()
        self.assertTrue(self.test_user.check_password('password'))
