"""
URL configuration for the Tipster Arena project.

This file defines the root URL patterns for the Django application, mapping URLs to views or included URLconfs.
The `urlpatterns` list serves as the entry point for routing requests to the appropriate handlers.

For more information, see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/

Examples:
- Function views: 
    1. Import: from my_app import views
    2. Add: path('', views.home, name='home')
- Class-based views:
    1. Import: from other_app.views import Home
    2. Add: path('', Home.as_view(), name='home')
- Including another URLconf:
    1. Import: from django.urls import include, path
    2. Add: path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Root URL patterns for the project
urlpatterns = [
    path("admin/", admin.site.urls),       # Route for Django admin interface
    path('', include('core.urls')),        # Include all core app URLs at the root path
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)