"""
App configuration for the reviews application.

This module contains the ReviewsConfig class which configures the reviews app,
including its name, label, and any app-specific settings or signals.
"""

from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    """Configuration for the Reviews application.
    
    This class configures the 'reviews' app, defining its name, default auto field,
    and any initialization settings. It also handles the connection of signal handlers.
    """
    # The full Python path to the application
    name = 'reviews'
    
    # Human-readable name for the application
    verbose_name = 'Reviews & Ratings'
    
    def ready(self):
        """
        Override this method to perform initialization tasks for the app.
        This method is called when the application starts.
        
        We import and register the template tags here to ensure they're available
        when the application starts.
        """
        # Import and register template tags
        from . import templatetags  # noqa
        
    # Default primary key field type to use for models that don't have a field with primary_key=True
    default_auto_field = 'django.db.models.BigAutoField'
    
    def ready(self):
        """Perform initialization tasks when Django starts."""
        # Import signals to register the signal handlers
        from . import signals  # noqa: F401
        
        # Connect the signal handlers
        signals.connect_signals()
