"""
App configuration for the accounts app.

This module contains the configuration for the accounts application.
"""
from django.apps import AppConfig

class AccountsConfig(AppConfig):
    """
    Configuration class for the accounts app.
    
    This class defines the configuration for the accounts application,
    including the default auto field and the name of the app.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    
    def ready(self):
        """
        Import signals and providers when the app is ready.
        This prevents AppRegistryNotReady errors by ensuring the app is fully loaded.
        """
        # Import signals and providers here to avoid circular imports
        from . import signals  # noqa
        from . import providers  # noqa
        
        # Only run in the main process, not during management commands like 'migrate'
        import sys
        if 'runserver' in sys.argv or 'uwsgi' in sys.argv[0]:
            # Import here to avoid AppRegistryNotReady errors
            from .models import UserProfile
            from django.conf import settings
            
            # Initialize MongoDB indexes if using MongoDB
            if hasattr(settings, 'MONGODB_DATABASES'):
                from mongoengine import connect
                from mongoengine.connection import get_connection
                
                # Connect to MongoDB
                db_alias = getattr(settings, 'MONGODB_DATABASES', {}).get('default', {})
                if db_alias:
                    connect(
                        db=db_alias.get('name', 'test'),
                        host=db_alias.get('host', 'localhost'),
                        port=db_alias.get('port', 27017),
                        username=db_alias.get('username'),
                        password=db_alias.get('password'),
                        authentication_source=db_alias.get('authentication_source', 'admin'),
                        alias='default'
                    )
                
                # Ensure indexes are created
                UserProfile.ensure_indexes()  # noqa: F401
