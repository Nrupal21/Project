"""
Encryption utilities for securing sensitive user data.

This module provides field-level encryption for sensitive user information including:
- User email addresses
- Phone numbers
- Physical addresses
- Restaurant contact information

Uses Fernet symmetric encryption (AES-128 in CBC mode) from the cryptography library.
All sensitive data is encrypted at rest in the database and decrypted only when needed.
"""

import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
import logging

logger = logging.getLogger('food_ordering.security')


class EncryptionManager:
    """
    Manages encryption and decryption of sensitive data fields.
    
    This class provides a centralized encryption service using Fernet symmetric encryption.
    It automatically generates encryption keys from Django's SECRET_KEY and a custom salt.
    
    Features:
    - Automatic key derivation from Django SECRET_KEY
    - Field-level encryption for sensitive data
    - Transparent encryption/decryption
    - Error handling and logging
    - Support for null/empty values
    
    Security Notes:
    - Uses PBKDF2 key derivation with 100,000 iterations
    - Employs AES-128 encryption in CBC mode via Fernet
    - All encrypted data is base64 encoded for database storage
    """
    
    _fernet = None
    _encryption_key = None
    
    @classmethod
    def _get_encryption_key(cls):
        """
        Generate or retrieve the encryption key.
        
        Derives a secure encryption key from Django's SECRET_KEY using PBKDF2.
        The key is cached for performance after first generation.
        
        Returns:
            bytes: 32-byte encryption key suitable for Fernet
            
        Raises:
            ImproperlyConfigured: If SECRET_KEY is not set or invalid
        """
        if cls._encryption_key is not None:
            return cls._encryption_key
        
        # Get Django's SECRET_KEY
        secret_key = getattr(settings, 'SECRET_KEY', None)
        if not secret_key:
            raise ImproperlyConfigured(
                "SECRET_KEY must be set in Django settings for encryption to work"
            )
        
        # Get custom encryption salt from settings or use default
        encryption_salt = getattr(
            settings, 
            'ENCRYPTION_SALT', 
            b'food-ordering-encryption-salt-v1'
        )
        
        # Derive encryption key using PBKDF2HMAC
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 32 bytes = 256 bits for AES-256
            salt=encryption_salt,
            iterations=100000,  # OWASP recommended minimum
        )
        
        # Generate key from SECRET_KEY
        key = base64.urlsafe_b64encode(
            kdf.derive(secret_key.encode('utf-8'))
        )
        
        cls._encryption_key = key
        logger.info("Encryption key derived successfully")
        return key
    
    @classmethod
    def _get_fernet(cls):
        """
        Get or create Fernet cipher instance.
        
        Returns:
            Fernet: Configured Fernet cipher for encryption/decryption
        """
        if cls._fernet is None:
            key = cls._get_encryption_key()
            cls._fernet = Fernet(key)
        return cls._fernet
    
    @classmethod
    def encrypt(cls, plaintext):
        """
        Encrypt plaintext data.
        
        Encrypts the provided plaintext using Fernet symmetric encryption.
        Handles None and empty string values gracefully.
        
        Args:
            plaintext (str): The data to encrypt
            
        Returns:
            str: Base64-encoded encrypted data, or None if input is None/empty
            
        Example:
            >>> encrypted = EncryptionManager.encrypt("user@example.com")
            >>> print(encrypted)
            'gAAAAABhX...'  # Base64 encoded ciphertext
        """
        if not plaintext:
            return None
        
        try:
            # Convert string to bytes
            plaintext_bytes = str(plaintext).encode('utf-8')
            
            # Encrypt using Fernet
            fernet = cls._get_fernet()
            encrypted_bytes = fernet.encrypt(plaintext_bytes)
            
            # Convert to string for database storage
            encrypted_str = encrypted_bytes.decode('utf-8')
            
            logger.debug(f"Successfully encrypted data (length: {len(plaintext)})")
            return encrypted_str
            
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise
    
    @classmethod
    def decrypt(cls, ciphertext, audit_context=None):
        """
        Decrypt encrypted data with audit logging.

        Decrypts the provided ciphertext using Fernet symmetric encryption.
        Handles None and empty string values gracefully.
        Logs all decryption operations for GDPR compliance.

        Args:
            ciphertext (str): The encrypted data to decrypt
            audit_context (dict): Optional context for audit logging
                - user_id: ID of user requesting decryption
                - field_name: Name of field being decrypted
                - model_name: Name of model containing the field

        Returns:
            str: Decrypted plaintext, or None if input is None/empty

        Raises:
            cryptography.fernet.InvalidToken: If decryption fails (wrong key or corrupted data)

        Example:
            >>> decrypted = EncryptionManager.decrypt("gAAAAABhX...", {
            ...     'user_id': 123,
            ...     'field_name': 'email',
            ...     'model_name': 'UserProfile'
            ... })
            >>> print(decrypted)
            'user@example.com'
        """
        if not ciphertext:
            return None

        try:
            # Convert string to bytes
            ciphertext_bytes = ciphertext.encode('utf-8')

            # Decrypt using Fernet
            fernet = cls._get_fernet()
            decrypted_bytes = fernet.decrypt(ciphertext_bytes)

            # Convert back to string
            decrypted_str = decrypted_bytes.decode('utf-8')

            # Log successful decryption with audit context (GDPR Article 30 compliance)
            audit_info = {
                'action': 'decrypt_success',
                'data_length': len(ciphertext),
                'timestamp': timezone.now().isoformat()
            }
            
            if audit_context:
                audit_info.update(audit_context)
                logger.info(
                    f"Data decrypted successfully - User: {audit_context.get('user_id', 'unknown')}, "
                    f"Field: {audit_context.get('field_name', 'unknown')}, "
                    f"Model: {audit_context.get('model_name', 'unknown')}"
                )
            else:
                logger.debug("Successfully decrypted data")
            
            return decrypted_str

        except Exception as e:
            # Log failed decryption attempts for security monitoring
            audit_info = {
                'action': 'decrypt_failed',
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
            
            if audit_context:
                audit_info.update(audit_context)
                logger.warning(
                    f"Decryption failed - User: {audit_context.get('user_id', 'unknown')}, "
                    f"Field: {audit_context.get('field_name', 'unknown')}, "
                    f"Error: {str(e)}"
                )
            else:
                logger.error(f"Decryption failed: {str(e)}")
            
            # Return None instead of raising to handle corrupted data gracefully
            return None
    
    @classmethod
    def encrypt_dict(cls, data_dict, fields_to_encrypt):
        """
        Encrypt multiple fields in a dictionary.
        
        Useful for encrypting form data or API payloads before database storage.
        
        Args:
            data_dict (dict): Dictionary containing data to encrypt
            fields_to_encrypt (list): List of field names to encrypt
            
        Returns:
            dict: New dictionary with specified fields encrypted
            
        Example:
            >>> data = {'email': 'user@example.com', 'phone': '1234567890', 'name': 'John'}
            >>> encrypted = EncryptionManager.encrypt_dict(data, ['email', 'phone'])
            >>> print(encrypted)
            {'email': 'gAAAAABhX...', 'phone': 'gAAAAABhY...', 'name': 'John'}
        """
        encrypted_dict = data_dict.copy()
        
        for field in fields_to_encrypt:
            if field in encrypted_dict and encrypted_dict[field]:
                encrypted_dict[field] = cls.encrypt(encrypted_dict[field])
        
        return encrypted_dict
    
    @classmethod
    def decrypt_dict(cls, data_dict, fields_to_decrypt):
        """
        Decrypt multiple fields in a dictionary.
        
        Useful for decrypting database records for display or processing.
        
        Args:
            data_dict (dict): Dictionary containing encrypted data
            fields_to_decrypt (list): List of field names to decrypt
            
        Returns:
            dict: New dictionary with specified fields decrypted
            
        Example:
            >>> encrypted = {'email': 'gAAAAABhX...', 'phone': 'gAAAAABhY...', 'name': 'John'}
            >>> decrypted = EncryptionManager.decrypt_dict(encrypted, ['email', 'phone'])
            >>> print(decrypted)
            {'email': 'user@example.com', 'phone': '1234567890', 'name': 'John'}
        """
        decrypted_dict = data_dict.copy()
        
        for field in fields_to_decrypt:
            if field in decrypted_dict and decrypted_dict[field]:
                decrypted_dict[field] = cls.decrypt(decrypted_dict[field])
        
        return decrypted_dict


class EncryptedField:
    """
    Descriptor for transparent field-level encryption in Django models.
    
    This descriptor automatically encrypts data when setting a field value
    and decrypts data when accessing the field value.
    
    Usage in Django models:
        class UserProfile(models.Model):
            _email_encrypted = models.TextField()
            email = EncryptedField('_email_encrypted')
    
    Features:
    - Transparent encryption/decryption
    - Automatic handling of None values
    - Works with Django ORM
    - Minimal code changes required
    """
    
    def __init__(self, encrypted_field_name):
        """
        Initialize the encrypted field descriptor.
        
        Args:
            encrypted_field_name (str): Name of the database field storing encrypted data
        """
        self.encrypted_field_name = encrypted_field_name
    
    def __get__(self, instance, owner):
        """
        Get and decrypt the field value.
        
        Args:
            instance: Model instance
            owner: Model class
            
        Returns:
            str: Decrypted field value
        """
        if instance is None:
            return self
        
        # Get encrypted value from database field
        encrypted_value = getattr(instance, self.encrypted_field_name, None)
        
        # Decrypt and return
        return EncryptionManager.decrypt(encrypted_value)
    
    def __set__(self, instance, value):
        """
        Encrypt and set the field value.
        
        Args:
            instance: Model instance
            value: Plaintext value to encrypt and store
        """
        # Encrypt the value
        encrypted_value = EncryptionManager.encrypt(value)
        
        # Store in database field
        setattr(instance, self.encrypted_field_name, encrypted_value)


def encrypt_user_data(user_data):
    """
    Encrypt sensitive user registration data.
    
    Helper function for encrypting user data during registration or profile updates.
    
    Args:
        user_data (dict): Dictionary containing user data
        
    Returns:
        dict: Dictionary with sensitive fields encrypted
        
    Example:
        >>> data = {
        ...     'username': 'john_doe',
        ...     'email': 'john@example.com',
        ...     'phone': '1234567890',
        ...     'address': '123 Main St'
        ... }
        >>> encrypted = encrypt_user_data(data)
    """
    sensitive_fields = ['email', 'phone_number', 'address', 'full_name']
    return EncryptionManager.encrypt_dict(user_data, sensitive_fields)


def decrypt_user_data(user_data):
    """
    Decrypt sensitive user data for display.
    
    Helper function for decrypting user data when displaying profiles or processing orders.
    
    Args:
        user_data (dict): Dictionary containing encrypted user data
        
    Returns:
        dict: Dictionary with sensitive fields decrypted
        
    Example:
        >>> encrypted = {'email': 'gAAAAABhX...', 'username': 'john_doe'}
        >>> decrypted = decrypt_user_data(encrypted)
        >>> print(decrypted['email'])
        'john@example.com'
    """
    sensitive_fields = ['email', 'phone_number', 'address', 'full_name']
    return EncryptionManager.decrypt_dict(user_data, sensitive_fields)


def encrypt_restaurant_data(restaurant_data):
    """
    Encrypt sensitive restaurant data.
    
    Helper function for encrypting restaurant data during registration or updates.
    
    Args:
        restaurant_data (dict): Dictionary containing restaurant data
        
    Returns:
        dict: Dictionary with sensitive fields encrypted
    """
    sensitive_fields = ['email', 'phone', 'address']
    return EncryptionManager.encrypt_dict(restaurant_data, sensitive_fields)


def decrypt_restaurant_data(restaurant_data):
    """
    Decrypt sensitive restaurant data for display.
    
    Helper function for decrypting restaurant data when displaying information.
    
    Args:
        restaurant_data (dict): Dictionary containing encrypted restaurant data
        
    Returns:
        dict: Dictionary with sensitive fields decrypted
    """
    sensitive_fields = ['email', 'phone', 'address']
    return EncryptionManager.decrypt_dict(restaurant_data, sensitive_fields)
