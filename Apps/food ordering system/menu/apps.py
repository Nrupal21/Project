"""
Menu app configuration.
Defines app settings and initialization logic.
"""
from django.apps import AppConfig


class MenuConfig(AppConfig):
    """
    Configuration class for the menu application.
    Manages food categories and menu items.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'menu'
