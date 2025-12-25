"""
Restaurant app configuration.
Defines app settings and initialization logic.
"""
from django.apps import AppConfig


class RestaurantConfig(AppConfig):
    """
    Configuration class for the restaurant application.
    Manages restaurant dashboard and order management features.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'restaurant'
    
    def ready(self):
        """
        Initialize the restaurant app.
        
        This method is called when the Django application starts up.
        It imports and registers the signals for automatic manager login tracking.
        """
        # Import signals to register them
        from . import signals
