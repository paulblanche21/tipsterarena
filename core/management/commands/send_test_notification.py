from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class Command(BaseCommand):
    help = 'Send a test notification to a user via WebSocket'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to send notification to')
        parser.add_argument('message', type=str, help='Notification message')

    def handle(self, *args, **options):
        User = get_user_model()
        try:
            user = User.objects.get(username=options['username'])
        except User.DoesNotExist:
            raise CommandError(f"User '{options['username']}' does not exist.")

        group_name = f'notifications_{user.id}'
        channel_layer = get_channel_layer()
        notification = {
            'type': 'notification',
            'notification': {
                'id': 0,
                'type': 'test',
                'message': options['message'],
                'created_at': 'now',
                'username': user.username,
                'avatar_url': user.userprofile.avatar.url if hasattr(user, 'userprofile') and user.userprofile.avatar else '',
            }
        }
        async_to_sync(channel_layer.group_send)(group_name, notification)
        self.stdout.write(self.style.SUCCESS(f"Sent test notification to {user.username}")) 