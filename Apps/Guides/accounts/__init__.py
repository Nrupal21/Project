"""
Accounts app initialization file.
This file makes the accounts directory a Python package.
"""

default_app_config = 'accounts.apps.AccountsConfig'

# Note: Signals and providers are now imported in apps.py ready() method
# to prevent circular imports during app loading.

# Import middleware classes to make them available when importing from accounts
from .middleware import OTPVerificationMiddleware
from .session_timeout_middleware import SessionTimeoutMiddleware

__all__ = [
    'OTPVerificationMiddleware',
    'SessionTimeoutMiddleware',
]
