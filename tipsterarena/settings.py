"""
Django settings for the Tipster Arena project.

This file configures the core settings for the Django application, including database,
middleware, templates, static files, security, and custom app integrations. Generated
by 'django-admin startproject' using Django 5.1.6 and customized for Tipster Arena.

For more information on this file, see:
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see:
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
from decouple import config  # For environment variable management
from dotenv import load_dotenv
import os


# Define the base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

SITE_URL = 'http://localhost:8000'  # For development; adjust for production

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-or8ih)*8^-c_@9h4r&sojeg#*5841-k%f9s+##9n=&thm)4')  # Replace with a secure key in production

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True  # Set to False in production for security
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']  # Add production hosts here

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",           # Admin interface
    "django.contrib.auth",            # Authentication system
    "django.contrib.contenttypes",    # Content type framework
    "django.contrib.sessions",        # Session management
    "django.contrib.messages",        # Messaging framework
    "django.contrib.staticfiles",     # Static file handling
    'core.apps.CoreConfig',           # Custom core app for Tipster Arena
    'corsheaders',                    # CORS headers for cross-origin requests
    'rest_framework',                 # Django REST framework for API support
    'rest_framework.authtoken',       # Token authentication for REST framework
    'csp',                            # Content Security Policy enforcement
    "django_vite",                    # Integration with Vite for frontend assets
    'social_django',                   # Social authentication support                     
    'channels',                       # WebSocket support
    'django_extensions',              # Development tools
    'debug_toolbar',                  # Debug toolbar
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",         # Security enhancements
    "whitenoise.middleware.WhiteNoiseMiddleware",           # Static file serving
    "django.contrib.sessions.middleware.SessionMiddleware",   # Session support
    'corsheaders.middleware.CorsMiddleware',                 # CORS middleware
    "django.middleware.common.CommonMiddleware",             # Common utilities
    "django.middleware.csrf.CsrfViewMiddleware",             # CSRF protection
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # User authentication
    "django.contrib.messages.middleware.MessageMiddleware",  # Messages support
    "django.middleware.clickjacking.XFrameOptionsMiddleware",  # Clickjacking protection
    'debug_toolbar.middleware.DebugToolbarMiddleware',       # Debug toolbar
]

ROOT_URLCONF = "tipsterarena.urls"  # Root URL configuration

# Template configuration
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",  # Django template engine
        "DIRS": [BASE_DIR / 'templates'],  # Directory for custom templates
        "APP_DIRS": True,                  # Enable app-specific templates
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",           # Debug context
                "django.template.context_processors.request",         # Request context
                "django.contrib.auth.context_processors.auth",        # Authentication context
                "django.contrib.messages.context_processors.messages",  # Messages context
                'core.context_processors.suggested_tipsters',         # Custom processor for suggested tipsters
                'core.context_processors.trending_tips',             # Custom processor for trending tips
            ],
        },
    },
]

WSGI_APPLICATION = "tipsterarena.wsgi.application"  # WSGI application entry point

# Database configuration
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'tipsterarena'),
        'USER': os.environ.get('DB_USER', 'admin'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'Frankfurt5!'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),  # Always use localhost by default
        'PORT': os.environ.get('DB_PORT', '5432'),
    },
    'test': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'tipsterarena_test',
        'USER': 'admin',
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'Frankfurt5!'),
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},  # Prevents similarity to user attributes
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},            # Enforces minimum length
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},          # Blocks common passwords
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},         # Prevents all-numeric passwords
]

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/
LANGUAGE_CODE = "en-us"  # Default language
TIME_ZONE = "UTC"        # Default time zone
USE_I18N = True          # Enable internationalization
USE_TZ = True            # Enable timezone support

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Add whitenoise for static file serving
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Authentication settings
LOGIN_REDIRECT_URL = '/home/'  # Redirect after successful login
LOGOUT_REDIRECT_URL = '/'      # Redirect after logout
LOGIN_URL = '/'                # Redirect to landing page if not authenticated


# CORS settings
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost:3000',  # Vite dev server
    'http://127.0.0.1:3000',
]
CORS_ALLOW_CREDENTIALS = True  # Allow cookies, auth headers
CORS_ALLOW_METHODS = ['GET', 'POST', 'OPTIONS']  # Explicitly allow methods
CORS_ALLOW_HEADERS = ['Content-Type', 'X-CSRFToken']  # Allow specific headers

# Security settings
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://*.twimg.com", "https://js.intercomcdn.com")
CSP_SCRIPT_SRC = ("'self'", "https://*.twimg.com", "https://js.intercomcdn.com")
CSP_FONT_SRC = ("'self'", "https://*.twimg.com", "https://js.intercomcdn.com", "https://fonts.intercomcdn.com", "'data:'")  # Added 'data:'
CSP_IMG_SRC = ("'self'", "data:", "https://*.twimg.com")
CSP_CONNECT_SRC = (
    "'self'",
    "ws://localhost:8000",
    "ws://127.0.0.1:8000",
    "wss://localhost:8000",
    "wss://127.0.0.1:8000",
    "ws://localhost",
    "wss://localhost",
    "ws://127.0.0.1",
    "wss://127.0.0.1"
)
CSP_STYLE_SRC = (
    "'self'",                  # Allow styles from same origin
    "https://cdnjs.cloudflare.com",  # Font Awesome
    "https://fonts.googleapis.com",  # Google Fonts
    "'unsafe-inline'",         # Allow inline styles (consider removing in production)
)
CSP_FONT_SRC = (
    "'self'",
    "https://fonts.googleapis.com",
    "https://fonts.gstatic.com",  # Google Fonts font files
)
CSP_IMG_SRC = (
    "'self'",
    "data:",  # Allow data URIs for inline images
)
CSP_CONNECT_SRC = ("'self'",)  # Restrict connections (e.g., APIs, WebSockets) to same origin
CSP_FRAME_SRC = ("'none'",)    # Disallow iframes
CSP_OBJECT_SRC = ("'none'",)   # Disallow <object> and <embed> tags

CSP_REPORT_ONLY = True         # Run CSP in report-only mode (logs violations without blocking)
CSP_REPORT_URI = "/csp-report/"  # Endpoint for CSP violation reports

# Django Vite
DJANGO_VITE = {
    'default': {
        'dev_mode': True,
        'dev_server_port': 3000,
        'manifest_path': os.path.join(BASE_DIR, 'static', 'dist', '.vite', 'manifest.json'),
        'static_url_prefix': '',  # Changed from 'static/' to empty string
    }
}

VITE_APP_DIR = BASE_DIR  # Directory containing vite.config.mjs (root of project)

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"  # Default auto-incrementing field type

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Allow public access by default
    ],
}

# Debug toolbar settings
INTERNAL_IPS = [
    '127.0.0.1',
    '0.0.0.0',
]

# Enable auto-reloading
DJANGO_AUTO_RELOAD = True

# Enable file watching
FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]

# WebSocket settings
ASGI_APPLICATION = 'tipsterarena.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('redis', 6379)],
            'capacity': 1500,  # Maximum number of messages that can be in a channel layer
            'expiry': 3600,   # Message expiry in seconds
        },
    },
}

# Development-specific logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'channels': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'daphne': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Social auth pipeline to handle UserProfile creation
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'yourapp.pipeline.create_user_profile',  # Custom pipeline to set handle
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)


# Load environment variables from .env file
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Stripe settings
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_MONTHLY_PRICE_ID = os.getenv('STRIPE_MONTHLY_PRICE_ID')
STRIPE_YEARLY_PRICE_ID = os.getenv('STRIPE_YEARLY_PRICE_ID')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

# Session settings
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_SAVE_EVERY_REQUEST = True  # Extend session on each request

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")