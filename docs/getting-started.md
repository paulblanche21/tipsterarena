# Getting Started

This guide will help you set up Tipster Arena for development and production environments.

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.12.10
- PostgreSQL 14+
- Redis 6+
- Node.js 18+ (for frontend development)
- Git

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/paulblanche21/tipsterarena.git
cd tipsterarena
```

### 2. Create and Activate Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
npm install  # For frontend dependencies
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root:

```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://user:password@localhost:5432/tipsterarena
REDIS_URL=redis://localhost:6379/0
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
```

### 5. Set Up Database

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6. Collect Static Files

```bash
python manage.py collectstatic
```

## Development Setup

### Running the Development Server

```bash
python manage.py runserver
```

### Running Celery Worker

```bash
celery -A tipsterarena worker -l INFO
```

### Running Celery Beat

```bash
celery -A tipsterarena beat -l INFO
```

### Running Tests

```bash
./run_tests.sh
```

## Configuration

### Database Configuration

The project uses PostgreSQL. Configure your database settings in `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'tipsterarena',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Redis Configuration

Redis is used for caching and Celery. Configure in `settings.py`:

```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://localhost:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### Email Configuration

Configure email settings in `settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-password'
```

## Deployment

### Heroku Deployment

1. Install Heroku CLI
2. Login to Heroku
3. Create a new app
4. Set up environment variables
5. Deploy using Git

```bash
heroku login
heroku create your-app-name
heroku config:set DEBUG=False
heroku config:set SECRET_KEY=your-secret-key
git push heroku main
```

### Production Settings

For production, ensure:

1. DEBUG is set to False
2. SECRET_KEY is properly set
3. ALLOWED_HOSTS is configured
4. SSL is enabled
5. Static files are served properly
6. Database backups are configured
7. Monitoring is set up

## Common Development Tasks

### Creating a New App

```bash
python manage.py startapp new_app
```

### Creating Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Creating Superuser

```bash
python manage.py createsuperuser
```

### Running Management Commands

```bash
python manage.py shell
python manage.py dbshell
python manage.py showmigrations
```

## Troubleshooting

If you encounter issues:

1. Check the logs in `logs/` directory
2. Verify environment variables
3. Check database connection
4. Ensure Redis is running
5. Check Celery worker status

## Next Steps

- Read the [Architecture](architecture.md) documentation
- Explore the [API Reference](api.md)
- Check out the [Development Guide](development.md) 