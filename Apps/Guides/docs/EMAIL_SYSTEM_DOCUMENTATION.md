# TravelGuide Email System Documentation

## Overview

This document outlines the email system in the TravelGuide project, including the centralized email utility, standardized templates, and implementation across different features.

## Email Configuration

The email system uses Django's built-in email functionality, configured in `settings.py`:

```python
# Email Configuration
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@travelguide.com')
```

## Centralized Email System

### Core Email Utility

The centralized email utility in `core/email_utils.py` provides standardized email functionality across the application.

```python
send_templated_email(recipient_email, subject, template_name, context, from_email=None)
```

**Key Features:**
- Single entry point for all email sending operations
- Supports single recipient or list of recipients
- Renders HTML templates with context variables
- Creates plain text fallback from HTML content
- Robust error handling and detailed logging
- Consistent template naming convention

### Admin Notification Utility

The `send_admin_notification` function in `core/email_utils.py` sends notifications to admin/staff users.

```python
send_admin_notification(subject, message, html_message=None)
```

**Key Features:**
- Automatically targets all staff/admin users
- Filters out users without email addresses
- Supports both plain text and HTML messages
- Comprehensive error logging
- Non-blocking operation

## Email Templates

Email templates are located in `templates/emails/` with feature-specific subdirectories. The template system includes:

### Base Template
- `base_email.html`: Foundation template with responsive styling for all emails

### Account Templates
- `emails/welcome.html`: Welcome email for new user registrations
- `emails/password_reset.html`: Password reset instructions with secure token
- `emails/guide_application_confirmation.html`: Confirmation for guide applications

### Booking Templates
- `emails/booking_confirmation.html`: Booking confirmation with details and next steps

### Destination Templates
- `emails/destinations/destination_submitted.html`: Admin notification for new destinations
- `emails/destinations/destination_approved.html`: Guide notification for approved destinations
- `emails/destinations/destination_rejected.html`: Guide notification for rejected destinations
- `emails/destinations/guide_submission_confirmation.html`: Confirmation of destination submission

All templates use Tailwind CSS styling consistent with the project's indigo/violet color scheme and responsive design for mobile compatibility.

## Implementation Across Features

### User Registration
- Uses `send_welcome_email` function in `accounts/utils.py`
- Sends welcome email with account activation instructions
- Leverages the centralized email utility

### Password Reset
- Implemented in `accounts/auth_views.py` as custom views
- Uses `send_password_reset_email` function in `accounts/utils.py`
- Generates secure tokens with proper expiration

### Booking System
- Implemented in `bookings/utils.py` with multiple notification types:
  - `send_booking_confirmation_email`: Sent after successful booking/payment
  - `send_booking_update_email`: Sent when booking details are updated
  - `send_guide_booking_notification`: Notifies guides of new bookings

### Destination Submission Workflow
- Implemented in `destinations/utils/email_notifications.py`:
  - `send_destination_submission_notification`: Notifies admins of new submissions
  - `send_destination_approved_notification`: Notifies guides of approval
  - `send_destination_rejected_notification`: Notifies guides of rejection with feedback
  - `send_guide_submission_confirmation`: Confirms receipt of submission

## Error Handling Features

The email system includes comprehensive error handling:

1. All email operations wrapped in try-except blocks
2. Detailed logging at info, warning, and error levels
3. Non-blocking operation to prevent failed emails from disrupting workflows
4. Template existence verification with fallback to plain text
5. Configuration validation before email sending attempts
6. User feedback messages based on email sending status

## Testing Email Functionality

Multiple test scripts have been created to verify email functionality:

### Basic Email Testing
```python
python manage.py shell < test_basic_email.py
```
Tests direct email sending using Django's `send_mail`

### Console Email Testing
```python
python manage.py shell < test_console_email.py
```
Tests email output to console using the console backend

### Comprehensive Email Testing
```python
python manage.py shell < test_email_functionality.py
```
Tests all email functions including:
1. Welcome emails
2. Password reset emails
3. Booking confirmation emails
4. Destination submission notifications
5. Admin notifications

## Common Email Issues and Solutions

### Email Not Being Sent

1. **Configuration Issues**: Verify that all email environment variables are properly set in `.env` file
2. **SMTP Server Access**: Ensure the application server can connect to the SMTP server
3. **Authentication Issues**: Check that email credentials are correct and not expired
4. **Network Issues**: Verify that outbound connections to the SMTP port are allowed
5. **Rate Limiting**: Check if the email provider is rate-limiting sending operations

### Email Templates Not Found

1. **Template Location**: Ensure templates are in the correct directory structure
   - All templates should be in `templates/emails/` or appropriate subdirectories
   - Template paths in code should match actual file locations
2. **Django Template Settings**: Verify template directories are properly configured in settings
3. **Template Name Typos**: Check for exact match in template names

### Email Content Issues

1. **Context Variables**: Ensure all required context variables are passed to templates
2. **Missing Images**: Check that image paths in templates are absolute and accessible
3. **CSS Compatibility**: Email-specific CSS may not work in all email clients

## Logging

Email-related events are logged to provide visibility and troubleshooting:

- **Info Level**: Successful email sending operations
- **Warning Level**: Non-critical issues that might affect email delivery
- **Error Level**: Failed email attempts with exception details
- **Debug Level**: Detailed information about email parameters for troubleshooting

Logs can be found in:
- `logs/travelguide.log`: General application logs
- `logs/api.log`: API-related email operations
- `logs/security.log`: Security-related emails (password resets, etc.)

For email debugging, you can temporarily set:
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

## Best Practices

1. **Always use the centralized email utility**: Never use Django's `send_mail` directly
2. **Handle email failures gracefully**: Don't let email failures break main workflows
3. **Log all email operations**: Both successes and failures should be logged
4. **Test with multiple email clients**: Test templates with Gmail, Outlook, mobile apps
5. **Keep templates consistent**: Follow the established naming and directory structure
6. **Use inline CSS**: Email clients have limited CSS support, so inline styles are recommended

## Future Improvements

Potential future improvements to the email system:

1. **Asynchronous email sending**: Implement Celery tasks for non-blocking email operations
2. **Email queue system**: Create a retry mechanism for failed email attempts
3. **Email preview system**: Develop admin interface for previewing email templates
4. **Email tracking**: Add functionality to monitor delivery and open rates
5. **Internationalization**: Support for email templates in multiple languages
6. **Email preferences**: Allow users to manage their email notification preferences
