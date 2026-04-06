# Two-Factor Authentication Integration Guide

This document outlines the complete implementation of two-factor authentication (2FA) in the TravelGuide application, explaining how it integrates with the existing login flow, security logging, and account protection features.

## Architecture Overview

The 2FA system is implemented as a multi-layered security feature that integrates with Django's authentication system:

1. **Models Layer**: Stores 2FA settings, secrets, backup codes
2. **Views Layer**: Handles setup, verification, management of 2FA
3. **Middleware Layer**: Enforces 2FA verification across the application
4. **Integration Layer**: Connects with existing login flow and security features

## Key Components

### Security Models

The 2FA system uses several models in `security/models.py`:

- **TwoFactorAuth**: Stores user's 2FA settings, secret key, backup codes
- **SecurityLog**: Records all security events with enhanced event types for 2FA
- **FailedLoginAttempt**: Tracks login failures and handles account lockout

### Security Utilities (`security/utils.py`)

A collection of helper functions for 2FA operations:

- **TOTP Management**: Generate secrets, validate codes, create QR codes
- **Backup Code Management**: Generate secure backup codes, verify them
- **Login Flow Helpers**: Complete login after 2FA verification, clean up sessions
- **IP Address Extraction**: Get client IP reliably for logging purposes

### 2FA Views (`security/views_2fa.py`)

Function-based views that handle all aspects of 2FA:

- **Setup**: Initial setup flow with QR code generation
- **Verification**: Code validation during login process
- **Management**: Enable/disable 2FA, regenerate backup codes
- **Security Dashboard**: Overview of user's security settings and logs

### Login Integration (`accounts/auth_views.py`)

Modified login flow to check for 2FA:

- **UserLoginView**: Enhanced to check if user has 2FA enabled
- If 2FA enabled: Store user ID in session and redirect to verification
- If 2FA not enabled: Complete login normally
- Enhanced security logging for all login events

### Security Middleware (`security/middleware.py`)

Enforces 2FA across the application:

- Intercepts requests to check for partial authentication state
- Redirects to 2FA verification if needed
- Allows access to certain paths without 2FA (static files, 2FA verification page)
- Handles account lockout for failed login attempts

### Test Cases (`security/tests/`)

Comprehensive test coverage:

- **test_twofa.py**: Unit tests for 2FA functionality
- **test_twofa_manual.py**: Integration tests for the complete login flow

## Authentication Flow

### Registration Flow

1. User registers with username, email, and password
2. Account is created with 2FA disabled by default
3. User is logged in immediately
4. Security events are logged

### Login Flow Without 2FA

1. User enters username and password
2. Credentials are verified
3. User is authenticated and logged in
4. Failed attempts are tracked
5. Security events are logged

### Login Flow With 2FA

1. User enters username and password
2. Credentials are verified
3. System detects 2FA is enabled
4. User ID is stored in session
5. User is redirected to 2FA verification page
6. User enters TOTP code or backup code
7. Code is verified
8. If valid, login is completed
9. Security events are logged

### Account Lockout

1. System tracks failed login attempts
2. After 5 failures (configurable), account is temporarily locked
3. Login attempts are blocked during lockout period
4. Security events are logged
5. User is directed to password reset

## Security Features

- **TOTP Implementation**: Industry-standard time-based one-time passwords
- **Backup Codes**: One-time use recovery codes
- **QR Code Generation**: Easy setup with authenticator apps
- **Session Management**: Secure handling of partial authentication state
- **Comprehensive Logging**: All security events are logged with details
- **Account Lockout**: Protection against brute force attacks

## Testing

The 2FA implementation includes comprehensive test cases:

```bash
# Run all security tests
python manage.py test security.tests

# Run specific tests
python manage.py test security.tests.test_twofa
python manage.py test security.tests.test_twofa_manual
```

## Best Practices Implementation

1. **Security in Depth**: Multiple layers of protection
2. **Least Privilege**: Users only access what they need
3. **Fail Secure**: Default to secure state
4. **Clear User Feedback**: Informative messages without revealing sensitive data
5. **Comprehensive Logging**: Audit trail for all security events
6. **Account Recovery**: Backup codes for emergency access

## Future Enhancements

1. **SMS-based 2FA**: Additional verification method
2. **Push Notifications**: Mobile app integration
3. **Hardware Token Support**: YubiKey and similar devices
4. **Risk-based Authentication**: Adaptive security based on context
5. **Session Duration Controls**: Fine-grained session timeout settings
