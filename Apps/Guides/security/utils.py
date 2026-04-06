"""
Security utility functions for the TravelGuide application.

This module provides various helper functions for security-related tasks
such as handling IP addresses, generating and validating TOTP secrets and codes,
creating backup codes, QR codes, and managing two-factor authentication workflow.
"""

import os
import base64
import pyotp
from io import BytesIO
import qrcode
import secrets
import string

from django.conf import settings
from django.utils import timezone
from django.contrib.auth import login
from ipware import get_client_ip as ipware_get_client_ip

from .models import SecurityLog, FailedLoginAttempt, TwoFactorAuth


def get_client_ip(request):
    """
    Extract the client IP address from a request.
    
    Uses django-ipware to reliably extract the client IP address,
    considering various proxy setups.
    
    Args:
        request: The HTTP request object
    
    Returns:
        str: The client IP address or None if not found
    """
    client_ip, is_routable = ipware_get_client_ip(request)
    return client_ip


def generate_totp_secret():
    """
    Generate a secure base32-encoded secret for TOTP.
    
    Creates a cryptographically strong random secret suitable
    for use with TOTP-based two-factor authentication.
    
    Returns:
        str: A base32-encoded secret string
    """
    return pyotp.random_base32()


def verify_totp_code(secret, code):
    """
    Verify a TOTP code against a secret.
    
    Validates that the provided code matches what would be generated
    by the authenticator app using the secret.
    
    Args:
        secret (str): The base32-encoded TOTP secret
        code (str): The code provided by the user
        
    Returns:
        bool: True if the code is valid, False otherwise
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(code)


def generate_backup_codes(count=10):
    """
    Generate a set of backup codes for two-factor authentication.
    
    Creates secure random backup codes in the format XXXX-XXXX
    for use when the primary 2FA method is unavailable.
    
    Args:
        count (int, optional): Number of backup codes to generate. Defaults to 10.
        
    Returns:
        list: A list of backup code strings
    """
    codes = []
    
    # Characters to use for backup codes (exclude similar-looking characters)
    allowed_chars = ''.join(c for c in string.ascii_uppercase + string.digits
                          if c not in 'IOl01')
    
    for _ in range(count):
        # Generate two groups of 4 characters
        part1 = ''.join(secrets.choice(allowed_chars) for _ in range(4))
        part2 = ''.join(secrets.choice(allowed_chars) for _ in range(4))
        
        # Format as XXXX-XXXX
        code = f"{part1}-{part2}"
        codes.append(code)
    
    return codes


def verify_backup_code(user, code):
    """
    Verify a backup code for a user and mark it as used if valid.
    
    Checks if the provided code exists in the user's backup codes list
    and removes it if it does (one-time use).
    
    Args:
        user: The user to verify the backup code for
        code (str): The backup code to verify
        
    Returns:
        bool: True if the code is valid, False otherwise
    """
    try:
        twofa = TwoFactorAuth.objects.get(user=user)
        
        # Check if code exists in backup codes
        if code in twofa.backup_codes:
            # Remove the code (one-time use)
            twofa.backup_codes.remove(code)
            twofa.save(update_fields=['backup_codes'])
            return True
        
        return False
    except TwoFactorAuth.DoesNotExist:
        return False


def generate_totp_uri(user, secret):
    """
    Generate a TOTP URI for QR code generation.
    
    Creates a URI that can be used to generate a QR code for easy
    setup in authenticator apps.
    
    Args:
        user: The user for whom the URI is being generated
        secret (str): The base32-encoded TOTP secret
        
    Returns:
        str: A TOTP URI
    """
    # Get the issuer name from settings or use default
    issuer_name = getattr(settings, 'TWOFA_ISSUER_NAME', 'TravelGuide')
    
    # Create the TOTP object
    totp = pyotp.TOTP(secret)
    
    # Generate the provisioning URI
    uri = totp.provisioning_uri(
        name=user.email,
        issuer_name=issuer_name
    )
    
    return uri


def generate_qr_code(uri):
    """
    Generate a QR code image from a URI.
    
    Creates a QR code image that can be scanned by authenticator apps
    to set up two-factor authentication.
    
    Args:
        uri (str): The URI to encode in the QR code
        
    Returns:
        BytesIO: A BytesIO object containing the QR code image
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save the image to a BytesIO object
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    return buffer


def generate_qr_code_base64(uri):
    """
    Generate a base64-encoded QR code image from a URI.
    
    Creates a QR code as a base64-encoded data URL that can be
    directly embedded in HTML.
    
    Args:
        uri (str): The URI to encode in the QR code
        
    Returns:
        str: A base64-encoded data URL for the QR code image
    """
    buffer = generate_qr_code(uri)
    
    # Convert to base64
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    # Return as data URL
    return f"data:image/png;base64,{img_str}"


def complete_login_after_twofa(request, user):
    """
    Complete the login process after successful 2FA verification.
    
    Finalizes authentication, cleans up the session, logs the event,
    and handles "remember me" functionality.
    
    Args:
        request: The HTTP request object
        user: The user to log in
        
    Returns:
        None
    """
    # Clear 2FA session data
    twofa_remember_me = request.session.get('twofa_remember_me', False)
    
    if 'twofa_user_id' in request.session:
        del request.session['twofa_user_id']
    
    if 'twofa_remember_me' in request.session:
        del request.session['twofa_remember_me']
    
    # Complete the login
    if not twofa_remember_me:
        # Session will expire when the user closes the browser
        request.session.set_expiry(0)
    
    login(request, user)
    
    # Clear any failed login attempts
    FailedLoginAttempt.objects.filter(username=user.username).delete()
    
    # Log the successful login
    SecurityLog.objects.create(
        user=user,
        event_type=SecurityLog.EVENT_LOGIN_SUCCESS,
        description=f"User {user.username} logged in successfully after 2FA verification",
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )


def check_account_lockout(username):
    """
    Check if an account is currently locked out.
    
    Determines if a user account is locked due to too many failed login attempts.
    
    Args:
        username (str): The username to check
        
    Returns:
        tuple: (is_locked, minutes_remaining) where is_locked is a boolean and
               minutes_remaining is the time left in the lockout period or 0
    """
    return FailedLoginAttempt.is_locked(username)
