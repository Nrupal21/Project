from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """
    Configuration class for the Notifications app.
    
    This class defines app-specific configuration for the notifications system,
    including the app name, verbose name, and any initialization needed when
    the app is loaded by Django.
    
    The indigo/violet color scheme is applied to all notification templates
    for consistent styling across the application.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'
    verbose_name = 'Notification System'
    
    def ready(self):
        """
        Perform initialization tasks when the app is ready.
        This method is called once when the app is fully loaded.
        
        Currently imports signal handlers to connect notification events.
        """
        # Import signal handlers to register them
        import notifications.signals  # noqa
