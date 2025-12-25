# Encryption System Setup Guide

## Quick Start

This guide will help you deploy the new encryption system for sensitive user data in the Food Ordering System.

## ⚠️ IMPORTANT: Before You Begin

**BACKUP YOUR DATABASE FIRST!**

```bash
# PostgreSQL backup
pg_dump -U postgres food_ordering_db > backup_before_encryption.sql

# Or use Django's dumpdata
python manage.py dumpdata > backup_before_encryption.json
```

## What's New

### Encrypted Fields

The following fields are now encrypted at rest in the database:

**UserProfile Model:**
- `full_name` - User's complete name
- `phone_number` - Contact phone number  
- `address` - Physical delivery address

**Restaurant Model:**
- `address` - Restaurant physical location
- `phone` - Restaurant contact number
- `email` - Restaurant contact email

**PendingRestaurant Model:**
- `address` - Pending restaurant location
- `phone` - Pending restaurant contact
- `email` - Pending restaurant email

### How It Works

1. **Transparent Encryption**: Data is automatically encrypted when saved
2. **Transparent Decryption**: Data is automatically decrypted when accessed
3. **No Code Changes Required**: Existing code continues to work
4. **Backward Compatible**: Uses property decorators for seamless integration

## Installation Steps

### Step 1: Verify Dependencies

The `cryptography` package should already be installed:

```bash
pip list | grep cryptography
```

If not installed:

```bash
pip install cryptography
```

### Step 2: Review Migrations

Two migration files have been created:

1. `customer/migrations/0009_add_encrypted_fields.py`
2. `restaurant/migrations/0009_add_encrypted_fields.py`

These migrations will:
- Add new encrypted fields (`_*_encrypted`)
- Remove old plaintext fields
- Preserve existing data structure

### Step 3: Create Data Migration (CRITICAL)

Before applying migrations, create a data migration to encrypt existing data:

```bash
python manage.py makemigrations customer --empty --name encrypt_existing_data
```

Edit the generated migration file:

```python
# customer/migrations/0010_encrypt_existing_data.py
from django.db import migrations

def encrypt_existing_user_data(apps, schema_editor):
    """
    Encrypt existing plaintext user data.
    
    This function reads existing plaintext data from the old fields,
    encrypts it, and stores it in the new encrypted fields.
    """
    from core.encryption import EncryptionManager
    
    UserProfile = apps.get_model('customer', 'UserProfile')
    
    # Process in batches to avoid memory issues
    batch_size = 100
    total = UserProfile.objects.count()
    processed = 0
    
    print(f"Encrypting {total} user profiles...")
    
    for profile in UserProfile.objects.all().iterator(chunk_size=batch_size):
        try:
            # Encrypt full_name if it exists
            if hasattr(profile, 'full_name') and profile.full_name:
                profile._full_name_encrypted = EncryptionManager.encrypt(profile.full_name)
            
            # Encrypt phone_number if it exists
            if hasattr(profile, 'phone_number') and profile.phone_number:
                profile._phone_number_encrypted = EncryptionManager.encrypt(profile.phone_number)
            
            # Encrypt address if it exists
            if hasattr(profile, 'address') and profile.address:
                profile._address_encrypted = EncryptionManager.encrypt(profile.address)
            
            profile.save()
            processed += 1
            
            if processed % 10 == 0:
                print(f"Processed {processed}/{total} profiles...")
                
        except Exception as e:
            print(f"Error encrypting profile {profile.id}: {str(e)}")
            # Continue processing other profiles
            continue
    
    print(f"Successfully encrypted {processed} user profiles!")

def reverse_encryption(apps, schema_editor):
    """
    Reverse migration - decrypt data back to plaintext.
    
    WARNING: This should only be used if you need to rollback.
    """
    from core.encryption import EncryptionManager
    
    UserProfile = apps.get_model('customer', 'UserProfile')
    
    print("Decrypting user profiles...")
    
    for profile in UserProfile.objects.all():
        try:
            # Decrypt fields back to plaintext
            if profile._full_name_encrypted:
                profile.full_name = EncryptionManager.decrypt(profile._full_name_encrypted)
            
            if profile._phone_number_encrypted:
                profile.phone_number = EncryptionManager.decrypt(profile._phone_number_encrypted)
            
            if profile._address_encrypted:
                profile.address = EncryptionManager.decrypt(profile._address_encrypted)
            
            profile.save()
            
        except Exception as e:
            print(f"Error decrypting profile {profile.id}: {str(e)}")
            continue

class Migration(migrations.Migration):
    dependencies = [
        ('customer', '0009_add_encrypted_fields'),
    ]
    
    operations = [
        migrations.RunPython(
            encrypt_existing_user_data,
            reverse_code=reverse_encryption
        ),
    ]
```

Create similar migration for restaurant data:

```bash
python manage.py makemigrations restaurant --empty --name encrypt_existing_data
```

Edit the file with restaurant encryption logic (similar to above).

### Step 4: Apply Migrations

**IMPORTANT**: Apply migrations in this exact order:

```bash
# 1. Apply schema changes (add encrypted fields)
python manage.py migrate customer 0009_add_encrypted_fields
python manage.py migrate restaurant 0009_add_encrypted_fields

# 2. Encrypt existing data
python manage.py migrate customer 0010_encrypt_existing_data
python manage.py migrate restaurant 0010_encrypt_existing_data

# 3. Apply any remaining migrations
python manage.py migrate
```

### Step 5: Verify Encryption

Create a management command to verify encryption:

```bash
python manage.py shell
```

```python
from customer.models import UserProfile
from restaurant.models import Restaurant
from core.encryption import EncryptionManager

# Test UserProfile encryption
profile = UserProfile.objects.first()
print(f"Decrypted name: {profile.full_name}")
print(f"Encrypted name: {profile._full_name_encrypted}")

# Test Restaurant encryption
restaurant = Restaurant.objects.first()
print(f"Decrypted address: {restaurant.address}")
print(f"Encrypted address: {restaurant._address_encrypted}")

# Verify encryption/decryption works
test_data = "Test User Name"
encrypted = EncryptionManager.encrypt(test_data)
decrypted = EncryptionManager.decrypt(encrypted)
print(f"Original: {test_data}")
print(f"Encrypted: {encrypted}")
print(f"Decrypted: {decrypted}")
print(f"Match: {test_data == decrypted}")
```

## Configuration

### Environment Variables

For production, set these in your `.env` file:

```bash
# Django secret key (REQUIRED - keep secure!)
SECRET_KEY=your-super-secret-key-change-this-in-production

# Custom encryption salt (OPTIONAL - for additional security)
ENCRYPTION_SALT=your-custom-encryption-salt-v1

# Database settings
DB_NAME=food_ordering_db
DB_USER=postgres
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432
```

### Security Checklist

- [ ] SECRET_KEY is unique and secure (min 50 characters)
- [ ] SECRET_KEY is stored in environment variables (not in code)
- [ ] ENCRYPTION_SALT is unique per deployment
- [ ] Database backups are encrypted
- [ ] Access logs are enabled and monitored
- [ ] SSL/TLS is enabled for database connections
- [ ] Django admin access is restricted
- [ ] Two-factor authentication is enabled for admin users

## Testing

### Unit Tests

Create tests to verify encryption:

```python
# tests/test_encryption.py
from django.test import TestCase
from customer.models import UserProfile
from restaurant.models import Restaurant
from django.contrib.auth.models import User
from core.encryption import EncryptionManager

class EncryptionTestCase(TestCase):
    """
    Test encryption functionality for sensitive data.
    """
    
    def test_user_profile_encryption(self):
        """Test UserProfile field encryption."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        profile = UserProfile.objects.create(
            user=user,
            full_name='John Doe',
            phone_number='+1234567890',
            address='123 Test St'
        )
        
        # Verify encrypted fields are not plaintext
        self.assertNotEqual(profile._full_name_encrypted, 'John Doe')
        self.assertNotEqual(profile._phone_number_encrypted, '+1234567890')
        self.assertNotEqual(profile._address_encrypted, '123 Test St')
        
        # Verify decryption works
        self.assertEqual(profile.full_name, 'John Doe')
        self.assertEqual(profile.phone_number, '+1234567890')
        self.assertEqual(profile.address, '123 Test St')
    
    def test_restaurant_encryption(self):
        """Test Restaurant field encryption."""
        restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            description='Test description',
            address='456 Restaurant Ave',
            phone='+9876543210',
            email='contact@test.com',
            cuisine_type='italian'
        )
        
        # Verify encrypted fields are not plaintext
        self.assertNotEqual(restaurant._address_encrypted, '456 Restaurant Ave')
        self.assertNotEqual(restaurant._phone_encrypted, '+9876543210')
        self.assertNotEqual(restaurant._email_encrypted, 'contact@test.com')
        
        # Verify decryption works
        self.assertEqual(restaurant.address, '456 Restaurant Ave')
        self.assertEqual(restaurant.phone, '+9876543210')
        self.assertEqual(restaurant.email, 'contact@test.com')
    
    def test_encryption_manager(self):
        """Test EncryptionManager utility functions."""
        test_data = "Sensitive Information"
        
        # Test encryption
        encrypted = EncryptionManager.encrypt(test_data)
        self.assertIsNotNone(encrypted)
        self.assertNotEqual(encrypted, test_data)
        
        # Test decryption
        decrypted = EncryptionManager.decrypt(encrypted)
        self.assertEqual(decrypted, test_data)
        
        # Test None handling
        self.assertIsNone(EncryptionManager.encrypt(None))
        self.assertIsNone(EncryptionManager.decrypt(None))
```

Run tests:

```bash
python manage.py test tests.test_encryption
```

## Rollback Procedure

If you need to rollback the encryption:

### Option 1: Database Restore

```bash
# Restore from backup
psql -U postgres food_ordering_db < backup_before_encryption.sql
```

### Option 2: Migration Rollback

```bash
# Rollback migrations
python manage.py migrate customer 0008  # Previous migration number
python manage.py migrate restaurant 0008
```

## Troubleshooting

### Issue: "ImportError: cannot import name 'PBKDF2'"

**Solution**: The import has been fixed to use `PBKDF2HMAC` instead of `PBKDF2`.

### Issue: Decryption returns None

**Possible Causes**:
1. SECRET_KEY changed after encryption
2. ENCRYPTION_SALT changed after encryption
3. Corrupted data in database

**Solution**:
1. Verify SECRET_KEY and ENCRYPTION_SALT match original values
2. Check database for data corruption
3. Restore from backup if necessary

### Issue: Migration fails with field errors

**Solution**:
1. Ensure data migration runs before schema migration
2. Check for existing data in old fields
3. Review migration dependencies

### Issue: Performance degradation

**Solution**:
1. Add database indexes on frequently queried fields
2. Use `select_related()` and `prefetch_related()` in queries
3. Implement caching for frequently accessed data
4. Consider read replicas for reporting queries

## Monitoring

### What to Monitor

1. **Decryption Failures**
   - Check logs for decryption errors
   - Alert on high failure rates

2. **Performance Metrics**
   - Query response times
   - Database CPU usage
   - Memory usage

3. **Security Events**
   - Failed login attempts
   - Unusual data access patterns
   - Admin actions on encrypted data

### Log Analysis

Check security logs:

```bash
# View security logs
tail -f logs/security.log

# Search for encryption errors
grep "Decryption failed" logs/security.log

# Count encryption operations
grep "Successfully encrypted" logs/security.log | wc -l
```

## Production Deployment

### Pre-Deployment Checklist

- [ ] Full database backup completed
- [ ] Migrations tested in staging environment
- [ ] SECRET_KEY and ENCRYPTION_SALT configured
- [ ] SSL/TLS enabled for all connections
- [ ] Monitoring and alerting configured
- [ ] Rollback procedure documented and tested
- [ ] Team trained on new encryption system
- [ ] Incident response plan updated

### Deployment Steps

1. **Maintenance Window**
   - Schedule during low-traffic period
   - Notify users of planned maintenance
   - Enable maintenance mode

2. **Backup**
   ```bash
   pg_dump -U postgres food_ordering_db > production_backup_$(date +%Y%m%d_%H%M%S).sql
   ```

3. **Deploy Code**
   ```bash
   git pull origin main
   pip install -r requirements.txt
   ```

4. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

5. **Verify**
   ```bash
   python manage.py shell
   # Run verification tests
   ```

6. **Monitor**
   - Watch error logs
   - Check application performance
   - Verify user functionality

7. **Disable Maintenance Mode**
   - Re-enable application
   - Notify users

## Support

### Documentation
- Main documentation: `ENCRYPTION_SECURITY_DOCUMENTATION.md`
- This setup guide: `ENCRYPTION_SETUP_GUIDE.md`
- Code documentation: Inline comments in `core/encryption.py`

### Contact
- **Technical Issues**: dev@tetech.in
- **Security Concerns**: security@tetech.in
- **Emergency**: Follow incident response procedures

## Next Steps

After successful deployment:

1. **Monitor for 24-48 hours**
   - Watch for errors
   - Check performance metrics
   - Verify user reports

2. **Update Documentation**
   - Document any issues encountered
   - Update runbooks
   - Share lessons learned

3. **Security Audit**
   - Schedule security review
   - Test backup/restore procedures
   - Verify compliance requirements

4. **Team Training**
   - Train support team on encryption system
   - Document common issues and solutions
   - Update onboarding materials

---

**Last Updated**: December 2024  
**Version**: 1.0  
**Status**: Ready for Production
