"""
WSGI config for the Tipster Arena project.

This file exposes the WSGI callable as a module-level variable named ``application``,
enabling synchronous web server gateway interface support for the Django application.
It is used for deploying Tipster Arena with WSGI-compatible servers (e.g., Gunicorn, uWSGI).

For more information on this file, see:
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Set the default Django settings module for the application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tipsterarena.settings")

# Define the WSGI application callable
application = get_wsgi_application()