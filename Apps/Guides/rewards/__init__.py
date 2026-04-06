"""
Rewards App Package.

This package contains the rewards system for the TravelGuide platform,
including models, views, and utilities for managing user reward points,
tiers, and redemptions.

The rewards system is a core component of the TravelGuide platform's user
engagement and loyalty strategy. It provides mechanisms for users to earn
points through various activities, track their progress toward higher reward
tiers, and redeem points for discounts, travel credits, and other benefits.

Key components of the rewards app include:
1. Point earning through activities (registrations, bookings, reviews, etc.)
2. Tiered membership levels with increasing benefits
3. Point redemption for various rewards
4. Admin interfaces for managing the rewards system
5. User-facing views for displaying points, history, and redemption options

The app follows the indigo/violet color scheme established for the TravelGuide
platform, ensuring visual consistency across all rewards-related UI elements.
"""

# Import the RewardsConfig class from the apps.py module
# This makes the configuration class available at the package level
# and allows Django to properly initialize the app with all its settings
from .apps import RewardsConfig

# Set the default_app_config variable to point to our RewardsConfig class
# This is a Django convention that ensures the app is properly configured
# when it's included in INSTALLED_APPS without the full config path
# 
# When Django loads this app, it will use this configuration to:
# 1. Register signal handlers defined in signals.py
# 2. Set up the app's admin site configurations
# 3. Initialize any app-specific settings and configurations
# 4. Apply the proper verbose name in the Django admin interface
default_app_config = 'rewards.apps.RewardsConfig'