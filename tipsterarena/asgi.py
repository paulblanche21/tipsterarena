"""
ASGI config for the Tipster Arena project.

This file exposes the ASGI callable as a module-level variable named ``application``,
enabling asynchronous server gateway interface support for the Django application.
It is used for deploying Tipster Arena with ASGI-compatible servers (e.g., Uvicorn, Daphne).

For more information on this file, see:
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

# Set the default Django settings module for the application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tipsterarena.settings")

# Initialize Django ASGI application early to ensure the app is loaded
application = get_asgi_application()