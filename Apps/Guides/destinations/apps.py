from django.apps import AppConfig


class DestinationsConfig(AppConfig):
    """Configuration class for the destinations app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'destinations'
    verbose_name = 'Destinations Management'
    
    def ready(self):
        """Run when the app is ready."""
        # Import signals to register them
        import destinations.signals  # noqa
