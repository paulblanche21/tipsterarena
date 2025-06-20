"""Management command to create default user groups and permissions."""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import (
    Tip, UserProfile, Comment, Follow, Like, Share, 
    Message, MessageThread
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

        # Create Free Users group
        free_group, created = Group.objects.get_or_create(name='Free Users')
        if created:
            self.stdout.write(self.style.SUCCESS('Created Free Users group'))

        # Free permissions (Free Tier)
        free_permissions = [
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
        ]

        # Add free permissions to Free Users group
        free_group.permissions.set(free_permissions)
        self.stdout.write(self.style.SUCCESS('Added free permissions to Free Users group'))

        # Create Premium Users group
        premium_group, created = Group.objects.get_or_create(name='Premium Users')
        if created:
            self.stdout.write(self.style.SUCCESS('Created Premium Users group'))

        # Premium permissions (Paid Tier)
        premium_permissions = free_permissions + [
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
        ]

        # Add premium permissions to Premium Users group
        premium_group.permissions.set(premium_permissions)
        self.stdout.write(self.style.SUCCESS('Added premium permissions to Premium Users group'))

        self.stdout.write(self.style.SUCCESS('''
        Permission Setup Complete:
        
        Free Users can:
        - View all tips and profiles
        - Create up to 5 tips per day
        - Comment on tips
        - Like tips
        - Follow up to 100 users
        - Edit their own profile
        
        Premium Users additionally can:
        - Create unlimited tips
        - Edit and delete their own tips
        - Edit and delete their comments
        - Share tips with their followers
        - Send direct messages
        - Follow unlimited users
        ''')) 