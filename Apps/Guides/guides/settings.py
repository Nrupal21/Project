"""
Django settings for guides project.

This file contains all the configuration settings for the Django project,
including database settings, installed apps, middleware, templates,
and other Django-specific settings.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# This sets the root directory of the project for file referencing
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
# This function reads variables from .env file and makes them available via os.environ
env_path = os.path.join(BASE_DIR, '.env')
load_dotenv(env_path)

# Debug: Print DB_PORT to verify it's being loaded correctly
print(f"DB_PORT from environment: {os.environ.get('DB_PORT')}")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# This is used for cryptographic signing and should be kept secure
# Get the secret key from environment variables, with a fallback for development
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY', 
    'django-insecure-3d5w9&$zp*0x)ysg5ah18i6!id%!&g1n0j&dp*_j!nh(40n5p%'
)

# SECURITY WARNING: don't run with debug turned on in production!
# Debug mode enables detailed error pages and should be turned off in production
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() == 'true'

# Hosts allowed to access the application
# Parse comma-separated string from environment variable and include ngrok domains
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'tetech.in,www.tetech.in,127.0.0.1,localhost').split(',')

# Add ngrok domain patterns
NGROK_DOMAIN = os.environ.get('NGROK_DOMAIN')
if NGROK_DOMAIN:
    ALLOWED_HOSTS.append(NGROK_DOMAIN)
    ALLOWED_HOSTS.append(f'.{NGROK_DOMAIN}')  # Include all subdomains

# API monitoring configuration
if DEBUG:
    # Default internal IPs for development
    INTERNAL_IPS = ['127.0.0.1', 'localhost']


    
# For development, allow all hosts when DEBUG is True
if DEBUG:
    ALLOWED_HOSTS.extend([
        '.ngrok-free.app',  # All ngrok free domains
        'localhost',
        'tetech.in',
        'www.tetech.in',
        '127.0.0.1',
        '[::1]',  # IPv6 localhost
    ])



# Application definition
# List of Django apps that are enabled in this project
INSTALLED_APPS = [
    'django.contrib.admin',  # Django admin interface
    'django.contrib.auth',   # Authentication system
    'django.contrib.contenttypes',  # Content type framework
    'django.contrib.sessions',     # Session framework
    'django.contrib.messages',     # Messaging framework
    'django.contrib.staticfiles',  # Static file management
    'django.contrib.humanize',     # Humanize data filters
    'django.contrib.sites',        # Sites framework
    
    # Third-party apps
    'rest_framework',             # Django REST Framework for APIs
    'allauth',                    # Authentication, registration, account management
    'allauth.account',            # Account management
    'allauth.socialaccount',      # Social authentication
    'pyotp',                      # TOTP for two-factor authentication
    'qrcode',                     # QR code generation for 2FA
    'django_extensions',          # Django extensions for development
    
    # Project apps
    'core',                       # Core functionality
    'destinations',               # Destination management
    'tours',                      # Tour packages management
    'bookings',                   # Booking management
    'reviews.apps.ReviewsConfig',  # User reviews
    'accounts',                   # User accounts
    'security',                   # Security features and 2FA
    'emergency',                  # Emergency services
    'transportation',             # Transportation options
    'itineraries',                # Travel itineraries
    'rewards.apps.RewardsConfig',  # Reward points system
    'guides.notifications',        # Notification system with indigo/violet styling
    
    # Travel Gallery app - manages and displays travel images with metadata
    # Using the full path to the app config class to ensure proper registration
    'travel_gallery.apps.TravelGalleryConfig',  # Travel photo gallery with image URLs
    'debug_toolbar',  # Django Debug Toolbar for development (without database access)
]

# Middleware configuration - software that processes requests/responses
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',           # Security enhancements
    'django.contrib.sessions.middleware.SessionMiddleware',    # Session support
    'django.middleware.common.CommonMiddleware',               # Common features
    'django.middleware.csrf.CsrfViewMiddleware',               # CSRF protection (must be before AuthenticationMiddleware)
    'django.contrib.auth.middleware.AuthenticationMiddleware', # Authentication
    'django.contrib.messages.middleware.MessageMiddleware',    # User messages
    'django.middleware.clickjacking.XFrameOptionsMiddleware',  # Clickjacking protection
    'security.middleware.SecurityMiddleware',                  # Custom security middleware for tracking logins
    'allauth.account.middleware.AccountMiddleware',           # Django-allauth account middleware
    'core.middleware.APILoggingMiddleware',                   # API request/response logging
]

# The main URL configuration module
ROOT_URLCONF = 'guides.urls'

# Template configuration
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],  # Look for templates in the templates directory
        'APP_DIRS': True,  # Look for templates in the app directories
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.installed_apps',
                'core.context_processors.adsense_settings',  # AdSense context processor
            ],
        },
    },
]

# WSGI application entry point
WSGI_APPLICATION = 'guides.wsgi.application'


# Database configuration
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# PostgreSQL database configuration - Hardcoded for testing
print("\n=== Using Hardcoded Database Configuration ===")

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'guides_db',
        'USER': 'postgres',
        'PASSWORD': 'Devil',
        'HOST': 'localhost',
        'PORT': '5432',
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

# Print the database configuration (without password)
print("=== Database Configuration ===")
db_config = DATABASES['default'].copy()
db_config['PASSWORD'] = '*' * 8 if db_config['PASSWORD'] else 'None'
for key, value in db_config.items():
    print(f"{key}: {value}")
print("==========================\n")


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media files (User uploaded content)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

# File Upload Size Limits
# Increase max upload size for destination images (20MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024  # 20 MB in bytes
FILE_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024  # 20 MB for in-memory file uploads

# Sites Framework Configuration
SITE_ID = 1  # ID of the current site in the django_site table

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Authentication backends
AUTHENTICATION_BACKENDS = (
    'accounts.backends.RoleBasedAuthBackend',  # Our custom role-based auth
    'social_core.backends.google.GoogleOAuth2',   # Google OAuth2
    'social_core.backends.facebook.FacebookOAuth2',  # Facebook OAuth2
    'django.contrib.auth.backends.ModelBackend',  # Fallback to default
)

# Social Auth Settings
SOCIAL_AUTH_URL_NAMESPACE = 'social'
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/'
SOCIAL_AUTH_LOGIN_ERROR_URL = '/accounts/login/'

# Google OAuth2 settings
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ.get('GOOGLE_OAUTH2_KEY', '')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get('GOOGLE_OAUTH2_SECRET', '')

# Facebook OAuth2 settings
SOCIAL_AUTH_FACEBOOK_KEY = os.environ.get('FACEBOOK_APP_ID', '')
SOCIAL_AUTH_FACEBOOK_SECRET = os.environ.get('FACEBOOK_APP_SECRET', '')
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email', 'public_profile']
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
    'fields': 'id, name, email'
}

# Social Auth Pipeline
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)

# Add 'social_django' to INSTALLED_APPS
INSTALLED_APPS = [
    # Django built-in apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',  # For number formatting (intcomma filter)
    
    # Third-party apps
    'social_django',
    'rest_framework',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    
    # Local apps
    'destinations',
    
    # Local apps (only those that exist in the project)
    'accounts',
    'core',
    'tours',
    'bookings',
    'reviews',
    'security',
    'transportation',
    'itineraries',
    'emergency',
    'guides',  # Local guides functionality
]
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
}

# Authentication settings
AUTHENTICATION_BACKENDS = [
    # Custom two-factor authentication backend
    'security.auth.TwoFactorAuthBackend',  # Our custom auth backend for 2FA
    'django.contrib.auth.backends.ModelBackend',  # Django's default auth backend
    'allauth.account.auth_backends.AuthenticationBackend',  # AllAuth backend
]

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Email configuration
# ------------------
# These settings configure how Django sends emails (for password resets, notifications, etc.)
# All settings are loaded from environment variables for security

# The backend implementation to use for sending emails
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND', 
    'django.core.mail.backends.smtp.EmailBackend'
)

# Host for sending emails (SMTP server)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.example.com')

# Port for sending email
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))

# Whether to use TLS when connecting to the SMTP server
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'

# Username to use for the SMTP server
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')

# Password to use for the SMTP server
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# Default 'from' email address
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'no-reply@tetech.in')

# Security Settings
# ----------------
# CSRF and session security settings loaded from environment variables
# These should be set to True in production with HTTPS

# CSRF settings
CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE', 'False').lower() == 'true'
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript to read the CSRF cookie
CSRF_USE_SESSIONS = False  # Store CSRF token in cookie, not session
CSRF_COOKIE_SAMESITE = 'Lax'  # Can be 'Lax', 'Strict', or 'None'
CSRF_FAILURE_VIEW = 'django.views.csrf.csrf_failure'  # Default CSRF failure view

# Trusted origins for CSRF and CORS
CSRF_TRUSTED_ORIGINS = [
    'https://tetech.in',
    'https://www.tetech.in',
    'http://tetech.in',
    'http://www.tetech.in',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost',
    'http://127.0.0.1',
    'https://*.ngrok-free.app',  # For ngrok URLs
    'http://*.ngrok-free.app',   # For non-HTTPS ngrok URLs
]

# Ensure CSRF cookie is sent with every request
CSRF_COOKIE_DOMAIN = None  # Set to None for local development
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'

# Session settings (related to CSRF)
SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Whether to use a secure cookie for the session
SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'

# Security settings for two-factor authentication
# ------------------------------------------

# Maximum failed login attempts before account lockout
MAX_LOGIN_ATTEMPTS = 5

# Login lockout duration in minutes
LOCKOUT_DURATION = 30

# Two-factor authentication settings
TWOFA_ISSUER_NAME = 'TravelGuide'

# Number of backup codes to generate for 2FA
TWOFA_BACKUP_CODES_COUNT = 10

# Security log settings
SECURITY_LOG_RETENTION_DAYS = 90  # How long to keep security logs

# Session security settings
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Expire session when browser closes
SESSION_COOKIE_AGE = 600  # Session timeout in seconds (10 minutes)
SESSION_SAVE_EVERY_REQUEST = True  # Reset session timeout on each request

# Content security policy settings
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'  # Prevent clickjacking

# Google AdSense Configuration
# ---------------------------
# Publisher ID for Google AdSense (replace with your actual AdSense Publisher ID)
GOOGLE_ADSENSE_PUBLISHER_ID = os.environ.get('GOOGLE_ADSENSE_PUBLISHER_ID', 'ca-pub-3458812139504498')

# Enable or disable AdSense globally
ADSENSE_ENABLED = os.environ.get('ADSENSE_ENABLED', 'True').lower() == 'true'

# Email Configuration
# ------------------------------------------------------------------------------
# These settings configure Django's email functionality for sending verification emails,
# password reset links, notifications, and other user communications.
# Settings are loaded from environment variables (.env file)

# The backend used to send emails
# This setting determines how Django sends emails (SMTP, console, file-based, etc.)
# For development testing, we'll use console email backend for immediate visibility
# of email content in the console output
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# For file-based email backend (commented out for now)
# EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = os.path.join(BASE_DIR, 'sent_emails')

# SMTP server hostname used for sending emails
# For Gmail, this should be 'smtp.gmail.com'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')

# Port number for the SMTP server
# Common ports: 587 (TLS), 465 (SSL), 25 (non-encrypted)
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))

# Whether to use TLS encryption when connecting to the SMTP server
# TLS (Transport Layer Security) encrypts the connection for security
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'

# Whether to use SSL encryption when connecting to the SMTP server
# This is an alternative to TLS and shouldn't be used simultaneously with TLS
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False').lower() == 'true'

# Username for SMTP authentication (usually the email address)
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')

# Password for SMTP authentication
# For Gmail, this should be an app password, not your regular password
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# Email address used as the 'from' address if not specified
# This will be the sender address shown to recipients
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

# Email address that error messages come from
SERVER_EMAIL = os.environ.get('SERVER_EMAIL', DEFAULT_FROM_EMAIL)

# Subject-line prefix for admin emails
EMAIL_SUBJECT_PREFIX = os.environ.get('EMAIL_SUBJECT_PREFIX', '[TravelGuide] ')

# Google Maps Configuration
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')
if not GOOGLE_MAPS_API_KEY and DEBUG:
    print('WARNING: GOOGLE_MAPS_API_KEY is not set. Google Maps will not work properly.')

# Ad slot IDs for different positions (replace with your actual ad unit IDs)
GOOGLE_ADSENSE_SLOTS = {
    'header': os.environ.get('ADSENSE_HEADER_SLOT', 'ca-pub-3458812139504498'),
    'sidebar': os.environ.get('ADSENSE_SIDEBAR_SLOT', 'xxxxxxxxxx'),
    'footer': os.environ.get('ADSENSE_FOOTER_SLOT', 'xxxxxxxxxx'),
    'in_article': os.environ.get('ADSENSE_IN_ARTICLE_SLOT', 'xxxxxxxxxx'),
}

# -----------------------------------------------------------------------------
# Logging Configuration
# -----------------------------------------------------------------------------
# This comprehensive logging configuration controls how Django logs messages
# throughout the application. It defines handlers, formatters, and loggers for
# different components with appropriate verbosity levels.

# Create logs directory if it doesn't exist
import os
logs_dir = os.path.join(BASE_DIR, 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Ensure logs directory exists
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Logging configuration
LOGGING = {
    # Version of the logging configuration schema
    'version': 1,
    
    # Whether existing loggers should be disabled when this config is used
    'disable_existing_loggers': False,
    
    # Formatters specify the layout of log records
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'api': {
            'format': '{asctime} - {levelname} - {message}',
            'style': '{',
        },
    },
    
    # Define log record formatters with different verbosity levels
    'formatters': {
        # Standard formatter with timestamp, level and message
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        # Verbose formatter with more context information for debugging
        'verbose': {
            'format': '%(asctime)s [%(levelname)s] %(name)s (%(pathname)s:%(lineno)d): %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        # Simple formatter for console output with color-coded level indicators
        'colored': {
            'format': '\033[1;36m%(asctime)s\033[0m [%(levelname)s] \033[1;33m%(name)s\033[0m: %(message)s',
            'datefmt': '%H:%M:%S',
        },
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'verbose': {
            'format': '%(asctime)s [%(levelname)s] %(name)s (%(pathname)s:%(lineno)d): %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    
    # Define handlers that determine where log messages go
    'handlers': {
        # API log file handler
        'api_file': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'api.log'),
            'when': 'midnight',
            'backupCount': 30,  # Keep 30 days of logs
            'formatter': 'verbose',
        },
        # Console handler for development
        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'colored',
        },
        # File handler for API logs
        'file': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(logs_dir, 'api.log'),
            'formatter': 'api',
        },
        # Handler for general application logs in a rotating file
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(logs_dir, 'travelguide.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB per file
            'backupCount': 5,  # Keep 5 backup files
            'formatter': 'standard',
        },
        # Handler specifically for security-related logs
        'security_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(logs_dir, 'security.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB per file
            'backupCount': 5,  # Keep 5 backup files
            'formatter': 'verbose',  # More detailed format for security logs
        },
        # Handler for registration process logs
        'registration_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(logs_dir, 'registration.log'),
            'maxBytes': 1024 * 1024 * 2,  # 2 MB per file
            'backupCount': 3,  # Keep 3 backup files
            'formatter': 'verbose',
        },
        # Handler for sending critical errors via email to admins
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,  # Include HTML content for better readability
        },
    },
    
    # Define loggers for different components of the application
    'loggers': {
        # Root logger that captures all logs not caught by other loggers
        '': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        # API logger
        'api': {
            'handlers': ['console', 'api_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        # Django request logger
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'WARNING',
            'propagate': False,
        },
        # Django's internal logger
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        # Django security subsystem logger
        'django.security': {
            'handlers': ['console', 'security_file', 'mail_admins'],
            'level': 'INFO',
            'propagate': False,
        },
        # Database queries logger (very verbose, enable only when debugging DB issues)
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',  # Set to DEBUG to see all SQL queries
            'propagate': False,
        },
        # Our accounts app logger with special focus on registration
        'accounts': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        # Specific logger for the registration process
        'accounts.auth_views': {
            'handlers': ['console', 'registration_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        # Security app logger
        'security': {
            'handlers': ['console', 'security_file', 'mail_admins'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

