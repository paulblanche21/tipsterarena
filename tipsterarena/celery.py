import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tipsterarena.settings')
app = Celery('tipsterarena')
app.conf.update(
    broker_url='redis://localhost:6379/0',
    broker_transport='redis',
    result_backend='redis://localhost:6379/0',
    task_default_queue='celery',
    task_default_exchange='celery',
    task_default_routing_key='celery',
)
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()