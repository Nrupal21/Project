# TravelGuide Security Module

This module provides comprehensive security features for the TravelGuide Django application, including two-factor authentication, failed login attempt tracking, account lockout policies, and security event logging.

## Features

### Two-Factor Authentication (2FA)

- Supports authenticator app (TOTP) based verification
- Generates backup codes for account recovery
- Enforces 2FA via middleware for protected routes
- QR code generation for easy setup with authenticator apps

### Login Security

- Tracks failed login attempts by username and IP address
- Implements account lockout after multiple failed attempts
- Provides password reset workflows for locked accounts
- Verifies account status during login process

### Security Logging

- Comprehensive event logging for security-relevant actions
- Tracks login attempts (successful, failed, blocked)
- Records 2FA-related events (setup, verification, disabling)
- Stores IP address and user agent for security auditing

### Security Dashboard

- Displays security status and recommendations
- Shows recent security events and login history
- Manages two-factor authentication settings
- Provides backup code management

## Technical Implementation

### Key Components

1. **Security Middleware**
   - Enforces 2FA verification for protected routes
   - Blocks login attempts for locked accounts
   - Logs security-relevant events

2. **Login View Integration**
   - Seamlessly integrates with Django's authentication system
   - Redirects to 2FA verification when required
   - Tracks and limits failed login attempts

3. **Two-Factor Authentication Models**
   - Stores TOTP secrets securely
   - Manages backup codes for account recovery
   - Tracks verification status

4. **Security Logging System**
   - Structured event logging
   - Multiple severity levels
   - Searchable and filterable logs

## Usage Flow

### User Registration
1. User creates an account
2. Account is created with 2FA disabled by default

### Setting Up Two-Factor Authentication
1. User navigates to security settings
2. User enables 2FA and selects authentication method
3. User scans QR code with authenticator app
4. User verifies setup with generated code
5. System provides backup codes for safekeeping

### Login with 2FA
1. User enters username and password
2. If credentials are valid and 2FA is enabled:
   - Session marks user for 2FA verification
   - User is redirected to 2FA verification page
3. User enters code from authenticator app or backup code
4. If code is valid:
   - 2FA verification is completed
   - User is fully authenticated and redirected to original destination

### Failed Login Handling
1. System tracks each failed login attempt
2. After configurable number of failures (default: 5):
   - Account is temporarily locked
   - User is informed of lockout and duration
   - Security event is logged
3. During lockout period:
   - Login attempts are automatically rejected
   - User is directed to password reset

## Configuration Settings

The following settings can be customized in settings.py:

```python
# Two-Factor Authentication
TWOFA_ISSUER_NAME = 'TravelGuide'  # Name shown in authenticator apps
TWOFA_BACKUP_CODES_COUNT = 10  # Number of backup codes to generate

# Login Security
MAX_LOGIN_ATTEMPTS = 5  # Number of attempts before lockout
LOCKOUT_DURATION = 30  # Lockout duration in minutes
```

## Security Best Practices

- Always use HTTPS in production
- Set secure cookies and use proper CSRF protection
- Implement proper error handling to prevent information leakage
- Regularly review security logs for suspicious activity
- Consider additional protection for admin interfaces

## Testing

Comprehensive test cases are provided in the `tests` directory:

```bash
# Run all security tests
python manage.py test security.tests

# Run specific test modules
python manage.py test security.tests.test_twofa
```
