"""
Rewards App Configuration.

This module configures the rewards app, which handles the reward points system,
including point earning, tracking, and redemption functionality.

The rewards app is a core component of the TravelGuide platform's user engagement
and loyalty strategy. It provides a comprehensive system for users to earn points
through various activities, track their progress toward reward tiers, and redeem
points for discounts, travel credits, and other benefits.

The app integrates with other components of the platform through Django signals
to automatically award points for activities like registrations, bookings, and reviews.
"""

from django.apps import AppConfig


class RewardsConfig(AppConfig):
    """
    Application configuration for the rewards system.
    
    This class configures the rewards application with its name and default auto field.
    It ensures the app is properly recognized by Django's app registry and handles any
    app-specific initialization that needs to happen when the app is loaded.
    
    The rewards system is designed with the following key features:
    - Point earning through various user activities (bookings, reviews, etc.)
    - Tiered membership levels with increasing benefits (Bronze, Silver, Gold, Platinum)
    - Point redemption for discounts, travel credits, and other rewards
    - Detailed point history and transaction tracking
    - Automatic point expiration management
    
    The app follows the indigo/violet color scheme established for the TravelGuide
    platform, ensuring visual consistency across all rewards-related UI elements.
    """
    # Use BigAutoField as the primary key type for all models in this app
    # This provides a 64-bit integer field which can handle very large numbers
    # of records without running out of unique IDs
    default_auto_field = 'django.db.models.BigAutoField'
    
    # Internal identifier for the app used by Django
    name = 'rewards'
    
    # Human-readable name shown in the Django admin interface
    verbose_name = 'Reward Points System'
    
    def ready(self):
        """
        Perform initialization tasks when the app is ready.
        
        This method is called when Django starts and is used to register any
        signal handlers or perform other initialization tasks.
        
        In the rewards app, this method primarily imports the signals module
        to ensure that all signal handlers are registered with Django's signal
        dispatcher. This enables automatic point awards for various user activities
        across the platform without requiring explicit function calls in views.
        
        The signals module contains handlers for events like:
        - User registration
        - Tour bookings
        - Review submissions
        - And other point-earning activities
        
        Note: The import is done here rather than at the module level to avoid
        circular import issues, as the signals module may import models from this app.
        """
        # Import the signals module to register all signal handlers
        # The noqa comment tells linters to ignore the import-not-at-top-level warning
        # since this is the recommended Django pattern for signal registration
        import rewards.signals  # noqa
