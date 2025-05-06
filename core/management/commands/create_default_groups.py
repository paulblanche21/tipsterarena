"""Management command to create default user groups and permissions."""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import (
    Tip, UserProfile, Comment, Follow, Like, Share, 
    Message, MessageThread, FootballEvent, GolfEvent, 
    TennisEvent, HorseRacingEvent
)

class Command(BaseCommand):
    help = 'Create default user groups and permissions'

    def handle(self, *args, **options):
        # Get content types for all relevant models
        tip_ct = ContentType.objects.get_for_model(Tip)
        profile_ct = ContentType.objects.get_for_model(UserProfile)
        comment_ct = ContentType.objects.get_for_model(Comment)
        follow_ct = ContentType.objects.get_for_model(Follow)
        like_ct = ContentType.objects.get_for_model(Like)
        share_ct = ContentType.objects.get_for_model(Share)
        message_ct = ContentType.objects.get_for_model(Message)
        message_thread_ct = ContentType.objects.get_for_model(MessageThread)
        football_ct = ContentType.objects.get_for_model(FootballEvent)
        golf_ct = ContentType.objects.get_for_model(GolfEvent)
        tennis_ct = ContentType.objects.get_for_model(TennisEvent)
        horse_racing_ct = ContentType.objects.get_for_model(HorseRacingEvent)

        # Create Basic Users group
        basic_group, created = Group.objects.get_or_create(name='Basic Users')
        if created:
            self.stdout.write(self.style.SUCCESS('Created Basic Users group'))

        # Basic permissions (Free Tier)
        basic_permissions = [
            # Tip permissions (limited)
            Permission.objects.get(codename='view_tip', content_type=tip_ct),
            Permission.objects.get(codename='add_tip', content_type=tip_ct),  # Can create up to 5 tips per day
            
            # Profile permissions
            Permission.objects.get(codename='view_userprofile', content_type=profile_ct),
            Permission.objects.get(codename='change_userprofile', content_type=profile_ct),  # Own profile only
            
            # Social interactions (limited)
            Permission.objects.get(codename='add_comment', content_type=comment_ct),  # Can comment
            Permission.objects.get(codename='view_comment', content_type=comment_ct),
            Permission.objects.get(codename='add_like', content_type=like_ct),  # Can like
            Permission.objects.get(codename='add_follow', content_type=follow_ct),  # Can follow up to 100 users
            
            # Basic event viewing
            Permission.objects.get(codename='view_footballevent', content_type=football_ct),
            Permission.objects.get(codename='view_golfevent', content_type=golf_ct),
            Permission.objects.get(codename='view_tennisevent', content_type=tennis_ct),
            Permission.objects.get(codename='view_hoseracing', content_type=horse_racing_ct),
        ]

        # Add basic permissions to Basic Users group
        basic_group.permissions.set(basic_permissions)
        self.stdout.write(self.style.SUCCESS('Added basic permissions to Basic Users group'))

        # Create Premium Users group
        premium_group, created = Group.objects.get_or_create(name='Premium Users')
        if created:
            self.stdout.write(self.style.SUCCESS('Created Premium Users group'))

        # Premium permissions (Paid Tier)
        premium_permissions = basic_permissions + [
            # Enhanced Tip permissions
            Permission.objects.get(codename='change_tip', content_type=tip_ct),  # Can edit own tips
            Permission.objects.get(codename='delete_tip', content_type=tip_ct),  # Can delete own tips
            
            # Enhanced Social Features
            Permission.objects.get(codename='change_comment', content_type=comment_ct),  # Can edit comments
            Permission.objects.get(codename='delete_comment', content_type=comment_ct),  # Can delete comments
            Permission.objects.get(codename='add_share', content_type=share_ct),  # Can share tips
            
            # Messaging System
            Permission.objects.get(codename='add_message', content_type=message_ct),
            Permission.objects.get(codename='view_message', content_type=message_ct),
            Permission.objects.get(codename='add_messagethread', content_type=message_thread_ct),
            Permission.objects.get(codename='view_messagethread', content_type=message_thread_ct),
            
            # Advanced Features
            Permission.objects.get(codename='view_analytics', content_type=tip_ct),  # Can view detailed tip analytics
            Permission.objects.get(codename='view_odds_history', content_type=tip_ct),  # Can view historical odds
            Permission.objects.get(codename='export_tips', content_type=tip_ct),  # Can export tip data
        ]

        # Add premium permissions to Premium Users group
        premium_group.permissions.set(premium_permissions)
        self.stdout.write(self.style.SUCCESS('Added premium permissions to Premium Users group'))

        self.stdout.write(self.style.SUCCESS('''
        Permission Setup Complete:
        
        Basic (Free) Users can:
        - View all tips and profiles
        - Create up to 5 tips per day
        - Comment on tips
        - Like tips
        - Follow up to 100 users
        - View basic sports events
        - Edit their own profile
        
        Premium Users additionally can:
        - Create unlimited tips
        - Edit and delete their own tips
        - Edit and delete their comments
        - Share tips with their followers
        - Send direct messages
        - View detailed analytics
        - View historical odds data
        - Export their tip data
        - Follow unlimited users
        ''')) 