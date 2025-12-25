"""
Customer app configuration.
Defines app settings and initialization logic.
"""
from django.apps import AppConfig


class CustomerConfig(AppConfig):
    """
    Configuration class for the customer application.
    Handles customer-facing features like menu browsing and cart.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'customer'
    
    def ready(self):
        """
        Initialize app and register signal handlers.
        """
        import customer.signals
