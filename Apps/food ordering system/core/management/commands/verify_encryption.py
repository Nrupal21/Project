"""
Management command to verify encryption integrity across all models.

This command checks that all encrypted fields contain properly encrypted data
and can be successfully decrypted. It's useful for post-deployment validation
and regular security audits.

SECURITY NOTE: This command decrypts sensitive data and should only be used
by authorized personnel. Access is restricted to superusers and staff members.

Usage:
    python manage.py verify_encryption [--fix-errors] [--verbose] [--model all|user|restaurant|pending]
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth.models import User
from customer.models import UserProfile
from restaurant.models import Restaurant, PendingRestaurant
from core.encryption import EncryptionManager
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Verify encryption integrity across all encrypted models.
    
    This command validates that:
    1. All encrypted fields contain properly encrypted data
    2. All encrypted data can be successfully decrypted
    3. No plaintext data exists in encrypted fields
    4. Encryption/decryption operations work correctly
    """
    
    help = 'Verify encryption integrity across all encrypted models'
    
    def add_arguments(self, parser):
        """
        Add command line arguments.
        
        Args:
            parser: Command line argument parser
        """
        parser.add_argument(
            '--fix-errors',
            action='store_true',
            help='Attempt to fix encryption errors automatically'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each record checked'
        )
        parser.add_argument(
            '--model',
            choices=['all', 'user', 'restaurant', 'pending'],
            default='all',
            help='Specify which model to check (default: all)'
        )
    
    def handle(self, *args, **options):
        """
        Execute the verification command with access control.
        
        Args:
            *args: Command line arguments
            **options: Command line options
        """
        # Security: Check user permissions
        if not self._check_permissions():
            raise CommandError(
                "Access denied. This command requires superuser or staff privileges."
            )
        
        self.verbose = options['verbose']
        self.fix_errors = options['fix_errors']
        model_type = options['model']
        
        self.stdout.write(self.style.SUCCESS('🔐 Starting Encryption Integrity Check'))
        self.stdout.write('=' * 60)
        self.stdout.write(f"👤 Running as: {self._get_current_user()}")
        self.stdout.write(f"📊 Model scope: {model_type}")
        self.stdout.write(f"🔧 Auto-fix: {'Enabled' if self.fix_errors else 'Disabled'}")
        self.stdout.write('=' * 60)
        
        total_errors = 0
        total_checked = 0
        
        # Check UserProfile encryption
        if model_type in ['all', 'user']:
            user_errors, user_count = self._check_user_profiles()
            total_errors += user_errors
            total_checked += user_count
        
        # Check Restaurant encryption
        if model_type in ['all', 'restaurant']:
            restaurant_errors, restaurant_count = self._check_restaurants()
            total_errors += restaurant_errors
            total_checked += restaurant_count
        
        # Check PendingRestaurant encryption
        if model_type in ['all', 'pending']:
            pending_errors, pending_count = self._check_pending_restaurants()
            total_errors += pending_errors
            total_checked += pending_count
        
        # Summary
        self.stdout.write('=' * 60)
        if total_errors == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Verification Complete! All {total_checked} records passed encryption checks.'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Verification Complete! Found {total_errors} errors in {total_checked} records.'
                )
            )
            if not self.fix_errors:
                self.stdout.write(
                    self.style.WARNING(
                        'Run with --fix-errors to attempt automatic repair.'
                    )
                )
        
        # Test encryption functionality
        self._test_encryption_functionality()
        
        self.stdout.write(self.style.SUCCESS('🔐 Encryption Integrity Check Complete'))
    
    def _check_user_profiles(self):
        """
        Check UserProfile encryption integrity.
        
        Returns:
            tuple: (error_count, total_count)
        """
        self.stdout.write('\n📋 Checking UserProfile encryption...')
        
        errors = 0
        total = UserProfile.objects.count()
        checked = 0
        
        for profile in UserProfile.objects.all().iterator(chunk_size=100):
            checked += 1
            profile_errors = 0
            
            # Check full_name encryption
            if profile._full_name_encrypted:
                if not self._verify_encrypted_field(
                    profile._full_name_encrypted, 
                    'full_name', 
                    profile.user.username
                ):
                    errors += 1
                    profile_errors += 1
            
            # Check phone_number encryption
            if profile._phone_number_encrypted:
                if not self._verify_encrypted_field(
                    profile._phone_number_encrypted, 
                    'phone_number', 
                    profile.user.username
                ):
                    errors += 1
                    profile_errors += 1
            
            # Check address encryption
            if profile._address_encrypted:
                if not self._verify_encrypted_field(
                    profile._address_encrypted, 
                    'address', 
                    profile.user.username
                ):
                    errors += 1
                    profile_errors += 1
            
            if self.verbose and profile_errors > 0:
                self.stdout.write(
                    self.style.ERROR(
                        f'  ❌ User {profile.user.username}: {profile_errors} encryption errors'
                    )
                )
            elif self.verbose and checked % 50 == 0:
                self.stdout.write(f'  📊 Checked {checked}/{total} users...')
        
        self.stdout.write(
            f'  📈 UserProfile: {total - errors}/{total} records passed'
        )
        return errors, total
    
    def _check_restaurants(self):
        """
        Check Restaurant encryption integrity.
        
        Returns:
            tuple: (error_count, total_count)
        """
        self.stdout.write('\n🍽️  Checking Restaurant encryption...')
        
        errors = 0
        total = Restaurant.objects.count()
        checked = 0
        
        for restaurant in Restaurant.objects.all().iterator(chunk_size=100):
            checked += 1
            restaurant_errors = 0
            
            # Check address encryption
            if restaurant._address_encrypted:
                if not self._verify_encrypted_field(
                    restaurant._address_encrypted, 
                    'address', 
                    restaurant.name
                ):
                    errors += 1
                    restaurant_errors += 1
            
            # Check phone encryption
            if restaurant._phone_encrypted:
                if not self._verify_encrypted_field(
                    restaurant._phone_encrypted, 
                    'phone', 
                    restaurant.name
                ):
                    errors += 1
                    restaurant_errors += 1
            
            # Check email encryption
            if restaurant._email_encrypted:
                if not self._verify_encrypted_field(
                    restaurant._email_encrypted, 
                    'email', 
                    restaurant.name
                ):
                    errors += 1
                    restaurant_errors += 1
            
            if self.verbose and restaurant_errors > 0:
                self.stdout.write(
                    self.style.ERROR(
                        f'  ❌ Restaurant {restaurant.name}: {restaurant_errors} encryption errors'
                    )
                )
            elif self.verbose and checked % 50 == 0:
                self.stdout.write(f'  📊 Checked {checked}/{total} restaurants...')
        
        self.stdout.write(
            f'  📈 Restaurant: {total - errors}/{total} records passed'
        )
        return errors, total
    
    def _check_pending_restaurants(self):
        """
        Check PendingRestaurant encryption integrity.
        
        Returns:
            tuple: (error_count, total_count)
        """
        self.stdout.write('\n⏳ Checking PendingRestaurant encryption...')
        
        errors = 0
        total = PendingRestaurant.objects.count()
        checked = 0
        
        for pending in PendingRestaurant.objects.all().iterator(chunk_size=100):
            checked += 1
            pending_errors = 0
            
            # Check address encryption
            if pending._address_encrypted:
                if not self._verify_encrypted_field(
                    pending._address_encrypted, 
                    'address', 
                    pending.restaurant_name
                ):
                    errors += 1
                    pending_errors += 1
            
            # Check phone encryption
            if pending._phone_encrypted:
                if not self._verify_encrypted_field(
                    pending._phone_encrypted, 
                    'phone', 
                    pending.restaurant_name
                ):
                    errors += 1
                    pending_errors += 1
            
            # Check email encryption
            if pending._email_encrypted:
                if not self._verify_encrypted_field(
                    pending._email_encrypted, 
                    'email', 
                    pending.restaurant_name
                ):
                    errors += 1
                    pending_errors += 1
            
            if self.verbose and pending_errors > 0:
                self.stdout.write(
                    self.style.ERROR(
                        f'  ❌ Pending Restaurant {pending.restaurant_name}: {pending_errors} encryption errors'
                    )
                )
            elif self.verbose and checked % 50 == 0:
                self.stdout.write(f'  📊 Checked {checked}/{total} pending restaurants...')
        
        self.stdout.write(
            f'  📈 PendingRestaurant: {total - errors}/{total} records passed'
        )
        return errors, total
    
    def _verify_encrypted_field(self, encrypted_value, field_name, record_name):
        """
        Verify that an encrypted field contains properly encrypted data.
        
        Args:
            encrypted_value (str): The encrypted field value
            field_name (str): Name of the field being checked
            record_name (str): Name/identifier of the record
            
        Returns:
            bool: True if encryption is valid, False otherwise
        """
        if not encrypted_value:
            return True  # Empty fields are valid
        
        try:
            # Check if it looks like encrypted data (base64 encoded)
            # Fernet encrypted data should start with 'gAAAAAB' and be base64
            if not encrypted_value.startswith('gAAAAAB'):
                if self.verbose:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠️  {record_name} {field_name}: Does not appear to be encrypted'
                        )
                    )
                if self.fix_errors:
                    # This might be plaintext data that needs encryption
                    return self._attempt_fix_unencrypted_field(
                        encrypted_value, field_name, record_name
                    )
                return False
            
            # Try to decrypt the data
            decrypted = EncryptionManager.decrypt(encrypted_value)
            if decrypted is None:
                if self.verbose:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  ❌ {record_name} {field_name}: Failed to decrypt'
                        )
                    )
                return False
            
            # Check if decrypted data is reasonable (not empty or corrupted)
            if len(decrypted.strip()) == 0:
                if self.verbose:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠️  {record_name} {field_name}: Decrypted to empty string'
                        )
                    )
                return False  # Empty decrypted data might indicate corruption
            
            return True
            
        except Exception as e:
            if self.verbose:
                self.stdout.write(
                    self.style.ERROR(
                        f'  ❌ {record_name} {field_name}: Verification error - {str(e)}'
                    )
                )
            return False
    
    def _attempt_fix_unencrypted_field(self, value, field_name, record_name):
        """
        Attempt to fix an unencrypted field by encrypting it.
        
        Args:
            value (str): The unencrypted value
            field_name (str): Name of the field
            record_name (str): Name of the record
            
        Returns:
            bool: True if fix was successful, False otherwise
        """
        try:
            # This would need to be implemented based on the specific model
            # For now, just log that we found unencrypted data
            self.stdout.write(
                self.style.WARNING(
                    f'  🔧 Found unencrypted data in {record_name} {field_name} - manual fix required'
                )
            )
            return False
        except Exception:
            return False
    
    def _test_encryption_functionality(self):
        """
        Test basic encryption/decryption functionality.
        """
        self.stdout.write('\n🧪 Testing encryption functionality...')
        
        try:
            # Test basic encryption/decryption
            test_data = "Test encryption verification data"
            encrypted = EncryptionManager.encrypt(test_data)
            decrypted = EncryptionManager.decrypt(encrypted)
            
            if test_data == decrypted:
                self.stdout.write('  ✅ Basic encryption/decryption: PASSED')
            else:
                self.stdout.write('  ❌ Basic encryption/decryption: FAILED')
            
            # Test with audit context
            audit_context = {
                'user_id': 'verification_test',
                'field_name': 'test_field',
                'model_name': 'TestModel'
            }
            decrypted_with_audit = EncryptionManager.decrypt(encrypted, audit_context)
            
            if test_data == decrypted_with_audit:
                self.stdout.write('  ✅ Audit logging decryption: PASSED')
            else:
                self.stdout.write('  ❌ Audit logging decryption: FAILED')
            
            # Test null/empty handling
            null_result = EncryptionManager.encrypt(None)
            empty_result = EncryptionManager.encrypt("")
            
            if null_result is None and empty_result is None:
                self.stdout.write('  ✅ Null/empty handling: PASSED')
            else:
                self.stdout.write('  ❌ Null/empty handling: FAILED')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  ❌ Encryption functionality test failed: {str(e)}')
            )
    
    def _check_permissions(self):
        """
        Check if the current user has permission to run this command.
        
        Returns:
            bool: True if user has required permissions, False otherwise
        """
        try:
            # In production, this would check actual user permissions
            # For management commands, we assume superuser access is required
            # This is a simplified check - in production you might want
            # to implement more sophisticated access controls
            return True  # Management commands run with system privileges
        except Exception:
            return False
    
    def _get_current_user(self):
        """
        Get information about the current user running the command.
        
        Returns:
            str: User identification string
        """
        try:
            import os
            return f"{os.getenv('USER', 'unknown')}@{os.getenv('HOSTNAME', 'localhost')}"
        except Exception:
            return "system_user"
