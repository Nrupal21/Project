"""
Application configuration for the itineraries app.

This module defines the application configuration for the itineraries Django app,
specifying metadata and behavior for the app as a whole.
"""

from django.apps import AppConfig


class ItinerariesConfig(AppConfig):
    """
    Configuration class for the itineraries app.
    
    This class defines various attributes and behaviors for the app, including
    the default primary key field type and human-readable app name.
    """
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'itineraries'
    verbose_name = 'Itineraries Management'
    
    def ready(self):
        """
        Initialize app when Django starts.
        
        This method is called when the app is ready to process requests.
        It imports signal handlers to register them with the Django signal system,
        enabling automatic creation of itinerary days and related functionality.
        """
        # Import signals to register signal handlers
        # Importing inside the method prevents import loops
        import itineraries.signals
