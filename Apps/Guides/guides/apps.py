"""
App configuration for the guides application.

This module contains the GuidesConfig class which configures the guides app.
"""

from django.apps import AppConfig


class GuidesConfig(AppConfig):
    """
    Application configuration for the guides app.
    
    This class configures the guides application and its settings.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'guides'
    verbose_name = 'Local Guides'
    
    def ready(self):
        """
        Method called when the app is ready.
        
        Use this to perform any app initialization, such as registering signals.
        """
        # Import signals to register them
        try:
            import guides.signals  # noqa F401
        except ImportError:
            pass
