"""
SMS OTP (One-Time Password) functionality.

This module provides functions for sending and verifying SMS OTPs.
"""
import random
import string
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from twilio.rest import Client
from .models import CustomUser
import logging

logger = logging.getLogger(__name__)

# Twilio settings (you'll need to add these to your settings.py)
TWILIO_ACCOUNT_SID = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = getattr(settings, 'TWILIO_PHONE_NUMBER', '')

# OTP settings
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 3
OTP_ATTEMPT_WINDOW = 15  # minutes

def generate_otp_code(length=OTP_LENGTH):
    """
    Generate a random numeric OTP code.
    
    Args:
        length (int): Length of the OTP code (default: 6)
        
    Returns:
        str: The generated OTP code
    """
    return ''.join(random.choices(string.digits, k=length))

def send_sms_otp(phone_number, otp_code):
    """
    Send an OTP code via SMS using Twilio.
    
    Args:
        phone_number (str): The phone number to send the OTP to (format: +1234567890)
        otp_code (str): The OTP code to send
        
    Returns:
        bool: True if the SMS was sent successfully, False otherwise
    """
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        logger.error("Twilio credentials not configured")
        return False
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=f"Your OTP code is: {otp_code}. Valid for {OTP_EXPIRY_MINUTES} minutes.",
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        logger.info(f"SMS OTP sent to {phone_number}. SID: {message.sid}")
        return True
    except Exception as e:
        logger.error(f"Failed to send SMS OTP to {phone_number}: {str(e)}")
        return False

def cache_otp(phone_number, otp_code):
    """
    Store the OTP code in cache with an expiry time.
    
    Args:
        phone_number (str): The phone number to associate with the OTP
        otp_code (str): The OTP code to store
        
    Returns:
        bool: True if the OTP was cached successfully
    """
    cache_key = f"otp_{phone_number}"
    expiry_time = OTP_EXPIRY_MINUTES * 60  # Convert minutes to seconds
    return cache.set(cache_key, {
        'code': otp_code,
        'created_at': datetime.now().isoformat(),
        'attempts': 0
    }, timeout=expiry_time)

def verify_otp(phone_number, user_otp):
    """
    Verify the provided OTP code for a phone number.
    
    Args:
        phone_number (str): The phone number to verify the OTP for
        user_otp (str): The OTP code provided by the user
        
    Returns:
        tuple: (bool, str) - (is_valid, message)
    """
    cache_key = f"otp_{phone_number}"
    cached_data = cache.get(cache_key)
    
    if not cached_data:
        return False, "OTP has expired or is invalid"
    
    # Check max attempts
    if cached_data.get('attempts', 0) >= MAX_OTP_ATTEMPTS:
        return False, "Maximum OTP attempts exceeded. Please request a new OTP."
    
    # Check if OTP matches
    if cached_data.get('code') != user_otp:
        # Increment attempt counter
        cached_data['attempts'] = cached_data.get('attempts', 0) + 1
        cache.set(cache_key, cached_data, timeout=cache.ttl(cache_key))
        return False, "Invalid OTP code"
    
    # OTP is valid, clear it from cache
    cache.delete(cache_key)
    return True, "OTP verified successfully"

def get_or_create_user_by_phone(phone_number):
    """
    Get an existing user by phone number or create a new one.
    
    Args:
        phone_number (str): The user's phone number
        
    Returns:
        tuple: (user, created) - The user object and a boolean indicating if it was created
    """
    try:
        user = CustomUser.objects.get(phone_number=phone_number)
        return user, False
    except CustomUser.DoesNotExist:
        # Create a new user with the phone number
        username = f"user_{phone_number}"
        email = f"{phone_number}@example.com"  # You might want to handle this differently
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            phone_number=phone_number,
            password=None  # User will set a password later
        )
        return user, True
