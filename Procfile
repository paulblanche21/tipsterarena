release: python manage.py migrate && python manage.py collectstatic --noinput
web: gunicorn tipsterarena.wsgi
worker: celery -A tipsterarena worker -l info
beat: celery -A tipsterarena beat -l info
