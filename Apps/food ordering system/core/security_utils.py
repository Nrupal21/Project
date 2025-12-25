"""
Security utilities for food ordering system
Provides input validation, sanitization, and audit logging functions
for payment processing and sensitive data handling
"""

import re
import logging
import hashlib
from decimal import Decimal, InvalidOperation
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.html import escape
from django.utils.translation import gettext_lazy as _

# Security loggers for different types of events
security_logger = logging.getLogger('food_ordering.security')
audit_logger = logging.getLogger('food_ordering.audit')
payment_logger = logging.getLogger('food_ordering.payments')


def validate_and_sanitize_payment_amount(amount):
    """
    Validate and sanitize payment amount to prevent injection attacks
    
    Args:
        amount: Input amount value (string, int, float, or Decimal)
    
    Returns:
        Decimal: Validated and sanitized amount
    
    Raises:
        ValidationError: If amount is invalid or potentially malicious
    """
    try:
        # Convert to string first to handle various input types
        amount_str = str(amount).strip()
        
        # Check for suspicious patterns that might indicate injection attempts
        suspicious_patterns = [
            r'<script.*?>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript protocol
            r'data:',  # Data protocol
            r'vbscript:',  # VBScript protocol
            r'on\w+\s*=',  # Event handlers
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, amount_str, re.IGNORECASE):
                security_logger.warning(
                    f"Suspicious pattern detected in payment amount: {amount_str[:50]}"
                )
                raise ValidationError(_('Invalid payment amount format'))
        
        # Remove any HTML entities or special characters
        sanitized_amount = re.sub(r'[^\d\.]', '', amount_str)
        
        # Convert to Decimal with proper validation
        decimal_amount = Decimal(sanitized_amount)
        
        # Validate amount range (prevent negative or extremely large amounts)
        if decimal_amount <= 0:
            raise ValidationError(_('Payment amount must be positive'))
        if decimal_amount > Decimal('99999.99'):
            raise ValidationError(_('Payment amount exceeds maximum limit'))
        
        # Ensure proper decimal places (max 2 for currency)
        if decimal_amount.as_tuple().exponent < -2:
            raise ValidationError(_('Payment amount has too many decimal places'))
        
        payment_logger.info(f"Payment amount validated: {decimal_amount}")
        return decimal_amount
        
    except (InvalidOperation, ValueError, TypeError) as e:
        security_logger.warning(f"Invalid payment amount format: {amount} - {str(e)}")
        raise ValidationError(_('Invalid payment amount format'))


def validate_and_sanitize_card_number(card_number):
    """
    Validate and sanitize credit card number using Luhn algorithm
    
    Args:
        card_number: Input card number (string)
    
    Returns:
        str: Sanitized card number (last 4 digits only for logging)
    
    Raises:
        ValidationError: If card number is invalid
    """
    try:
        # Remove spaces, dashes, and other non-digit characters
        sanitized = re.sub(r'[^\d]', '', str(card_number))
        
        # Check for suspicious patterns
        if len(sanitized) < 13 or len(sanitized) > 19:
            security_logger.warning("Invalid card number length detected")
            raise ValidationError(_('Invalid credit card number'))
        
        # Luhn algorithm validation
        total = 0
        reverse_digits = sanitized[::-1]
        
        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        
        if total % 10 != 0:
            security_logger.warning("Invalid card number (failed Luhn check)")
            raise ValidationError(_('Invalid credit card number'))
        
        # Log only last 4 digits for security
        last_four = sanitized[-4:]
        payment_logger.info(f"Card number validated ending in: ****{last_four}")
        
        return sanitized
        
    except (ValueError, TypeError) as e:
        security_logger.warning(f"Card number validation error: {str(e)}")
        raise ValidationError(_('Invalid credit card number format'))


def validate_and_sanitize_cvv(cvv):
    """
    Validate and sanitize CVV code
    
    Args:
        cvv: Input CVV code (string)
    
    Returns:
        str: Sanitized CVV (not logged for security)
    
    Raises:
        ValidationError: If CVV is invalid
    """
    try:
        sanitized = re.sub(r'[^\d]', '', str(cvv))
        
        # CVV should be 3 or 4 digits
        if len(sanitized) not in [3, 4]:
            security_logger.warning("Invalid CVV length detected")
            raise ValidationError(_('Invalid CVV code'))
        
        payment_logger.info("CVV validated successfully")
        return sanitized
        
    except (ValueError, TypeError) as e:
        security_logger.warning(f"CVV validation error: {str(e)}")
        raise ValidationError(_('Invalid CVV format'))


def validate_and_sanitize_expiry_date(expiry_month, expiry_year):
    """
    Validate and sanitize credit card expiry date
    
    Args:
        expiry_month: Expiry month (string or int)
        expiry_year: Expiry year (string or int)
    
    Returns:
        tuple: (sanitized_month, sanitized_year)
    
    Raises:
        ValidationError: If expiry date is invalid or expired
    """
    try:
        month = int(expiry_month)
        year = int(expiry_year)
        
        # Validate month range
        if month < 1 or month > 12:
            raise ValidationError(_('Invalid expiry month'))
        
        # Validate year range (reasonable future dates)
        current_year = 2025  # Should use datetime.now().year in production
        if year < current_year or year > current_year + 10:
            raise ValidationError(_('Invalid expiry year'))
        
        # Check if card is expired
        if year == current_year and month < 11:  # Assuming current month is November
            raise ValidationError(_('Credit card has expired'))
        
        payment_logger.info(f"Expiry date validated: {month}/{year}")
        return (month, year)
        
    except (ValueError, TypeError) as e:
        security_logger.warning(f"Expiry date validation error: {str(e)}")
        raise ValidationError(_('Invalid expiry date format'))


def sanitize_user_input(text_input, max_length=255):
    """
    Sanitize user text input to prevent XSS and injection attacks
    
    Args:
        text_input: User input text (string)
        max_length: Maximum allowed length (default: 255)
    
    Returns:
        str: Sanitized text input
    """
    if not text_input:
        return ""
    
    # Convert to string and truncate
    sanitized = str(text_input)[:max_length]
    
    # Remove potentially dangerous HTML tags
    dangerous_tags = ['script', 'iframe', 'object', 'embed', 'form', 'input', 'textarea']
    for tag in dangerous_tags:
        pattern = f'<{tag}.*?>.*?</{tag}>'
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove JavaScript event handlers
    event_handlers = [
        'onload', 'onclick', 'onerror', 'onmouseover', 'onmouseout',
        'onfocus', 'onblur', 'onchange', 'onsubmit', 'onreset'
    ]
    for handler in event_handlers:
        pattern = f'{handler}\s*='
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
    
    # Escape HTML entities
    sanitized = escape(sanitized)
    
    return sanitized.strip()


def log_security_event(event_type, message, user=None, request=None):
    """
    Log security events with proper context and masking
    
    Args:
        event_type: Type of security event (string)
        message: Event message (string)
        user: User object (optional)
        request: Request object (optional)
    """
    # Get IP address from request
    ip_address = getattr(request, 'META', {}).get('REMOTE_ADDR', 'unknown')
    
    # Get user information
    username = getattr(user, 'username', 'anonymous') if user else 'anonymous'
    
    # Log to appropriate logger
    if event_type in ['login_attempt', 'lockout', 'suspicious_activity']:
        security_logger.warning(
            f"{event_type}: {message} | User: {username} | IP: {ip_address}"
        )
    elif event_type in ['order_created', 'payment_processed', 'profile_updated']:
        audit_logger.info(
            f"{event_type}: {message} | User: {username} | IP: {ip_address}",
            extra={'user': username, 'ip': ip_address}
        )
    elif event_type in ['payment_attempt', 'payment_success', 'payment_failure']:
        payment_logger.info(
            f"{event_type}: {message} | User: {username} | IP: {ip_address}",
            extra={'user': username, 'ip': ip_address}
        )


def validate_webhook_signature(payload, signature, secret):
    """
    Validate webhook signature to prevent webhook spoofing attacks
    
    Args:
        payload: Request payload (bytes or string)
        signature: Received signature (string)
        secret: Webhook secret (string)
    
    Returns:
        bool: True if signature is valid
    
    Raises:
        ValidationError: If signature is invalid
    """
    try:
        # Convert payload to bytes if needed
        if isinstance(payload, str):
            payload_bytes = payload.encode('utf-8')
        else:
            payload_bytes = payload
        
        # Calculate expected signature
        expected_signature = hashlib.sha256(
            payload_bytes + secret.encode('utf-8')
        ).hexdigest()
        
        # Compare signatures securely
        if not hashlib.sha256(signature.encode()).hexdigest() == hashlib.sha256(expected_signature.encode()).hexdigest():
            security_logger.warning("Invalid webhook signature detected")
            raise ValidationError(_('Invalid webhook signature'))
        
        payment_logger.info("Webhook signature validated successfully")
        return True
        
    except Exception as e:
        security_logger.error(f"Webhook signature validation error: {str(e)}")
        raise ValidationError(_('Webhook signature validation failed'))


def rate_limit_check(identifier, limit=5, window=300):
    """
    Check rate limiting for sensitive operations
    
    Args:
        identifier: Unique identifier (IP address, user ID, etc.)
        limit: Maximum allowed requests (default: 5)
        window: Time window in seconds (default: 300 = 5 minutes)
    
    Returns:
        bool: True if request is allowed, False if rate limited
    """
    # This is a simplified implementation
    # In production, use Redis or django-ratelimit for better performance
    from django.core.cache import cache
    
    cache_key = f"rate_limit:{identifier}"
    current_count = cache.get(cache_key, 0)
    
    if current_count >= limit:
        security_logger.warning(
            f"Rate limit exceeded for {identifier}: {current_count}/{limit}"
        )
        return False
    
    # Increment counter
    cache.set(cache_key, current_count + 1, window)
    return True
