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


# Define the base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

SITE_URL = 'http://localhost:8000'  # For development; adjust for production

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-or8ih)*8^-c_@9h4r&sojeg#*5841-k%f9s+$tj##9n=&thm)4"  # Replace with a secure key in production

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True  # Set to False in production for security
ALLOWED_HOSTS = ['localhost', '127.0.0.1']  # Add production hosts here

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
    "csp",                            # Content Security Policy enforcement
    "django_vite",                    # Integration with Vite for frontend assets
    'django_crontab',                 # Cron job management
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",         # Security enhancements
    "django.contrib.sessions.middleware.SessionMiddleware",   # Session support
    'corsheaders.middleware.CorsMiddleware',                 # CORS middleware for handling cross-origin requests
    "django.middleware.common.CommonMiddleware",             # Common utilities
    "django.middleware.csrf.CsrfViewMiddleware",             # CSRF protection
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # User authentication
    "django.contrib.messages.middleware.MessageMiddleware",  # Messages support
    "django.middleware.clickjacking.XFrameOptionsMiddleware",  # Clickjacking protection
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
        'NAME': 'tipsterarena',
        'USER': 'paul',
        'PASSWORD': config('DATABASE_PASSWORD'),
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

# Static files configuration (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/
STATIC_URL = '/static/'              # URL prefix for static files
STATICFILES_DIRS = [BASE_DIR / 'static']  # Directory for static files during development
STATIC_ROOT = BASE_DIR / 'staticfiles'    # Directory for collected static files in production

# Media files configuration (user-uploaded content)
MEDIA_URL = '/media/'         # URL prefix for media files
MEDIA_ROOT = BASE_DIR / 'media'  # Directory for storing media files


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
CSP_CONNECT_SRC = ("'self'", "https://*.twimg.com", "https://api.x.com")
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

# Django Vite configuration for frontend asset management
DJANGO_VITE = {
    'default': {
        'dev_mode': DEBUG,                    # Use Vite dev server in debug mode
        'dev_server_port': 3000,              # Vite development server port
        'static_url_prefix': '',              # No prefix for static URLs
        'manifest_path': BASE_DIR / 'static/dist/manifest.json',  # Path to Vite manifest
    }
}

VITE_APP_DIR = BASE_DIR  # Directory containing vite.config.mjs (root of project)

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"  # Default auto-incrementing field type

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAdminUser',
    ],
}

CRONJOBS = [
    # Run update_football_events every 24 hours at midnight
    ('0 0 * * *', 'core.cron.update_football_events', '>> /var/log/tipsterarena_cron.log 2>&1'),
    # Run check_inplay_matches every 10 minutes
    ('*/10 * * * *', 'core.cron.check_inplay_matches', '>> /var/log/tipsterarena_cron.log 2>&1'),
]

# Logging configuration for cron jobs
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/tipsterarena.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'core': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}