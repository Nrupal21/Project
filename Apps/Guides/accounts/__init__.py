"""
Accounts App Initialization.

This module initializes the accounts app and exposes important models and utilities.

Note: To prevent circular imports, models should be imported directly from accounts.models
using the full import path, e.g.:
    from accounts.models import User, UserProfile, etc.
"""

# No direct imports here to prevent circular imports
# Import models using their full path when needed

# Define what gets imported with 'from accounts import *'
__all__ = [
    'User',
    'UserProfile',
    'UserPreference',
    'UserFavorite',
    'GuideApplication',
    'VerificationToken'
]