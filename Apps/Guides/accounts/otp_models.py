"""
OTP models for the accounts app.

This module contains models related to OTP (One-Time Password) functionality
for secure two-factor authentication.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
import pyotp
import uuid
from datetime import timedelta

class OTPDevice(models.Model):
    """
    Model to store OTP device information for users.
    
    This model tracks the OTP secret key and verification status for each user.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='otp_device')
    secret_key = models.CharField(max_length=50, unique=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        """
        Returns a string representation of the OTP device.
        
        Returns:
            str: A string showing the username and verification status
        """
        return f"OTP Device for {self.user.username} - {'Verified' if self.is_verified else 'Not Verified'}"
    
    def generate_secret_key(self):
        """
        Generates a new random secret key for OTP.
        
        Returns:
            str: The generated secret key
        """
        self.secret_key = pyotp.random_base32()
        self.save()
        return self.secret_key
    
    def get_totp_object(self):
        """
        Returns a TOTP object using the device's secret key.
        
        Returns:
            pyotp.TOTP: A TOTP object for generating and verifying OTP codes
        """
        return pyotp.TOTP(self.secret_key)
    
    def verify_otp(self, otp_code):
        """
        Verifies the provided OTP code against the device's secret key.
        
        Args:
            otp_code (str): The OTP code to verify
            
        Returns:
            bool: True if OTP is valid, False otherwise
        """
        totp = self.get_totp_object()
        return totp.verify(otp_code)
    
    def generate_otp(self):
        """
        Generates a new OTP code.
        
        Returns:
            str: A new OTP code
        """
        totp = self.get_totp_object()
        return totp.now()


class OTPSession(models.Model):
    """
    Model to store temporary OTP session information.
    
    This model is used during the login process to track pending OTP verification sessions.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='otp_sessions')
    session_key = models.UUIDField(default=uuid.uuid4, unique=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    def __str__(self):
        """
        Returns a string representation of the OTP session.
        
        Returns:
            str: A string showing the username and session status
        """
        return f"OTP Session for {self.user.username} - {'Verified' if self.is_verified else 'Pending'}"
    
    def save(self, *args, **kwargs):
        """
        Custom save method that sets expiration time if not already set.
        
        Sets the session to expire after a certain time period (30 minutes by default).
        """
        if not self.expires_at:
            # Set expiration to 30 minutes from creation by default
            self.expires_at = timezone.now() + timedelta(minutes=30)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """
        Checks if the OTP session has expired.
        
        Returns:
            bool: True if the session has expired, False otherwise
        """
        return timezone.now() > self.expires_at
    
    @classmethod
    def create_session(cls, user):
        """
        Creates a new OTP session for the given user.
        
        Args:
            user: The user to create the session for
            
        Returns:
            OTPSession: The newly created OTP session
        """
        # Clean up old sessions for this user
        cls.objects.filter(user=user, is_verified=False).delete()
        
        # Create new session
        session = cls(user=user)
        session.save()
        return session
