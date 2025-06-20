import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels_redis.core import RedisChannelLayer
from django.conf import settings
import redis.asyncio as redis


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
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

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.group_name = "chatroom"
        if self.user.is_anonymous:
            await self.close()
        else:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            # Store user info in Redis
            redis_client = redis.from_url(settings.REDIS_URL)
            await redis_client.hset('chat_online_users', self.user.username, self.get_avatar_url())
            await self.accept()
            
            # Send recent messages to the newly connected user
            recent_messages = await self.get_recent_messages()
            await self.send(text_data=json.dumps({
                "type": "chat_history",
                "messages": recent_messages
            }))
            
            # Broadcast updated user list to all clients
            online_users = await redis_client.hgetall('chat_online_users')
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "user_list_update",
                    "users": [(username.decode(), avatar_url.decode()) for username, avatar_url in online_users.items()],
                },
            )

    @database_sync_to_async
    def get_recent_messages(self):
        from core.models import ChatMessage
        messages = ChatMessage.objects.select_related('sender', 'sender__userprofile').order_by('-created_at')[:50]
        return [{
            'username': msg.sender.username if msg.sender else 'Anonymous',
            'message': msg.content,
            'image_url': msg.image.url if msg.image else None,
            'gif_url': msg.gif_url,
            'emoji': msg.emoji,
            'avatar_url': msg.sender.userprofile.avatar.url if msg.sender and msg.sender.userprofile.avatar else None,
            'created_at': msg.created_at.isoformat()
        } for msg in messages]

    async def disconnect(self, close_code):
        if not self.user.is_anonymous:
            # Remove user from Redis
            redis_client = redis.from_url(settings.REDIS_URL)
            await redis_client.hdel('chat_online_users', self.user.username)
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            # Broadcast updated user list to all clients
            online_users = await redis_client.hgetall('chat_online_users')
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "user_list_update",
                    "users": [(username.decode(), avatar_url.decode()) for username, avatar_url in online_users.items()],
                },
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get("type") == "chat_message":
                message = data.get("message", "")
                username = data.get("username", "Anonymous")
                avatar_url = data.get("avatar_url", "")
                image_url = data.get("image_url", None)
                gif_url = data.get("gif_url", None)
                
                # Save message to database
                await self.save_message(message, image_url, gif_url)
                
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "chat_message_broadcast",
                        "username": username,
                        "avatar_url": avatar_url,
                        "message": message,
                        "image_url": image_url,
                        "gif_url": gif_url,
                    },
                )
            elif data.get("type") == "request_user_list":
                # Get current user list from Redis
                redis_client = redis.from_url(settings.REDIS_URL)
                online_users = await redis_client.hgetall('chat_online_users')
                await self.send(text_data=json.dumps({
                    "type": "user_list",
                    "users": [(username.decode(), avatar_url.decode()) for username, avatar_url in online_users.items()],
                }))
        except json.JSONDecodeError:
            print("Error decoding JSON message")
        except Exception as e:
            print(f"Error in receive: {str(e)}")

    @database_sync_to_async
    def save_message(self, content, image_url=None, gif_url=None):
        from core.models import ChatMessage
        ChatMessage.objects.create(
            sender=self.user,
            content=content,
            image=image_url,
            gif_url=gif_url
        )

    async def chat_message_broadcast(self, event):
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "username": event["username"],
            "avatar_url": event["avatar_url"],
            "message": event["message"],
            "image_url": event.get("image_url"),
            "gif_url": event.get("gif_url"),
        }))

    async def user_list_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "user_list",
            "users": event["users"],
        }))

    def get_avatar_url(self):
        try:
            profile = self.user.userprofile
            if profile.avatar:
                return profile.avatar.url
        except Exception:
            pass
        from django.conf import settings
        return settings.STATIC_URL + 'img/default-avatar.png'

class DirectMessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
            return

        # Get thread_id from URL if present
        self.thread_id = self.scope['url_route']['kwargs'].get('thread_id')
        
        if self.thread_id:
            # Create a unique group name for this thread
            self.thread_group_name = f"thread_{self.thread_id}"
        else:
            # For base messages endpoint, use user-specific group
            self.thread_group_name = f"user_messages_{self.user.id}"
        
        # Add to appropriate group
        await self.channel_layer.group_add(
            self.thread_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Remove from group
        await self.channel_layer.group_discard(
            self.thread_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        
        # Handle heartbeat messages
        if data.get("type") == "heartbeat":
            await self.send(text_data=json.dumps({
                "type": "heartbeat_ack"
            }))
            return
            
        if data.get("type") == "direct_message":
            message = data.get("message", "")
            image_url = data.get("image_url")
            gif_url = data.get("gif_url")
            
            # Broadcast to thread group
            await self.channel_layer.group_send(
                self.thread_group_name,
                {
                    "type": "direct_message_broadcast",
                    "sender": self.user.username,
                    "message": message,
                    "image_url": image_url,
                    "gif_url": gif_url,
                    "created_at": data.get("created_at")
                }
            )

    async def direct_message_broadcast(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            "type": "direct_message",
            "sender": event["sender"],
            "message": event["message"],
            "image_url": event.get("image_url"),
            "gif_url": event.get("gif_url"),
            "created_at": event.get("created_at"),
            "message_id": event.get("message_id")  # Include message ID in the response
        })) 