"""
Utility functions for OTP (One-Time Password) functionality.

This module provides helper functions for generating, validating, and managing OTPs.
"""
import random
import string
import time
from datetime import datetime, timedelta

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
import pyotp

def generate_otp_code(length=6):
    """
    Generate a random numeric OTP code of the specified length.
    
    Args:
        length (int): Length of the OTP code (default: 6)
        
    Returns:
        str: The generated OTP code
    """
    return ''.join(random.choices(string.digits, k=length))

def generate_totp_secret():
    """
    Generate a new TOTP secret key.
    
    Returns:
        str: A base32-encoded secret key
    """
    return pyotp.random_base32()

def get_totp_uri(secret, email, issuer_name=None):
    """
    Generate a TOTP provisioning URI for use with authenticator apps.
    
    Args:
        secret (str): The TOTP secret key
        email (str): User's email address
        issuer_name (str, optional): Name of the issuer (app name)
        
    Returns:
        str: A TOTP provisioning URI
    """
    if not issuer_name:
        issuer_name = getattr(settings, 'OTP_ISSUER_NAME', 'GuidesApp')
    
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=email,
        issuer_name=issuer_name
    )

def verify_otp(secret, otp_code, window=1):
    """
    Verify a TOTP code against a secret key.
    
    Args:
        secret (str): The TOTP secret key
        otp_code (str): The OTP code to verify
        window (int): Number of time steps to check on either side of the current time
        
    Returns:
        bool: True if the OTP code is valid, False otherwise
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(otp_code, valid_window=window)

def get_otp_expiry_timestamp():
    """
    Get the expiry timestamp for an OTP code based on settings.
    
    Returns:
        datetime: The datetime when the OTP will expire
    """
    expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
    return timezone.now() + timedelta(minutes=expiry_minutes)

def is_otp_expired(created_at):
    """
    Check if an OTP code has expired.
    
    Args:
        created_at (datetime): When the OTP was created
        
    Returns:
        bool: True if the OTP has expired, False otherwise
    """
    expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
    expiry_time = created_at + timedelta(minutes=expiry_minutes)
    return timezone.now() > expiry_time

def cache_otp_attempt(user_id, max_attempts=3, window_minutes=15):
    """
    Track OTP verification attempts in cache.
    
    Args:
        user_id (int): The user's ID
        max_attempts (int): Maximum allowed attempts before locking out
        window_minutes (int): Time window in minutes to track attempts
        
    Returns:
        tuple: (bool, int) - (is_locked, attempts_remaining)
    """
    cache_key = f'otp_attempts_{user_id}'
    attempts = cache.get(cache_key, [])
    now = timezone.now()
    
    # Remove attempts older than the time window
    attempts = [t for t in attempts if now - t < timedelta(minutes=window_minutes)]
    
    # Add current attempt
    attempts.append(now)
    
    # Update cache
    cache.set(cache_key, attempts, window_minutes * 60)
    
    # Check if user is locked out
    if len(attempts) >= max_attempts:
        return True, 0
    
    return False, max_attempts - len(attempts)

def clear_otp_attempts(user_id):
    """
    Clear OTP verification attempts for a user.
    
    Args:
        user_id (int): The user's ID
    """
    cache_key = f'otp_attempts_{user_id}'
    cache.delete(cache_key)
