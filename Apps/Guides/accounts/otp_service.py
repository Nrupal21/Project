"""
OTP Service for handling OTP generation and verification.

This module provides services for generating and verifying OTP codes.
"""
import pyotp
from datetime import timedelta
from django.utils import timezone
from .otp_models import OTPDevice, OTPSession

class OTPService:
    """
    Service class for handling OTP operations.
    
    This class provides methods for generating OTP codes, verifying them,
    and managing OTP sessions.
    """
    
    @staticmethod
    def generate_otp(user):
        """
        Generates a new OTP code for the given user.
        
        Args:
            user: The user to generate the OTP for
            
        Returns:
            tuple: (otp_code, otp_uri) - The generated OTP code and URI for QR code
        """
        # Get or create OTP device for the user
        device, created = OTPDevice.objects.get_or_create(user=user)
        if created or not device.secret_key:
            device.generate_secret_key()
        
        # Generate TOTP object
        totp = device.get_totp_object()
        
        # Generate the current OTP code
        otp_code = totp.now()
        
        # Generate provisioning URI for QR code (optional)
        otp_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="YourAppName"
        )
        
        return otp_code, otp_uri
    
    @staticmethod
    def verify_otp(user, otp_code):
        """
        Verifies the provided OTP code for the given user.
        
        Args:
            user: The user to verify the OTP for
            otp_code: The OTP code to verify
            
        Returns:
            bool: True if the OTP is valid, False otherwise
        """
        try:
            device = OTPDevice.objects.get(user=user)
            totp = device.get_totp_object()
            return totp.verify(otp_code)
        except OTPDevice.DoesNotExist:
            return False
    
    @staticmethod
    def create_otp_session(user):
        """
        Creates a new OTP verification session for the user.
        
        Args:
            user: The user to create the session for
            
        Returns:
            OTPSession: The created OTP session
        """
        return OTPSession.create_session(user)
    
    @staticmethod
    def verify_otp_session(session_key, otp_code):
        """
        Verifies an OTP session with the provided OTP code.
        
        Args:
            session_key: The session key to verify
            otp_code: The OTP code to verify
            
        Returns:
            tuple: (bool, str) - (success, error_message)
        """
        try:
            session = OTPSession.objects.get(
                session_key=session_key,
                is_verified=False,
                expires_at__gt=timezone.now()
            )
            
            if OTPService.verify_otp(session.user, otp_code):
                session.is_verified = True
                session.save()
                return True, "OTP verified successfully"
            return False, "Invalid OTP code"
            
        except OTPSession.DoesNotExist:
            return False, "Invalid or expired session"
