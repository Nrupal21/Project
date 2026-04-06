"""
WSGI config for guides project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Set the Django settings module path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guides.settings')

# Initialize the WSGI application
application = get_wsgi_application()
