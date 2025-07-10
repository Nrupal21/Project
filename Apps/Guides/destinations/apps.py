"""
App configuration for the destinations app.

This module contains the configuration for the destinations application.
"""
from django.apps import AppConfig

class DestinationsConfig(AppConfig):
    """
    Configuration class for the destinations app.
    
    This class defines the configuration for the destinations application,
    including the default auto field and the name of the app.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'destinations'
    
    def ready(self):
        """
        Method called when the app is ready.
        
        This method is called when Django starts. It's used to perform
        any initialization tasks, such as registering signals.
        """
        # Import signals to register them
        import destinations.signals
