from django.urls import re_path
from core.consumers import NotificationConsumer, ChatConsumer

websocket_urlpatterns = [
    re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
    re_path(r'ws/chat/$', ChatConsumer.as_asgi()),
] 