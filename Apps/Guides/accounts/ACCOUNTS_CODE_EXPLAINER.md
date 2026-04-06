# Accounts App - Code Explainer

## Overview
The `accounts` app handles all user-related functionality including authentication, registration, profile management, email verification, and two-factor authentication (2FA).

## File Structure

```
accounts/
├── __init__.py                 # Python package initialization
├── admin.py                   # Django admin configuration
├── auth_views.py              # Authentication-related views
├── email_verification.py      # Email verification functionality
├── forms.py                   # User registration and profile forms
├── forms_preferences.py       # User preference forms
├── models.py                  # Database models for user data
├── urls.py                    # URL routing for accounts app
├── views.py                   # Main view functions
├── views_profile.py           # Profile management views
└── views_verification.py      # Email verification views
```

## Core Components

### 1. Models (models.py)

#### UserProfile Model
**Purpose**: Extends Django's built-in User model with additional profile information.

**Key Features**:
- **Profile Information**: Stores profile picture, bio, phone number, address, date of birth
- **User Preferences**: Newsletter subscription, email notification settings
- **Location Data**: Latitude/longitude for location-based recommendations
- **Verification Status**: Tracks if user account is verified
- **Timestamps**: Creation and update timestamps

**Relationships**:
- One-to-one relationship with Django's User model
- Related through `user.profile` reverse lookup

#### UserFavorite Model
**Purpose**: Allows users to save favorite destinations, tours, and other content.

**Key Features**:
- **Generic Relations**: Can store favorites for any content type (destinations, tours, etc.)
- **User Association**: Links favorites to specific users
- **Timestamp Tracking**: Records when items were favorited

#### UserPreference Model
**Purpose**: Stores user preferences for personalized recommendations.

**Key Features**:
- **Destination Preferences**: JSON field storing preferred destination types
- **Travel Interests**: List of user's travel interests
- **Budget Preferences**: User's budget category preference
- **Recommendation Engine**: Data used for personalized content

### 2. Views Structure

#### auth_views.py
**Purpose**: Handles core authentication operations.

**Key Functions**:
```python
def login_view(request):
    """
    Handles user login with email/username support.
    Includes rate limiting and security checks.
    """

def register_view(request):
    """
    Handles new user registration.
    Sends email verification upon successful registration.
    """

def logout_view(request):
    """
    Logs out user and clears session data.
    Redirects to home page with success message.
    """

def password_reset_view(request):
    """
    Initiates password reset process.
    Sends reset email to user's registered email.
    """
```

#### views.py
**Purpose**: Main user account management views.

**Key Functions**:
```python
def dashboard_view(request):
    """
    User dashboard showing account overview.
    Displays bookings, favorites, and recent activity.
    """

def account_settings_view(request):
    """
    Account settings management page.
    Allows users to update account information.
    """

def delete_account_view(request):
    """
    Handles account deletion requests.
    Includes confirmation and data cleanup.
    """
```

#### views_profile.py
**Purpose**: User profile management functionality.

**Key Functions**:
```python
def profile_view(request, username=None):
    """
    Displays user profile information.
    Shows public profile data and user's content.
    """

def edit_profile_view(request):
    """
    Handles profile editing functionality.
    Updates profile information and preferences.
    """

def upload_profile_picture(request):
    """
    Handles profile picture upload and processing.
    Includes image validation and resizing.
    """
```

#### views_verification.py
**Purpose**: Email verification and account validation.

**Key Functions**:
```python
def send_verification_email(request):
    """
    Sends email verification link to user.
    Generates secure verification token.
    """

def verify_email(request, token):
    """
    Verifies email address using token.
    Updates user verification status.
    """

def resend_verification(request):
    """
    Resends verification email if needed.
    Includes rate limiting to prevent abuse.
    """
```

### 3. Forms Structure

#### forms.py
**Purpose**: User registration and authentication forms.

**Key Forms**:
```python
class CustomUserCreationForm(forms.ModelForm):
    """
    Enhanced user registration form.
    Includes additional validation and field customization.
    """

class CustomAuthenticationForm(forms.Form):
    """
    Custom login form supporting email/username.
    Includes remember me functionality.
    """

class ProfileUpdateForm(forms.ModelForm):
    """
    Form for updating user profile information.
    Handles profile picture upload and validation.
    """
```

#### forms_preferences.py
**Purpose**: User preference and settings forms.

**Key Forms**:
```python
class UserPreferencesForm(forms.ModelForm):
    """
    Form for managing user travel preferences.
    Includes destination types, interests, and budget.
    """

class NotificationSettingsForm(forms.Form):
    """
    Form for managing notification preferences.
    Controls email and push notification settings.
    """

class PrivacySettingsForm(forms.Form):
    """
    Form for managing privacy settings.
    Controls profile visibility and data sharing.
    """
```

### 4. Email Verification System

#### email_verification.py
**Purpose**: Handles email verification workflow.

**Key Functions**:
```python
def generate_verification_token(user):
    """
    Generates secure verification token for email confirmation.
    Uses cryptographic functions for security.
    """

def send_verification_email(user, request):
    """
    Sends verification email with secure link.
    Uses templates for consistent branding.
    """

def verify_token(token):
    """
    Validates verification token and returns user.
    Handles token expiration and security checks.
    """
```

### 5. URL Configuration (urls.py)

**URL Patterns**:
```python
urlpatterns = [
    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profile Management URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/<str:username>/', views.profile_view, name='user_profile'),
    
    # Account Management URLs
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('settings/', views.account_settings_view, name='settings'),
    path('delete/', views.delete_account_view, name='delete_account'),
    
    # Verification URLs
    path('verify-email/', views.send_verification_email, name='send_verification'),
    path('verify/<str:token>/', views.verify_email, name='verify_email'),
    
    # Password Management URLs
    path('password/reset/', views.password_reset_view, name='password_reset'),
    path('password/change/', views.password_change_view, name='password_change'),
]
```

## Key Features

### 1. User Registration & Authentication
- **Email/Username Login**: Supports both email and username for login
- **Secure Registration**: Email verification required for new accounts
- **Password Security**: Strong password requirements and validation
- **Session Management**: Secure session handling with customizable timeouts

### 2. Profile Management
- **Extended Profiles**: Rich profile information beyond basic user data
- **Profile Pictures**: Image upload with validation and processing
- **Location Services**: Optional location data for personalized recommendations
- **Privacy Controls**: User-controlled visibility settings

### 3. Email Verification
- **Secure Tokens**: Cryptographically secure verification tokens
- **Email Templates**: Professional email templates with branding
- **Token Expiration**: Time-limited verification tokens for security
- **Resend Functionality**: Users can request new verification emails

### 4. User Preferences
- **Travel Interests**: Customizable travel preference categories
- **Notification Settings**: Granular control over email and push notifications
- **Recommendation Data**: Preferences used for personalized content
- **Budget Preferences**: Budget category selection for relevant recommendations

### 5. Security Features
- **Rate Limiting**: Prevents brute force attacks on authentication
- **CSRF Protection**: Cross-site request forgery protection
- **Input Validation**: Comprehensive form validation and sanitization
- **Session Security**: Secure session configuration and management

## Database Relationships

```
User (Django built-in)
├── UserProfile (1:1)          # Extended profile information
├── UserFavorite (1:Many)      # User's favorite items
├── UserPreference (1:1)       # User preferences and settings
├── Booking (1:Many)           # User's tour bookings
└── Review (1:Many)            # User's reviews and ratings
```

## Integration Points

### 1. With Other Apps
- **Tours App**: User bookings and tour favorites
- **Destinations App**: Destination favorites and preferences
- **Reviews App**: User-generated reviews and ratings
- **Security App**: Two-factor authentication integration

### 2. External Services
- **Email Service**: SMTP configuration for verification emails
- **Image Processing**: PIL/Pillow for profile picture processing
- **Location Services**: Integration with geocoding services

## Security Considerations

### 1. Data Protection
- **Password Hashing**: Django's built-in password hashing
- **Email Verification**: Required for account activation
- **Data Validation**: Comprehensive input validation
- **File Upload Security**: Secure image upload handling

### 2. Authentication Security
- **Rate Limiting**: Login attempt limitations
- **Session Security**: Secure session configuration
- **CSRF Protection**: Protection against cross-site attacks
- **Token Security**: Secure verification token generation

## Testing

The accounts app includes comprehensive tests for:
- **Model Validation**: User profile and preference model tests
- **View Functionality**: Authentication and profile management tests
- **Form Validation**: User registration and profile form tests
- **Security Testing**: Authentication security and rate limiting tests

## Future Enhancements

Planned improvements include:
- **Social Authentication**: OAuth integration (Google, Facebook, etc.)
- **Advanced 2FA**: TOTP and hardware key support
- **Profile Analytics**: User activity and engagement metrics
- **Advanced Preferences**: Machine learning-based preference detection
