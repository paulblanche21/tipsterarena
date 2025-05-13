import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        User = get_user_model()
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
        else:
            self.group_name = f"notifications_{self.user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            # Optionally send unread notifications on connect
            await self.send_unread_notifications()

    async def disconnect(self, close_code):
        if not self.user.is_anonymous:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        # Handle incoming messages if needed
        pass

    async def send_notification(self, event):
        # Called by other code to send a notification to this user
        notification = event["notification"]
        await self.send(text_data=json.dumps({
            "type": "notification",
            "notification": notification
        }))

    async def send_unread_notifications(self):
        notifications = await self.get_unread_notifications()
        for n in notifications:
            await self.send(text_data=json.dumps({
                'type': 'notification',
                'notification': n
            }))

    @database_sync_to_async
    def get_unread_notifications(self):
        from core.models import Notification
        User = get_user_model()
        notifications = Notification.objects.filter(user=self.user, read=False).order_by('-created_at')[:5]
        result = []
        for n in notifications:
            result.append({
                'id': n.id,
                'type': n.type,
                'message': n.content,
                'created_at': n.created_at.isoformat(),
                'username': n.related_user.username if n.related_user else '',
                'avatar_url': n.related_user.userprofile.avatar.url if n.related_user and hasattr(n.related_user, 'userprofile') and n.related_user.userprofile.avatar else '',
            })
        return result

    async def notify(self, event):
        await self.send(text_data=json.dumps(event["data"])) 