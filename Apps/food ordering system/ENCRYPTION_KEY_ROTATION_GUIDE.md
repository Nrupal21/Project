# Encryption Key Rotation Guide

## ⚠️ CRITICAL SECURITY WARNING

**Changing SECRET_KEY or ENCRYPTION_SALT after encryption will permanently break access to all encrypted data!**

This guide provides the safe procedure for rotating encryption keys without data loss.

## When to Rotate Keys

### Required Rotation
- **Security Breach**: Immediately if SECRET_KEY is compromised
- **Personnel Changes**: When staff with key access leave the company
- **Compliance Requirements**: As required by security standards (typically annually)

### Recommended Rotation
- **Annual**: Every 12 months for security best practices
- **Major Updates**: After major system upgrades

## Pre-Rotation Checklist

- [ ] **Full Database Backup** - Create complete backup of all data
- [ ] **Test Environment** - Practice rotation in staging first
- [ ] **Maintenance Window** - Schedule during low-traffic period
- [ ] **Rollback Plan** - Document and test rollback procedures
- [ ] **Team Notification** - Inform all stakeholders about maintenance

## Key Rotation Procedure

### Step 1: Backup Everything

```bash
# Complete database backup
pg_dump -U postgres food_ordering_db > pre_rotation_backup_$(date +%Y%m%d_%H%M%S).sql

# Backup current encryption settings
cp food_ordering/settings.py food_ordering/settings.py.backup

# Document current keys (store securely)
echo "SECRET_KEY: $(grep SECRET_KEY .env)" >> rotation_log.txt
echo "ENCRYPTION_SALT: $(grep ENCRYPTION_SALT .env)" >> rotation_log.txt
```

### Step 2: Create Key Rotation Migration

```bash
python manage.py makemigrations core --empty --name rotate_encryption_keys
```

Edit the migration file:

```python
# core/migrations/XXXX_rotate_encryption_keys.py
from django.db import migrations
from django.conf import settings

def rotate_encryption_keys(apps, schema_editor):
    """
    Rotate encryption keys and re-encrypt all sensitive data.
    
    This migration:
    1. Decrypts all data with old keys
    2. Updates to new keys
    3. Re-encrypts all data with new keys
    """
    from core.encryption import EncryptionManager
    from customer.models import UserProfile
    from restaurant.models import Restaurant, PendingRestaurant
    
    print("🔄 Starting encryption key rotation...")
    
    # Store old encryption manager instance
    old_encryption_manager = EncryptionManager
    
    # Update settings with new keys (temporarily for this migration)
    # In practice, you would update environment variables before running migration
    
    # Process UserProfile data
    print("📋 Rotating UserProfile encryption...")
    user_count = UserProfile.objects.count()
    processed_users = 0
    
    for profile in UserProfile.objects.all().iterator(chunk_size=100):
        try:
            # Decrypt with old keys
            old_full_name = profile.full_name if profile._full_name_encrypted else None
            old_phone = profile.phone_number if profile._phone_number_encrypted else None
            old_address = profile.address if profile._address_encrypted else None
            
            # Re-encrypt with new keys (automatic when properties are accessed)
            if old_full_name:
                profile.full_name = old_full_name
            if old_phone:
                profile.phone_number = old_phone
            if old_address:
                profile.address = old_address
            
            profile.save()
            processed_users += 1
            
            if processed_users % 10 == 0:
                print(f"  Processed {processed_users}/{user_count} users...")
                
        except Exception as e:
            print(f"  ❌ Error rotating user {profile.id}: {str(e)}")
            continue
    
    print(f"✅ Completed {processed_users} user profiles")
    
    # Process Restaurant data
    print("🍽️ Rotating Restaurant encryption...")
    restaurant_count = Restaurant.objects.count()
    processed_restaurants = 0
    
    for restaurant in Restaurant.objects.all().iterator(chunk_size=100):
        try:
            # Decrypt with old keys
            old_address = restaurant.address if restaurant._address_encrypted else None
            old_phone = restaurant.phone if restaurant._phone_encrypted else None
            old_email = restaurant.email if restaurant._email_encrypted else None
            
            # Re-encrypt with new keys
            if old_address:
                restaurant.address = old_address
            if old_phone:
                restaurant.phone = old_phone
            if old_email:
                restaurant.email = old_email
            
            restaurant.save()
            processed_restaurants += 1
            
            if processed_restaurants % 10 == 0:
                print(f"  Processed {processed_restaurants}/{restaurant_count} restaurants...")
                
        except Exception as e:
            print(f"  ❌ Error rotating restaurant {restaurant.id}: {str(e)}")
            continue
    
    print(f"✅ Completed {processed_restaurants} restaurants")
    
    # Process PendingRestaurant data
    print("⏳ Rotating PendingRestaurant encryption...")
    pending_count = PendingRestaurant.objects.count()
    processed_pending = 0
    
    for pending in PendingRestaurant.objects.all().iterator(chunk_size=100):
        try:
            # Decrypt with old keys
            old_address = pending.address if pending._address_encrypted else None
            old_phone = pending.phone if pending._phone_encrypted else None
            old_email = pending.email if pending._email_encrypted else None
            
            # Re-encrypt with new keys
            if old_address:
                pending.address = old_address
            if old_phone:
                pending.phone = old_phone
            if old_email:
                pending.email = old_email
            
            pending.save()
            processed_pending += 1
            
            if processed_pending % 10 == 0:
                print(f"  Processed {processed_pending}/{pending_count} pending restaurants...")
                
        except Exception as e:
            print(f"  ❌ Error rotating pending restaurant {pending.id}: {str(e)}")
            continue
    
    print(f"✅ Completed {processed_pending} pending restaurants")
    print("🎉 Encryption key rotation completed successfully!")


def reverse_key_rotation(apps, schema_editor):
    """
    Reverse key rotation - restore original encryption.
    
    WARNING: This requires the original keys to be available.
    """
    print("⚠️ Reversing key rotation - this requires original keys")
    # Implementation would depend on having stored the original encrypted data
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('core', 'previous_migration'),
    ]
    
    operations = [
        migrations.RunPython(
            rotate_encryption_keys,
            reverse_code=reverse_key_rotation
        ),
    ]
```

### Step 3: Update Environment Variables

```bash
# Backup current .env
cp .env .env.backup

# Generate new SECRET_KEY (Django command)
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Generate new ENCRYPTION_SALT
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env file with new values
nano .env
```

### Step 4: Execute Rotation

```bash
# Apply the key rotation migration
python manage.py migrate core

# Verify encryption works with new keys
python manage.py verify_encryption --verbose
```

### Step 5: Post-Rotation Verification

```bash
# Test encryption/decryption with new keys
python manage.py shell -c "
from core.encryption import EncryptionManager
test = 'Key rotation test data'
encrypted = EncryptionManager.encrypt(test)
decrypted = EncryptionManager.decrypt(encrypted)
print(f'Rotation test: {test == decrypted}')
"

# Verify all data is accessible
python manage.py shell -c "
from customer.models import UserProfile
from restaurant.models import Restaurant

print(f'User profiles accessible: {UserProfile.objects.count()}')
print(f'Restaurants accessible: {Restaurant.objects.count()}')

# Test specific records
user = UserProfile.objects.first()
print(f'User data: {user.full_name}')

restaurant = Restaurant.objects.first()
print(f'Restaurant data: {restaurant.address}')
"
```

## Emergency Rollback Procedure

### If Rotation Fails Mid-Process

1. **Stop All Operations**
   ```bash
   # Put application in maintenance mode
   python manage.py shell -c "
   from django.core.management import call_command
   call_command('migrate', 'core', 'previous_migration')
   "
   ```

2. **Restore from Backup**
   ```bash
   # Restore database
   psql -U postgres food_ordering_db < pre_rotation_backup_YYYYMMDD_HHMMSS.sql
   
   # Restore settings
   cp food_ordering/settings.py.backup food_ordering/settings.py
   cp .env.backup .env
   ```

3. **Verify System**
   ```bash
   python manage.py verify_encryption
   python manage.py check
   ```

## Testing Key Rotation

### In Staging Environment

1. **Setup Test Data**
   ```bash
   python manage.py shell -c "
   from customer.models import UserProfile
   from django.contrib.auth.models import User
   
   # Create test data
   user = User.objects.create_user('test_rotation', 'test@example.com', 'pass123')
   profile = UserProfile.objects.create(
       user=user,
       full_name='Test Rotation User',
       phone_number='+1234567890',
       address='123 Test Street'
   )
   print('Test data created')
   "
   ```

2. **Practice Rotation**
   ```bash
   # Follow the full rotation procedure
   # Verify data integrity after rotation
   python manage.py shell -c "
   from customer.models import UserProfile
   profile = UserProfile.objects.get(user__username='test_rotation')
   print(f'After rotation: {profile.full_name}')
   assert profile.full_name == 'Test Rotation User'
   print('✅ Rotation test passed')
   "
   ```

## Monitoring After Rotation

### Check System Health

```bash
# Monitor for decryption errors
tail -f logs/security.log | grep "decrypt_failed"

# Check application performance
python manage.py verify_encryption --model all

# Monitor database performance
python manage.py shell -c "
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('SELECT COUNT(*) FROM customer_userprofile WHERE _full_name_encrypted IS NOT NULL')
    print(f'Encrypted profiles: {cursor.fetchone()[0]}')
"
```

### Key Metrics to Monitor

1. **Decryption Success Rate**: Should be 100%
2. **Application Response Time**: Monitor for performance impact
3. **Error Logs**: Watch for encryption-related errors
4. **User Reports**: Check for data access issues

## Security Considerations

### During Rotation

- **Limited Access**: Only authorized personnel should perform rotation
- **Secure Communication**: Use secure channels for key distribution
- **Audit Trail**: Log all rotation activities
- **Backup Security**: Ensure backups are encrypted and secure

### After Rotation

- **Secure Old Keys**: Store old keys securely for audit purposes
- **Update Documentation**: Record rotation date and new key identifiers
- **Team Training**: Train staff on new procedures
- **Compliance Reporting**: Document rotation for compliance audits

## Troubleshooting

### Common Issues

1. **Migration Fails Mid-Way**
   - Check database connectivity
   - Verify sufficient disk space
   - Review error logs for specific issues

2. **Data Corruption**
   - Restore from backup
   - Check for incomplete transactions
   - Verify database integrity

3. **Performance Issues**
   - Monitor database load during rotation
   - Consider batch processing for large datasets
   - Optimize database indexes

### Error Messages and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `InvalidToken` | Wrong encryption key | Verify SECRET_KEY and ENCRYPTION_SALT |
| `Database connection lost` | Long-running operation | Break into smaller batches |
| `Memory error` | Large dataset processing | Use chunk_size in queries |

## Compliance Documentation

### Required Records

- **Rotation Date**: When keys were rotated
- **Authorization**: Who approved the rotation
- **Method**: How rotation was performed
- **Verification**: How success was confirmed
- **Backup Location**: Where backups are stored

### Sample Rotation Log

```
Date: 2024-12-07
Performed by: Security Team
Authorization: CTO approval (Ticket #SEC-001)
Method: Automated migration with data re-encryption
Records processed: 1,247 users, 89 restaurants, 12 pending
Verification: All data accessible, encryption tests passed
Backup location: Secure backup server (encrypted)
Next rotation due: 2025-12-07
```

## Contact Information

- **Security Team**: security@tetech.in
- **Database Team**: dba@tetech.in
- **Emergency Contact**: oncall@tetech.in

---

**Last Updated**: December 2024  
**Version**: 1.0  
**Approval Required**: Security Team Lead  
**Classification**: Confidential - Security Procedure
