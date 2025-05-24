from django.urls import re_path
from core.consumers import NotificationConsumer, ChatConsumer, DirectMessageConsumer

websocket_urlpatterns = [
    re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
    re_path(r'ws/chat/$', ChatConsumer.as_asgi()),
    re_path(r'ws/messages/$', DirectMessageConsumer.as_asgi()),  # Base messages endpoint
    re_path(r'ws/messages/(?P<thread_id>\w+)/$', DirectMessageConsumer.as_asgi()),
] 