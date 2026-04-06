"""
ASGI config for guides project.

This module contains the ASGI application used by Django's development server
and any production ASGI deployments. It should expose a module-level variable
named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Set the Django settings module path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guides.settings')

# Initialize the ASGI application
application = get_asgi_application()
