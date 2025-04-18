# tipsterarena/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tipsterarena.settings')
app = Celery('tipsterarena')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.update(
    broker_url='redis://localhost:6379/0',  # Hardcode for testing
    broker_transport='redis',
    result_backend='redis://localhost:6379/0',  # Ensure backend is set
)
app.autodiscover_tasks()