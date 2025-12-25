"""
Orders app configuration.
Defines app settings and initialization logic.
"""
from django.apps import AppConfig


class OrdersConfig(AppConfig):
    """
    Configuration class for the orders application.
    Manages customer orders and order items.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'
