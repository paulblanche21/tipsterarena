from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Update a user\'s handle'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str)
        parser.add_argument('handle', type=str)

    def handle(self, *args, **options):
        username = options['username']
        handle = options['handle']
        
        try:
            user = User.objects.get(username=username)
            profile = user.userprofile
            
            # Add @ if not present
            if not handle.startswith('@'):
                handle = f'@{handle}'
                
            profile.handle = handle
            profile.save()
            
            self.stdout.write(self.style.SUCCESS(f'Successfully updated handle for {username} to {handle}'))
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {username} does not exist'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}')) 