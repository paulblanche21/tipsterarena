# core/management/commands/fix_database.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import MessageThread, UserProfile
import logging

class Command(BaseCommand):
    help = 'Check and fix database data for MessageThreads and UserProfiles'

    def handle(self, *args, **options):
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        logger.info("Starting database fix script")

        # Check and fix threads
        try:
            user = User.objects.get(username='testuser1')
            logger.info(f"Checking threads for user: {user.username}")

            threads = MessageThread.objects.filter(participants=user)
            logger.info(f"Found {threads.count()} threads for {user.username}")

            for thread in threads:
                logger.info(f"Thread ID: {thread.id}")
                participants = thread.participants.all()
                participant_usernames = [p.username for p in participants]
                logger.info(f"Participants: {participant_usernames}")

                if len(participant_usernames) < 2:
                    logger.warning(f"Thread {thread.id} has fewer than 2 participants: {participant_usernames}")
                    logger.info(f"Deleting thread {thread.id}")
                    thread.delete()
                else:
                    other_participant = thread.participants.exclude(id=user.id).first()
                    logger.info(f"Other participant: {other_participant.username if other_participant else None}")

        except User.DoesNotExist:
            logger.error("User 'testuser1' does not exist")
            return
        except Exception as e:
            logger.error(f"Error checking threads: {str(e)}")
            return

        # Ensure user profiles
        try:
            users = User.objects.all()
            logger.info(f"Found {users.count()} users")

            for user in users:
                profile, created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={'handle': f"@{user.username}"}
                )
                if created:
                    logger.info(f"Created UserProfile for {user.username} with handle {profile.handle}")
                elif not profile.handle:
                    profile.handle = f"@{user.username}"
                    profile.save()
                    logger.info(f"Set handle for {user.username} to {profile.handle}")
                else:
                    logger.info(f"User {user.username} already has a UserProfile with handle {profile.handle}")

        except Exception as e:
            logger.error(f"Error ensuring user profiles: {str(e)}")
            return

        logger.info("Database fix script completed")