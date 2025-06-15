"""Views for handling user interactions in Tipster Arena."""
import logging
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods
from django.http import JsonResponse
from django.contrib.auth.models import User
import json
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache


from ..models import (
    Follow, MessageThread, Message, Like, Share,
    UserProfile, Tip, Comment, Notification
)

logger = logging.getLogger(__name__)

__all__ = [
    'FollowUserView',
    'MessagesView',
    'SendMessageView',
    'GetThreadMessagesView',
    'NotificationsView',
    'MessageSettingsView',
    'BookmarksView',
    'ToggleBookmarkView',
    'LikeCommentView',
    'ShareCommentView',
    'MarkNotificationReadView',
    'GetMessagesView',
    'StartMessageThreadView',
    'SearchUsersView',
    'UpdateMessageSettingsView',
]

class FollowUserView(LoginRequiredMixin, View):
    """Handle following and unfollowing users."""
    
    def get(self, request, username):
        """Get follow status for a user."""
        try:
            if not username:
                return JsonResponse({
                    'success': False,
                    'error': 'Username is required'
                }, status=400)

            user_to_check = get_object_or_404(User, username=username)
            is_following = Follow.objects.filter(
                follower=request.user,
                followed=user_to_check
            ).exists()
            
            follower_count = Follow.objects.filter(followed=user_to_check).count()
            
            return JsonResponse({
                'success': True,
                'is_following': is_following,
                'follower_count': follower_count
            })
            
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'User not found'
            }, status=404)
        except Exception as e:
            logger.error(f"Error in follow status check: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while checking follow status'
            }, status=500)

    def post(self, request, username):
        """Handle follow/unfollow action."""
        try:
            if not username or not username.strip():
                return JsonResponse({
                    'success': False,
                    'error': 'Username is required'
                }, status=400)

            # Rate limiting check
            cache_key = f'follow_attempts_{request.user.id}'
            attempts = cache.get(cache_key, 0)
            if attempts >= 10:  # Max 10 follow/unfollow actions per minute
                logger.warning(f"Rate limit exceeded for user {request.user.username}")
                return JsonResponse({
                    'success': False,
                    'error': 'Too many follow actions. Please wait a minute.'
                }, status=429)
            cache.set(cache_key, attempts + 1, 60)  # Store for 1 minute

            # Get user to follow
            user_to_follow = get_object_or_404(User, username=username)

            # Can't follow yourself
            if request.user == user_to_follow:
                logger.warning(f"User {request.user.username} attempted to follow themselves")
                return JsonResponse({
                    'success': False,
                    'error': 'Cannot follow yourself'
                }, status=400)

            # Check follow limit for free tier users
            if request.user.userprofile.tier == 'free':
                following_count = Follow.objects.filter(follower=request.user).count()
                if following_count >= 20:
                    logger.info(f"Free tier user {request.user.username} hit follow limit")
                    return JsonResponse({
                        'success': False,
                        'error': 'Free tier limit reached. Upgrade to Premium for unlimited follows!'
                    }, status=403)

            # Check if already following
            follow_exists = Follow.objects.filter(
                follower=request.user,
                followed=user_to_follow
            ).exists()

            if follow_exists:
                # Unfollow
                Follow.objects.filter(
                    follower=request.user,
                    followed=user_to_follow
                ).delete()
                is_following = False
                message = 'Successfully unfollowed user'
                logger.info(f"User {request.user.username} unfollowed {username}")
            else:
                try:
                    # Follow
                    Follow.objects.create(
                        follower=request.user,
                        followed=user_to_follow
                    )
                    is_following = True
                    message = 'Successfully followed user'
                    logger.info(f"User {request.user.username} followed {username}")
                except Exception as e:
                    if 'unique constraint' in str(e).lower():
                        # If we hit a race condition where the follow was created between our check and create
                        is_following = True
                        message = 'Already following this user'
                        logger.info(f"User {request.user.username} already following {username}")
                    else:
                        raise  # Re-raise if it's a different error

            # Get updated follower count
            follower_count = Follow.objects.filter(followed=user_to_follow).count()

            return JsonResponse({
                'success': True,
                'message': message,
                'is_following': is_following,
                'follower_count': follower_count
            })

        except User.DoesNotExist:
            logger.error(f"User not found: {username}")
            return JsonResponse({
                'success': False,
                'error': 'User not found'
            }, status=404)
        except Exception as e:
            logger.error(f"Error in follow_user view: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while processing your request'
            }, status=500)

class MessagesView(LoginRequiredMixin, View):
    """Display message threads and individual thread messages."""
    def get(self, request, thread_id=None):
        user = request.user
        message_threads = (MessageThread.objects.filter(participants=user)
                          .order_by('-updated_at')[:20]
                          .prefetch_related('participants__userprofile'))

        threads_with_participants = []
        for thread in message_threads:
            other_participant = thread.participants.exclude(id=user.id).first()
            last_message = thread.messages.last()
            follower_count = other_participant.followers.count() if other_participant else 0
            followed_by = Follow.objects.filter(followed=other_participant).exclude(follower=user).order_by('?')[:3]
            followed_by_names = [f.follower.username for f in followed_by]
            threads_with_participants.append({
                'thread': thread,
                'other_participant': other_participant,
                'last_message': last_message,
                'follower_count': follower_count,
                'followed_by': followed_by_names,
            })

        selected_thread = None
        messages = []
        if thread_id:
            selected_thread = get_object_or_404(MessageThread, id=thread_id, participants=user)
            selected_thread.other_participant = selected_thread.participants.exclude(id=user.id).first()
            messages = selected_thread.messages.all().order_by('created_at')

        context = {
            'message_threads': threads_with_participants,
            'selected_thread': selected_thread,
            'messages': messages,
        }
        return render(request, 'core/messages.html', context)

class SendMessageView(LoginRequiredMixin, View):
    """Handle sending messages in a thread."""
    def post(self, request, thread_id=None):
        try:
            content = request.POST.get('content', '').strip()
            if not content:
                return JsonResponse({
                    'success': False,
                    'error': 'Message content is required'
                }, status=400)

            # Rate limiting
            cache_key = f'message_attempts_{request.user.id}'
            attempts = cache.get(cache_key, 0)
            if attempts >= 20:  # Max 20 messages per minute
                logger.warning(f"Rate limit exceeded for user {request.user.username}")
                return JsonResponse({
                    'success': False,
                    'error': 'Too many messages. Please wait a minute.'
                }, status=429)
            cache.set(cache_key, attempts + 1, 60)  # Store for 1 minute

            if thread_id:
                # Existing thread
                thread = get_object_or_404(MessageThread, id=thread_id, participants=request.user)
                other_participant = thread.participants.exclude(id=request.user.id).first()
            else:
                # New thread
                recipient_username = request.POST.get('recipient')
                if not recipient_username:
                    return JsonResponse({
                        'success': False,
                        'error': 'Recipient is required for new threads'
                    }, status=400)

                recipient = get_object_or_404(User, username=recipient_username)
                if recipient == request.user:
                    return JsonResponse({
                        'success': False,
                        'error': 'Cannot send message to yourself'
                    }, status=400)

                # Check if thread already exists
                existing_thread = MessageThread.objects.filter(
                    participants=request.user
                ).filter(
                    participants=recipient
                ).first()

                if existing_thread:
                    thread = existing_thread
                else:
                    thread = MessageThread.objects.create()
                    thread.participants.add(request.user, recipient)
                other_participant = recipient

            # Create message
            message = Message.objects.create(
                thread=thread,
                sender=request.user,
                content=content
            )

            # Update thread's updated_at
            thread.save()  # This will update the updated_at field

            return JsonResponse({
                'success': True,
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'created_at': message.created_at.isoformat(),
                    'sender': {
                        'username': message.sender.username,
                        'avatar_url': message.sender.userprofile.avatar.url if message.sender.userprofile.avatar else None
                    }
                }
            })

        except Exception as e:
            logger.error(f"Error in send_message view: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while sending the message'
            }, status=500)

class GetThreadMessagesView(LoginRequiredMixin, View):
    """Get messages for a specific thread."""
    def get(self, request, thread_id):
        try:
            thread = get_object_or_404(MessageThread, id=thread_id, participants=request.user)
            messages = thread.messages.order_by('created_at')
            
            messages_data = []
            for message in messages:
                messages_data.append({
                    'id': message.id,
                    'content': message.content,
                    'created_at': message.created_at.isoformat(),
                    'sender': {
                        'username': message.sender.username,
                        'avatar_url': message.sender.userprofile.avatar.url if message.sender.userprofile.avatar else None
                    }
                })
            
            return JsonResponse({
                'success': True,
                'messages': messages_data
            })
            
        except Exception as e:
            logger.error(f"Error in get_thread_messages view: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while retrieving messages'
            }, status=500)

class NotificationsView(LoginRequiredMixin, View):
    """Display user notifications."""
    def get(self, request):
        try:
            notifications = Notification.objects.filter(
                user=request.user
            ).order_by('-created_at')[:50]
            
            return render(request, 'core/notifications.html', {
                'notifications': notifications
            })
            
        except Exception as e:
            logger.error(f"Error in notifications view: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while retrieving notifications'
            }, status=500)

class MessageSettingsView(LoginRequiredMixin, View):
    """Render message notification settings page."""
    def get(self, request):
        user = request.user
        if not hasattr(user, 'userprofile'):
            UserProfile.objects.get_or_create(user=user)

        return render(request, 'core/message_settings.html', {
            'user': user,
        })

class BookmarksView(LoginRequiredMixin, View):
    """Display user's bookmarked tips."""
    def get(self, request):
        try:
            bookmarked_tips = Tip.objects.filter(
                bookmarks=request.user
            ).order_by('-created_at')
            
            return render(request, 'core/bookmarks.html', {
                'bookmarked_tips': bookmarked_tips
            })
        except Exception as e:
            logger.error(f"Error in bookmarks view: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while retrieving bookmarks'
            }, status=500)

class LikeCommentView(LoginRequiredMixin, View):
    """Handle liking and unliking comments."""
    def post(self, request):
        try:
            comment_id = request.POST.get('comment_id')
            if not comment_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Comment ID is required'
                }, status=400)

            comment = get_object_or_404(Comment, id=comment_id)
            like, created = Like.objects.get_or_create(
                user=request.user,
                comment=comment
            )

            if not created:
                like.delete()
                is_liked = False
            else:
                is_liked = True

            return JsonResponse({
                'success': True,
                'is_liked': is_liked,
                'likes_count': comment.likes.count()
            })

        except Exception as e:
            logger.error(f"Error in like_comment view: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while processing the like'
            }, status=500)

class ShareCommentView(LoginRequiredMixin, View):
    """Handle sharing comments."""
    def post(self, request):
        try:
            comment_id = request.POST.get('comment_id')
            if not comment_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Comment ID is required'
                }, status=400)

            comment = get_object_or_404(Comment, id=comment_id)
            share, created = Share.objects.get_or_create(
                user=request.user,
                comment=comment
            )

            if not created:
                share.delete()
                is_shared = False
            else:
                is_shared = True

            return JsonResponse({
                'success': True,
                'is_shared': is_shared,
                'shares_count': comment.shares.count()
            })

        except Exception as e:
            logger.error(f"Error in share_comment view: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while processing the share'
            }, status=500)

class MarkNotificationReadView(LoginRequiredMixin, View):
    """Mark notifications as read."""
    def post(self, request):
        try:
            notification_ids = request.POST.getlist('notification_ids[]')
            if not notification_ids:
                return JsonResponse({
                    'success': False,
                    'error': 'No notification IDs provided'
                }, status=400)

            notifications = Notification.objects.filter(
                id__in=notification_ids,
                user=request.user
            )
            notifications.update(read=True)

            return JsonResponse({
                'success': True,
                'message': f'Marked {notifications.count()} notifications as read'
            })

        except Exception as e:
            logger.error(f"Error in mark_notification_read view: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while marking notifications as read'
            }, status=500)

class GetMessagesView(LoginRequiredMixin, View):
    """Get all message threads for a user."""
    def get(self, request):
        try:
            threads = MessageThread.objects.filter(
                participants=request.user
            ).order_by('-updated_at')

            messages_data = []
            for thread in threads:
                other_participant = thread.participants.exclude(id=request.user.id).first()
                last_message = thread.messages.last()
                
                if last_message:
                    messages_data.append({
                        'thread_id': thread.id,
                        'username': other_participant.username,
                        'avatar': other_participant.userprofile.avatar.url if other_participant.userprofile.avatar else None,
                        'last_message': last_message.content,
                        'last_message_date': last_message.created_at.isoformat(),
                        'unread_count': thread.messages.filter(
                            sender=other_participant,
                            is_read=False
                        ).count()
                    })

            return JsonResponse(messages_data, safe=False)

        except Exception as e:
            logger.error(f"Error in get_messages view: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while retrieving messages'
            }, status=500)

class StartMessageThreadView(LoginRequiredMixin, View):
    """Start a new message thread with users."""
    def post(self, request):
        try:
            # Try to get data from JSON first
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                user_ids = data.get('user_ids', [])
            else:
                # Fall back to form data
                user_ids = request.POST.getlist('user_ids')

            if not user_ids:
                return JsonResponse({
                    'success': False,
                    'error': 'At least one recipient is required'
                }, status=400)

            # Get all recipients
            recipients = User.objects.filter(id__in=user_ids)
            if not recipients.exists():
                return JsonResponse({
                    'success': False,
                    'error': 'One or more recipients not found'
                }, status=404)

            # Check if thread already exists with these exact participants
            existing_thread = MessageThread.objects.filter(
                participants=request.user
            ).filter(
                participants__in=recipients
            ).distinct()

            if existing_thread.exists():
                thread = existing_thread.first()
            else:
                thread = MessageThread.objects.create()
                thread.participants.add(request.user)
                thread.participants.add(*recipients)

            # Get the first recipient for the response
            first_recipient = recipients.first()
            return JsonResponse({
                'success': True,
                'thread_id': thread.id,
                'user': {
                    'username': first_recipient.username,
                    'avatar': first_recipient.userprofile.avatar.url if first_recipient.userprofile.avatar else None
                }
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error in start_message_thread view: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while starting the message thread'
            }, status=500)

class UpdateMessageSettingsView(LoginRequiredMixin, View):
    """Update user's message notification settings."""
    def post(self, request):
        try:
            data = json.loads(request.body)
            user = request.user
            
            if not hasattr(user, 'userprofile'):
                UserProfile.objects.get_or_create(user=user)
            
            # Update notification settings
            user.userprofile.email_notifications = data.get('email_notifications', True)
            user.userprofile.push_notifications = data.get('push_notifications', True)
            user.userprofile.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Message settings updated successfully'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error in update_message_settings view: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while updating message settings'
            }, status=500)

class SearchUsersView(LoginRequiredMixin, View):
    """Search for users by username."""
    def get(self, request):
        query = request.GET.get('q', '').strip()
        if not query or len(query) < 2:
            return JsonResponse({'users': []})

        users = User.objects.filter(
            username__icontains=query
        ).exclude(
            id=request.user.id
        ).select_related('userprofile')[:10]

        users_data = [{
            'id': user.id,
            'username': user.username,
            'avatar': user.userprofile.avatar.url if hasattr(user, 'userprofile') and user.userprofile.avatar else None,
        } for user in users]

        return JsonResponse({'users': users_data})

@login_required
@require_POST
def update_message_settings(request):
    """Update user's message settings."""
    try:
        data = json.loads(request.body)
        setting = data.get('allow_messages')
        
        if setting not in ['no_one', 'followers', 'everyone']:
            return JsonResponse({
                'success': False,
                'error': 'Invalid setting value'
            }, status=400)
            
        user_profile = request.user.userprofile
        user_profile.allow_messages = setting
        user_profile.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Message settings updated successfully'
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error updating message settings: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

class ToggleBookmarkView(LoginRequiredMixin, View):
    """Handle toggling bookmarks for tips."""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            tip_id = data.get('tip_id')
            
            if not tip_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Tip ID is required'
                }, status=400)

            # Rate limiting
            cache_key = f'bookmark_attempts_{request.user.id}'
            attempts = cache.get(cache_key, 0)
            if attempts >= 20:  # Max 20 bookmark actions per minute
                logger.warning(f"Rate limit exceeded for user {request.user.username}")
                return JsonResponse({
                    'success': False,
                    'error': 'Too many bookmark actions. Please wait a minute.'
                }, status=429)
            cache.set(cache_key, attempts + 1, 60)  # Store for 1 minute

            tip = get_object_or_404(Tip, id=tip_id)
            
            # Check if already bookmarked
            bookmark_exists = tip.bookmarks.filter(id=request.user.id).exists()
            
            if bookmark_exists:
                # Remove bookmark
                tip.bookmarks.remove(request.user)
                is_bookmarked = False
                message = 'Tip removed from bookmarks'
                logger.info(f"User {request.user.username} removed tip {tip_id} from bookmarks")
            else:
                # Add bookmark
                tip.bookmarks.add(request.user)
                is_bookmarked = True
                message = 'Tip added to bookmarks'
                logger.info(f"User {request.user.username} bookmarked tip {tip_id}")

            return JsonResponse({
                'success': True,
                'message': message,
                'is_bookmarked': is_bookmarked
            })

        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body")
            return JsonResponse({
                'success': False,
                'error': 'Invalid request format'
            }, status=400)
        except Tip.DoesNotExist:
            logger.error(f"Tip not found: {tip_id}")
            return JsonResponse({
                'success': False,
                'error': 'Tip not found'
            }, status=404)
        except Exception as e:
            logger.error(f"Error in toggle_bookmark view: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while processing your request'
            }, status=500) 