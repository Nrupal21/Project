# Data Encryption Security Documentation

## Overview

This document describes the comprehensive field-level encryption system implemented in the Food Ordering System to protect sensitive user and restaurant data. The system uses industry-standard encryption to ensure data privacy and security compliance.

## Encryption Technology

### Encryption Algorithm
- **Method**: Fernet symmetric encryption (AES-128 in CBC mode)
- **Library**: Python `cryptography` package
- **Key Derivation**: PBKDF2 with SHA-256
- **Iterations**: 100,000 (OWASP recommended minimum)
- **Key Length**: 256 bits (32 bytes)

### Security Features
- ✅ **At-Rest Encryption**: All sensitive data encrypted in database
- ✅ **Transparent Decryption**: Automatic decryption when accessed
- ✅ **Key Derivation**: Secure key generation from Django SECRET_KEY
- ✅ **Salt Protection**: Custom salt for additional security
- ✅ **Error Handling**: Graceful handling of corrupted data
- ✅ **Logging**: Security event logging for audit trails

## Encrypted Data Fields

### User Profile (UserProfile Model)
The following user data is encrypted at rest:

1. **Full Name** (`full_name`)
   - Database field: `_full_name_encrypted`
   - Contains: User's complete name
   - Used for: Delivery, personalization

2. **Phone Number** (`phone_number`)
   - Database field: `_phone_number_encrypted`
   - Contains: Contact phone number
   - Used for: Order notifications, delivery contact

3. **Address** (`address`)
   - Database field: `_address_encrypted`
   - Contains: Physical delivery address
   - Used for: Food delivery

### Restaurant Data (Restaurant Model)
The following restaurant contact information is encrypted:

1. **Address** (`address`)
   - Database field: `_address_encrypted`
   - Contains: Restaurant physical location
   - Used for: Customer information, delivery routing

2. **Phone** (`phone`)
   - Database field: `_phone_encrypted`
   - Contains: Restaurant contact number
   - Used for: Customer inquiries, order coordination

3. **Email** (`email`)
   - Database field: `_email_encrypted`
   - Contains: Restaurant contact email
   - Used for: Business communications

### Pending Restaurant (PendingRestaurant Model)
Same fields as Restaurant model are encrypted during the approval process.

## Implementation Details

### Encryption Manager (`core/encryption.py`)

The `EncryptionManager` class provides centralized encryption services:

```python
from core.encryption import EncryptionManager

# Encrypt data
encrypted = EncryptionManager.encrypt("sensitive data")

# Decrypt data
decrypted = EncryptionManager.decrypt(encrypted)
```

### Transparent Property Access

Models use Python properties for transparent encryption/decryption:

```python
# Setting a value (automatically encrypted)
user_profile.full_name = "John Doe"
user_profile.save()

# Getting a value (automatically decrypted)
name = user_profile.full_name  # Returns "John Doe"
```

### Database Storage

- **Encrypted fields** are stored as `TextField` with `_encrypted` suffix
- **Properties** provide transparent access without suffix
- **Original field names** work exactly as before (backward compatible)

## Configuration

### Settings (`food_ordering/settings.py`)

```python
# Encryption salt (customize in production)
ENCRYPTION_SALT = b'food-ordering-encryption-salt-v1'

# Encrypted fields documented in settings
# - UserProfile: full_name, phone_number, address
# - Restaurant: address, phone, email
# - PendingRestaurant: address, phone, email
```

### Environment Variables

For production, set custom encryption salt:

```bash
# .env file
ENCRYPTION_SALT=your-custom-salt-here-change-in-production
SECRET_KEY=your-django-secret-key-keep-this-secure
```

## Security Best Practices

### Key Management

1. **SECRET_KEY Protection**
   - Never commit SECRET_KEY to version control
   - Use environment variables in production
   - Rotate keys periodically (requires data re-encryption)

2. **Encryption Salt**
   - Use unique salt per deployment
   - Store securely in environment variables
   - Document salt changes for key rotation

3. **Backup Strategy**
   - Backup SECRET_KEY and ENCRYPTION_SALT securely
   - Store in password manager or secrets vault
   - Document recovery procedures

### Access Control

1. **Database Access**
   - Limit database user permissions
   - Use read-only replicas for reporting
   - Audit database access logs

2. **Application Access**
   - Implement role-based access control
   - Log all data access events
   - Monitor for unusual access patterns

3. **Admin Interface**
   - Restrict Django admin access
   - Use two-factor authentication
   - Log all admin actions

## Migration Guide

### Step 1: Install Dependencies

```bash
pip install cryptography
```

### Step 2: Create Migrations

```bash
python manage.py makemigrations customer
python manage.py makemigrations restaurant
```

### Step 3: Apply Migrations

```bash
python manage.py migrate
```

### Step 4: Encrypt Existing Data

Create a data migration to encrypt existing plaintext data:

```python
# In a new migration file
from django.db import migrations
from core.encryption import EncryptionManager

def encrypt_existing_data(apps, schema_editor):
    UserProfile = apps.get_model('customer', 'UserProfile')
    
    for profile in UserProfile.objects.all():
        # Encrypt existing data
        if profile.full_name:
            profile._full_name_encrypted = EncryptionManager.encrypt(profile.full_name)
        if profile.phone_number:
            profile._phone_number_encrypted = EncryptionManager.encrypt(profile.phone_number)
        if profile.address:
            profile._address_encrypted = EncryptionManager.encrypt(profile.address)
        profile.save()

class Migration(migrations.Migration):
    dependencies = [
        ('customer', 'XXXX_previous_migration'),
    ]
    
    operations = [
        migrations.RunPython(encrypt_existing_data),
    ]
```

## Usage Examples

### Creating User Profile with Encrypted Data

```python
from customer.models import UserProfile
from django.contrib.auth.models import User

# Create user
user = User.objects.create_user(
    username='john_doe',
    email='john@example.com',
    password='secure_password'
)

# Create profile with encrypted data
profile = UserProfile.objects.create(
    user=user,
    full_name='John Doe',  # Automatically encrypted
    phone_number='+1234567890',  # Automatically encrypted
    address='123 Main St, City',  # Automatically encrypted
    city='New York',
    postal_code='10001'
)

# Access decrypted data
print(profile.full_name)  # Returns "John Doe" (decrypted)
print(profile.phone_number)  # Returns "+1234567890" (decrypted)
```

### Creating Restaurant with Encrypted Data

```python
from restaurant.models import Restaurant

# Create restaurant with encrypted contact info
restaurant = Restaurant.objects.create(
    name='Pizza Palace',
    description='Best pizza in town',
    address='456 Food St, City',  # Automatically encrypted
    phone='+9876543210',  # Automatically encrypted
    email='contact@pizzapalace.com',  # Automatically encrypted
    cuisine_type='italian',
    opening_time='09:00',
    closing_time='22:00'
)

# Access decrypted data
print(restaurant.address)  # Returns "456 Food St, City" (decrypted)
print(restaurant.phone)  # Returns "+9876543210" (decrypted)
```

### Bulk Encryption/Decryption

```python
from core.encryption import EncryptionManager

# Encrypt multiple fields in a dictionary
user_data = {
    'username': 'john_doe',
    'email': 'john@example.com',
    'phone': '+1234567890',
    'address': '123 Main St'
}

encrypted_data = EncryptionManager.encrypt_dict(
    user_data, 
    ['email', 'phone', 'address']
)

# Decrypt multiple fields
decrypted_data = EncryptionManager.decrypt_dict(
    encrypted_data,
    ['email', 'phone', 'address']
)
```

## Troubleshooting

### Issue: Decryption Fails

**Symptoms**: `None` returned when accessing encrypted fields

**Causes**:
1. SECRET_KEY changed after encryption
2. ENCRYPTION_SALT changed after encryption
3. Corrupted encrypted data in database

**Solutions**:
1. Restore original SECRET_KEY and ENCRYPTION_SALT
2. Re-encrypt data with new keys
3. Check database for data corruption

### Issue: Migration Errors

**Symptoms**: Migration fails with field errors

**Causes**:
1. Existing data in old fields
2. Field name conflicts

**Solutions**:
1. Create data migration to transfer data
2. Use `_encrypted` suffix for database fields
3. Apply migrations in correct order

### Issue: Performance Degradation

**Symptoms**: Slow queries when accessing encrypted fields

**Causes**:
1. Decryption overhead on large datasets
2. N+1 query problems

**Solutions**:
1. Use `select_related()` and `prefetch_related()`
2. Cache decrypted data when appropriate
3. Consider read replicas for reporting

## Compliance and Regulations

### GDPR Compliance
- ✅ Data encryption at rest
- ✅ Right to erasure (delete encrypted data)
- ✅ Data portability (export decrypted data)
- ✅ Audit logging for data access

### PCI DSS Compliance
- ✅ Encryption of cardholder data (if applicable)
- ✅ Secure key management
- ✅ Access control and monitoring
- ✅ Regular security audits

### HIPAA Compliance (if applicable)
- ✅ PHI encryption at rest
- ✅ Access logging and monitoring
- ✅ Secure key storage
- ✅ Data breach notification procedures

## Monitoring and Auditing

### Security Logging

The system logs encryption-related events:

```python
import logging
logger = logging.getLogger('food_ordering.security')

# Logged events:
# - Encryption key generation
# - Encryption operations
# - Decryption failures
# - Key rotation events
```

### Audit Trail

Monitor these security events:
1. Failed decryption attempts
2. Unusual data access patterns
3. Key rotation events
4. Admin access to encrypted data

### Metrics to Track

1. **Encryption Performance**
   - Average encryption time
   - Average decryption time
   - Cache hit rates

2. **Security Events**
   - Failed decryption count
   - Key rotation frequency
   - Unauthorized access attempts

## Key Rotation Procedure

### When to Rotate Keys

1. **Scheduled Rotation**: Every 12 months
2. **Security Breach**: Immediately if keys compromised
3. **Personnel Changes**: When key holders leave
4. **Compliance Requirements**: As required by regulations

### Rotation Steps

1. **Backup Current Data**
   ```bash
   python manage.py dumpdata > backup.json
   ```

2. **Generate New Keys**
   - Update SECRET_KEY in environment
   - Update ENCRYPTION_SALT if needed

3. **Re-encrypt All Data**
   ```python
   # Create management command for re-encryption
   python manage.py reencrypt_data
   ```

4. **Verify Data Integrity**
   ```python
   python manage.py verify_encryption
   ```

5. **Update Documentation**
   - Document key change date
   - Update backup procedures
   - Notify relevant personnel

## Support and Maintenance

### Regular Maintenance Tasks

1. **Weekly**
   - Review security logs
   - Monitor decryption failures
   - Check system performance

2. **Monthly**
   - Audit data access patterns
   - Review encryption coverage
   - Test backup/restore procedures

3. **Quarterly**
   - Security assessment
   - Performance optimization
   - Update documentation

4. **Annually**
   - Key rotation
   - Compliance audit
   - Security training

### Contact Information

For security issues or questions:
- **Security Team**: security@tetech.in
- **Development Team**: dev@tetech.in
- **Emergency**: Use incident response procedures

## Additional Resources

### Documentation
- [Django Security Best Practices](https://docs.djangoproject.com/en/stable/topics/security/)
- [Cryptography Library Docs](https://cryptography.io/)
- [OWASP Cryptographic Storage](https://owasp.org/www-project-cheat-sheets/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)

### Tools
- [Django Debug Toolbar](https://django-debug-toolbar.readthedocs.io/)
- [Security Headers Scanner](https://securityheaders.com/)
- [SSL Labs](https://www.ssllabs.com/ssltest/)

---

**Document Version**: 1.0  
**Last Updated**: December 2024  
**Author**: Development Team  
**Review Date**: December 2025
