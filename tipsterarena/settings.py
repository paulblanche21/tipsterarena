"""
Django settings for the Tipster Arena project.

This file configures the core settings for the Django application, including database,
middleware, templates, static files, security, and custom app integrations. Generated
by 'django-admin startproject' using Django 5.1.6 and customized for Tipster Arena.

For more information on this file, see:
https://docs.djangoproject.com/en/5.1/topics/settings/
"""

from pathlib import Path
from celery.schedules import crontab
import os
import ssl
import certifi
import dj_database_url

# Define the base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

SITE_URL = 'http://localhost:8000'  # For development; adjust for production

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-or8ih)*8^-c_@9h4r&sojeg#*5841-k%f9s+$tj##9n=&thm)4')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True  # Set to False in production for security
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'tipster-arena-462b360fb9c5.herokuapp.com']

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core.apps.CoreConfig",
    "django_celery_beat",
    "corsheaders",
    "rest_framework",
    "rest_framework.authtoken",
    "csp",
    "django_vite",
    "compressor",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    'corsheaders.middleware.CorsMiddleware',
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "tipsterarena.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                'core.context_processors.suggested_tipsters',
            ],
        },
    },
]

WSGI_APPLICATION = "tipsterarena.wsgi.application"

# Database configuration
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600
    )
}

if not os.environ.get('DATABASE_URL'):
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files configuration
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Authentication settings
LOGIN_REDIRECT_URL = '/home/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/'

# CORS settings
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ['GET', 'POST', 'OPTIONS']
CORS_ALLOW_HEADERS = ['Content-Type', 'X-CSRFToken']

# Security settings
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",
    "https://*.twimg.com",
    "https://js.intercomcdn.com",
    "https://cdnjs.cloudflare.com",
    "https://fonts.googleapis.com",
)
CSP_SCRIPT_SRC = ("'self'", "https://*.twimg.com", "https://js.intercomcdn.com")
CSP_FONT_SRC = (
    "'self'",
    "https://*.twimg.com",
    "https://js.intercomcdn.com",
    "https://fonts.intercomcdn.com",
    "https://fonts.googleapis.com",
    "https://fonts.gstatic.com",
    "'data:'",
)
CSP_IMG_SRC = ("'self'", "data:", "https://*.twimg.com")
CSP_CONNECT_SRC = ("'self'", "https://*.twimg.com", "https://api.x.com")
CSP_FRAME_SRC = ("'none'",)
CSP_OBJECT_SRC = ("'none'",)
CSP_REPORT_ONLY = True
CSP_REPORT_URI = "/csp-report/"

# Django Vite configuration
DJANGO_VITE = {
    'default': {
        'dev_mode': DEBUG,
        'dev_server_port': 3000,
        'static_url_prefix': '',
        'manifest_path': BASE_DIR / 'static/dist/manifest.json',
    }
}

VITE_APP_DIR = BASE_DIR

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAdminUser',
    ],
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
        'file': {'class': 'logging.FileHandler', 'filename': 'scraper.log'},
    },
    'loggers': {
        'core': {'handlers': ['console', 'file'], 'level': 'DEBUG'},
    },
}

# Celery configuration
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_BROKER_TRANSPORT = 'redis'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'visibility_timeout': 3600,
}
CELERY_BROKER_USE_SSL = {
    'ssl_cert_reqs': ssl.CERT_REQUIRED,
    'ssl_ca_certs': certifi.where(),
} if os.environ.get('CELERY_BROKER_URL', '').startswith('rediss://') else {}

# Celery Beat schedule
CELERY_BEAT_SCHEDULE = {
    'fetch-football-fixtures-every-hour': {
        'task': 'core.tasks.fetch_football_fixtures',
        'schedule': crontab(minute=0, hour='0'),
    },
    'fetch-inplay-fixtures-every-30-minutes': {
        'task': 'core.tasks.fetch_football_fixtures',
        'schedule': crontab(minute='*/30'),
        'args': (['in'],),
    },
}