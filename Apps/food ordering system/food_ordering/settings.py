"""
Django settings for food_ordering project.
Generated for Django 4.2+ with production-ready configurations.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-development-key-change-in-production')

# ============================================
# ENCRYPTION CONFIGURATION
# ============================================
# Field-level encryption for sensitive user data
# Uses Fernet symmetric encryption (AES-128 in CBC mode)
# Encryption key is derived from SECRET_KEY using PBKDF2

# Get encryption salt from environment or use default
# Always ensure it's bytes for cryptographic operations
encryption_salt_env = os.getenv('ENCRYPTION_SALT', 'food-ordering-encryption-salt-v1')
ENCRYPTION_SALT = encryption_salt_env.encode('utf-8') if isinstance(encryption_salt_env, str) else encryption_salt_env

# Encrypted fields in the system:
# - UserProfile: full_name, phone_number, address
# - Restaurant: address, phone, email
# - PendingRestaurant: address, phone, email

# SECURITY WARNING: don't run with debug turned on in production!
# Read DEBUG from environment variable, default to False for safety
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# ALLOWED_HOSTS configuration
# In production, set this via environment variable
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
# Add additional hosts if needed
if 'tetech.in' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.extend(['tetech.in', 'www.tetech.in', 'demo.tetech.in'])
# For development/testing
if DEBUG:
    ALLOWED_HOSTS.extend(['testserver', '.ngrok-free.app'])



# Application definition
# Core Django apps and project-specific apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Security and Authentication
    'axes',  # Django Axes for brute force protection
    
    # Project apps
    'core.apps.CoreConfig',
    'customer.apps.CustomerConfig',
    'restaurant.apps.RestaurantConfig',
    'orders.apps.OrdersConfig',
    'menu.apps.MenuConfig',
]

# Middleware configuration
# Handles request/response processing pipeline
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serve static files efficiently in production
    'core.middleware.DateRestrictionMiddleware',  # Date-based access restrictions
    # 'django_csp.middleware.CSPMiddleware',  # Content Security Policy middleware - temporarily disabled for debugging
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # 'axes.middleware.AxesMiddleware',  # Temporarily disabled to debug authentication issues
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'core.middleware.SessionTimeoutMiddleware',  # Custom session timeout middleware - temporarily disabled for debugging
]

ROOT_URLCONF = 'food_ordering.urls'

# Template configuration
# Uses Tailwind CSS for styling
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'customer.context_processors.cart_count',  # Custom cart count processor
                'core.context_processors.session_timeout_context',  # Session timeout settings
                'core.context_processors.site_info_context',  # Site information
                'core.context_processors.user_role_context',  # User role information for restaurant owners
                'orders.context_processors.flash_sales_context',  # Flash sales and seasonal promotions
            ],
        },
    },
]

WSGI_APPLICATION = 'food_ordering.wsgi.application'


# Database configuration
# Uses PostgreSQL for production-ready performance
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'food_ordering_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}


# Password validation
# Ensures strong password requirements
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
# Sets timezone and language settings
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# Configuration for serving static assets
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise configuration for efficient static file serving
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files configuration
# Handles user-uploaded content (food images, etc.)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Session configuration
# Uses database-backed sessions for cart functionality
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Session timeout settings for enhanced security
SESSION_COOKIE_AGE = 3600  # 60 minutes absolute timeout in seconds (longer for staff)
SESSION_SAVE_EVERY_REQUEST = True  # Track activity for inactivity timeout
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Allow remember me functionality to work

# Custom session timeout middleware settings
SESSION_INACTIVITY_TIMEOUT = 1800  # 30 minutes inactivity timeout for customers
SESSION_STAFF_INACTIVITY_TIMEOUT = 3600  # 60 minutes for restaurant staff
SESSION_WARNING_TIME = 120  # Show warning 2 minutes before timeout

# Exempt URLs that should not trigger session timeout
SESSION_TIMEOUT_EXEMPT_URLS = [
    '/checkout/',
    '/payment/',
    '/order/confirm/',
    '/api/payment/',
    '/api/checkout/',
    '/auth/password-reset/',
    '/auth/reset/',
]


# Login/Logout URLs
# Redirects after authentication
LOGIN_URL = 'core:login'
LOGIN_REDIRECT_URL = 'customer:home'
LOGOUT_REDIRECT_URL = 'core:login'

# Authentication Backends
# Custom backend that allows login with either username or email address
AUTHENTICATION_BACKENDS = [
    'core.authentication.UsernameOrEmailBackend',  # Custom backend for username/email login
    'django.contrib.auth.backends.ModelBackend',  # Fallback to default Django backend
]


# Site configuration
SITE_NAME = 'Tetech Food Ordering'
SITE_DOMAIN = 'tetech.in'
SITE_URL = f'https://{SITE_DOMAIN}'  # Production URL

# Email configuration
# Settings for sending registration and notification emails
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Use console for development
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # Uncomment for production

# SMTP Configuration (load from environment variables)
EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '25'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'False').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

# Default from email for all system emails
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'Tetech Food Ordering <noreply@tetech.in>')

# Email settings for development (console backend will print emails to console)
EMAIL_SUBJECT_PREFIX = '[Tetech Food Ordering] '

# SMS Notification Configuration (Twilio)
# Settings for sending SMS notifications for order updates
# Uncomment and configure these settings for production use
TWILIO_ACCOUNT_SID = None  # Replace with your Twilio Account SID
TWILIO_AUTH_TOKEN = None  # Replace with your Twilio Auth Token
TWILIO_PHONE_NUMBER = None  # Replace with your Twilio phone number

# Development settings for SMS (set to True to disable SMS in development)
SMS_ENABLED = False

# Notification preferences (can be overridden per user)
EMAIL_NOTIFICATIONS_ENABLED = True
SMS_NOTIFICATIONS_ENABLED = False  # Disabled by default to manage costs


# ============================================
# RAZORPAY PAYMENT GATEWAY CONFIGURATION
# ============================================
# Razorpay API credentials for online payment processing
# Get your API keys from: https://dashboard.razorpay.com/app/keys
# For testing, use Test API Keys. For production, use Live API Keys.
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', 'rzp_test_XXXXXXXXX')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', 'your_secret_key_here')

# Payment gateway settings
RAZORPAY_CURRENCY = 'INR'  # Indian Rupees
RAZORPAY_PAYMENT_TIMEOUT = 900  # 15 minutes for payment completion


# CSRF trusted origins for development
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'http://127.0.0.1:55072',
    'http://localhost:55072',
    'http://127.0.0.1:52416',
    'http://localhost:52416',
    'http://127.0.0.1:57026',
    'https://de1b90997900.ngrok-free.app',
    'https://*.ngrok-free.app'
]

# Django Axes Configuration for Brute Force Protection
# Prevents repeated login attempts with sophisticated tracking
AXES_FAILURE_LIMIT = 10  # Allow 10 failed attempts before lockout (more reasonable)
AXES_COOLOFF_TIME = 1  # Lockout for 1 hour (more effective deterrent)
AXES_RESET_ON_SUCCESS = True  # Reset failure count on successful login
AXES_LOCKOUT_TEMPLATE = 'core/lockout.html'  # Custom lockout page
AXES_VERBOSITY = 1  # Log lockout events
AXES_BACKEND = 'axes.backends.standalone.AxesBackend'  # Use standalone backend (switch to cache for production)
AXES_LOCKOUT_PARAMETERS = ['ip_address']  # IP-based lockout only (prevents username enumeration)
AXES_ENABLE_ACCESS_FAILURE_LOG = True  # Enable detailed failure logging for monitoring
AXES_ONLY_USER_FAILURES = False  # Prevent username enumeration attacks

# Production cache backend for Axes (uncomment for production with Redis/Memcached)
# AXES_BACKEND = 'axes.backends.cache.AxesBackend'
#         }
#     }
# }

# Exempt URLs from Axes lockout (payment webhooks, static files, etc.)
AXES_NEVER_LOCKOUT_WHITELIST = [
    '/api/payment/webhook/',  # Payment gateway callbacks
    '/api/checkout/webhook/',  # Checkout webhooks
    '/static/',  # Static files
    '/media/',  # Media files
]

# Rate Limiting Configuration
# Protect sensitive endpoints from abuse
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'  # Use default cache backend

# Content Security Policy Configuration (using django-csp middleware)
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_CONNECT_SRC = ("'self'", "https://api.stripe.com")
CSP_FRAME_SRC = ("'self'",)
CSP_FORM_ACTION = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_UPGRADE_INSECURE_REQUESTS = True

# Logging Configuration for Security and Audit
# Comprehensive logging with sensitive data masking for payment processing
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'security': {
            'format': '{levelname} {asctime} [SECURITY] {module} {message}',
            'style': '{',
        },
        'audit': {
            'format': '{levelname} {asctime} [AUDIT] {module} user:{user} ip:{ip} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'sensitive_data_filter': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': lambda record: not any(
                sensitive in record.getMessage().lower() 
                for sensitive in ['password', 'credit_card', 'cvv', 'ssn', 'token']
            ) or record.levelname >= 'WARNING'
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'food_ordering.log',
            'formatter': 'verbose',
            'filters': ['require_debug_false', 'sensitive_data_filter'],
        },
        'security_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'formatter': 'security',
            'filters': ['require_debug_false'],
        },
        'audit_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'audit.log',
            'formatter': 'audit',
            'filters': ['require_debug_false'],
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'axes': {
            'handlers': ['security_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'food_ordering.security': {
            'handlers': ['security_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'food_ordering.audit': {
            'handlers': ['audit_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'food_ordering.payments': {
            'handlers': ['audit_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    
    # Enhanced Security Headers for Production
    SECURE_HSTS_SECONDS = 31536000  # 1 year HSTS
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Content Security Policy
    SECURE_CONTENT_SECURITY_POLICY = {
        "default-src": "'self'",
        "script-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net",
        "style-src": "'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src": "'self' https://fonts.gstatic.com",
        "img-src": "'self' data: https: https:",
        "connect-src": "'self' https://api.stripe.com",
        "frame-src": "'self'",
        "form-action": "'self'",
        "frame-ancestors": "'none'",
        "base-uri": "'self'",
        "upgrade-insecure-requests": "",
    }
    
    # Additional Security Headers
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
    
    # Session Security Enhings
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SAMESITE = 'Lax'
    
    # Password policy for production
    AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
            'OPTIONS': {
                'min_length': 12,  # Stronger minimum length for production
            }
        },
        {
            'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        },
    ]
