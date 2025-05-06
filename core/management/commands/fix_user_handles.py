from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fix user handles for all users'

    def handle(self, *args, **options):
        users = User.objects.all()
        fixed_count = 0
        created_count = 0

        for user in users:
            try:
                profile, created = UserProfile.objects.get_or_create(user=user)
                
                if created:
                    # Generate a unique handle based on username
                    base_handle = f"@{user.username}"
                    handle = base_handle
                    counter = 1
                    
                    # Ensure handle uniqueness
                    while UserProfile.objects.filter(handle=handle).exists():
                        handle = f"{base_handle}{counter}"
                        counter += 1
                    
                    profile.handle = handle
                    profile.save()
                    created_count += 1
                    logger.info(f"Created profile for {user.username} with handle {handle}")
                
                elif not profile.handle:
                    # Generate a unique handle based on username
                    base_handle = f"@{user.username}"
                    handle = base_handle
                    counter = 1
                    
                    # Ensure handle uniqueness
                    while UserProfile.objects.filter(handle=handle).exists():
                        handle = f"{base_handle}{counter}"
                        counter += 1
                    
                    profile.handle = handle
                    profile.save()
                    fixed_count += 1
                    logger.info(f"Fixed handle for {user.username} to {handle}")
                
                elif not profile.handle.startswith('@'):
                    profile.handle = f"@{profile.handle}"
                    profile.save()
                    fixed_count += 1
                    logger.info(f"Added @ prefix to handle for {user.username}: {profile.handle}")

            except Exception as e:
                logger.error(f"Error processing user {user.username}: {str(e)}")

        self.stdout.write(self.style.SUCCESS(
            f'Successfully processed {users.count()} users: '
            f'{created_count} profiles created, {fixed_count} handles fixed'
        )) 