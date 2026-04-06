# Login Implementation Guide

This document provides a comprehensive guide to the login system implementation in the TravelGuide application, including authentication flow, 2FA, and role-based access control.

## Table of Contents
- [Authentication Flow](#authentication-flow)
- [Two-Factor Authentication (2FA)](#two-factor-authentication-2fa)
- [Role-Based Access Control](#role-based-access-control)
- [Security Features](#security-features)
- [Error Handling](#error-handling)
- [Testing](#testing)

## Authentication Flow

### 1. User Login
- **Endpoint**: `/accounts/login/`
- **View**: `security.views.user_login`
- **Template**: `security/login.html`
- **Form**: `UserLoginForm`

#### Process:
1. User submits login form with username/email and password
2. System validates credentials against database
3. If valid, check if 2FA is enabled for the user
4. If 2FA is enabled, redirect to 2FA verification
5. If 2FA is not enabled, log the user in and redirect to appropriate dashboard

### 2. 2FA Verification (if enabled)
- **Endpoint**: `/security/two-factor/verify/`
- **View**: `TwoFactorVerifyView`
- **Template**: `security/two_factor_verify.html`

#### Process:
1. User enters TOTP code from authenticator app
2. System verifies code against stored secret
3. If valid, complete login process
4. If invalid, show error message and allow retry
5. After 3 failed attempts, account may be temporarily locked

## Two-Factor Authentication (2FA)

### Setup Process
1. User navigates to security settings
2. Clicks "Enable 2FA"
3. Scans QR code with authenticator app
4. Verifies setup by entering a code
5. Receives backup codes

### Key Components
- **TOTP Implementation**: Uses `pyotp` for time-based one-time passwords
- **Secret Storage**: Encrypted in database using `TwoFactorAuth` model
- **Backup Codes**: 10 one-time use codes stored hashed in database

### Views
- `TwoFactorSetupView`: Initial 2FA setup with QR code
- `TwoFactorConfirmView`: Verify 2FA setup
- `TwoFactorVerifyView`: Verify 2FA during login
- `TwoFactorManageView`: Manage 2FA settings

## Role-Based Access Control

### User Roles
1. **Admin**: Full system access
2. **Manager**: Can manage content and users
3. **Staff**: Limited backend access
4. **User**: Basic access (default)

### Permission System
- **Module-based permissions** (e.g., 'destinations', 'tours')
- **Action-based permissions** (e.g., 'create', 'read', 'update', 'delete')
- **Role assignments** stored in `RoleAssignment` model

### Checking Permissions
```python
# In views
@login_required
@permission_required('destinations', 'create')
def create_destination(request):
    # View logic here
    pass

# In templates
{% if user|has_permission:'destinations.create' %}
    <!-- Show create button -->
{% endif %}
```

## Security Features

### Account Protection
- Rate limiting for login attempts
- Account lockout after multiple failed attempts
- Session management with configurable timeout
- CSRF protection
- Password hashing with PBKDF2

### Security Logging
All security-relevant actions are logged in the `SecurityLog` model, including:
- Login/logout events
- Failed login attempts
- 2FA setup and verification
- Role and permission changes

## Error Handling

### Common Error Scenarios
1. **Invalid Credentials**
   - Message: "Invalid username or password"
   - Action: Show error on login form

2. **Account Locked**
   - Message: "Account temporarily locked. Please try again later."
   - Action: Prevent login attempts for configured duration

3. **2FA Verification Failed**
   - Message: "Invalid verification code. X attempts remaining."
   - Action: Allow retry until max attempts reached

4. **Insufficient Permissions**
   - Message: "You don't have permission to access this page."
   - Action: Redirect to access denied page

## Testing

### Test Cases
1. **Login Tests**
   - Successful login with correct credentials
   - Failed login with incorrect credentials
   - Account lockout after multiple failed attempts

2. **2FA Tests**
   - Successful 2FA setup
   - Successful login with 2FA
   - Failed 2FA verification
   - Backup code usage

3. **Role Tests**
   - Permission enforcement
   - Role-based redirects
   - Access control for protected views

### Running Tests
```bash
# Run all security tests
python manage.py test security.tests

# Run specific test case
python manage.py test security.tests.test_twofa_manual.TestTwoFactorLoginFlow
```

## Troubleshooting

### Common Issues
1. **2FA Not Working**
   - Verify system time is synchronized (TOTP is time-sensitive)
   - Check if 2FA is properly set up for the user
   - Verify the secret key in the database

2. **Login Loop**
   - Check session configuration in settings.py
   - Verify middleware order
   - Check for infinite redirects in login/logout views

3. **Permission Issues**
   - Verify role assignments
   - Check permission strings in code
   - Check middleware processing order

## Related Documentation
- [Security Implementation Guide](./SECURITY_IMPLEMENTATION.md)
- [User Management Guide](./USER_MANAGEMENT.md)
- [API Authentication Guide](./API_AUTHENTICATION.md)
