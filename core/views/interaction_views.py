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
    'follow_user',
    'messages_view',
    'send_message',
    'get_thread_messages',
    'notifications',
    'message_settings_view',
    'bookmarks',
    'toggle_bookmark',
    'like_comment',
    'share_comment',
    'mark_notification_read',
    'get_messages',
    'start_message_thread',
    'search_users',
    'update_message_settings',
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

@login_required
def messages_view(request, thread_id=None):
    """Display message threads and individual thread messages."""
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

@login_required
def send_message(request, thread_id=None):
    """Handle sending a new message or creating a new message thread."""
    try:
        # Try to get data from JSON first
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            content = data.get('content')
            image = request.FILES.get('image')
            gif_url = data.get('gif_url')
        else:
            # Fall back to form data
            content = request.POST.get('content')
            image = request.FILES.get('image')
            gif_url = request.POST.get('gif_url')

        if not content and not image and not gif_url:
            return JsonResponse({'success': False, 'error': 'Message content, image, or GIF URL must be provided'}, status=400)

        if thread_id:
            thread = get_object_or_404(MessageThread, id=thread_id, participants=request.user)
        else:
            recipient_username = request.POST.get('recipient_username')
            if not recipient_username:
                return JsonResponse({'success': False, 'error': 'Recipient username required'}, status=400)
            recipient = get_object_or_404(User, username=recipient_username)
            if recipient == request.user:
                return JsonResponse({'success': False, 'error': 'Cannot message yourself'}, status=400)

            thread = MessageThread.objects.filter(participants=request.user).filter(participants=recipient).first()
            if not thread:
                thread = MessageThread.objects.create()
                thread.participants.add(request.user, recipient)

        message = Message.objects.create(
            thread=thread,
            sender=request.user,
            content=content or '',
            image=image,
            gif_url=gif_url
        )

        # Send WebSocket message
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"thread_{thread.id}",
            {
                "type": "direct_message_broadcast",
                "sender": request.user.username,
                "message": message.content,
                "image_url": message.image.url if message.image else None,
                "gif_url": message.gif_url,
                "created_at": message.created_at.isoformat(),
                "message_id": message.id
            }
        )

        return JsonResponse({
            'success': True,
            'message_id': message.id,
            'content': message.content,
            'created_at': message.created_at.isoformat(),
            'sender': message.sender.username,
            'thread_id': thread.id,
            'image': message.image.url if message.image else None,
            'gif_url': message.gif_url if message.gif_url else None,
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error in send_message view: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def get_thread_messages(request, thread_id):
    """Retrieve and return messages for a specific thread."""
    thread = get_object_or_404(MessageThread, id=thread_id, participants=request.user)
    messages = thread.messages.all().order_by('created_at')
    
    # Get the other participant's information
    other_participant = thread.participants.exclude(id=request.user.id).first()
    user_info = None
    if other_participant:
        user_info = {
            'username': other_participant.username,
            'avatar': other_participant.userprofile.avatar.url if hasattr(other_participant, 'userprofile') and other_participant.userprofile.avatar else '/static/images/default-avatar.png'
        }
    
    messages_data = [
        {
            'id': msg.id,
            'content': msg.content,
            'sender': msg.sender.username,
            'created_at': msg.created_at.isoformat(),
            'image': msg.image.url if msg.image else None,
            'gif_url': msg.gif_url
        }
        for msg in messages
    ]
    return JsonResponse({
        'success': True, 
        'messages': messages_data,
        'user': user_info
    })

@login_required
def notifications(request):
    """Display notifications for likes, follows, and shares."""
    user = request.user
    like_notifications = (Like.objects.filter(tip__user=user)
                         .order_by('-created_at')[:20]
                         .select_related('user', 'tip', 'user__userprofile'))
    follow_notifications = (Follow.objects.filter(followed=user)
                           .order_by('-created_at')[:20]
                           .select_related('follower', 'follower__userprofile'))
    share_notifications = (Share.objects.filter(tip__user=user)
                          .order_by('-created_at')[:20]
                          .select_related('user', 'tip', 'user__userprofile'))

    return render(request, 'core/notifications.html', {
        'like_notifications': like_notifications,
        'follow_notifications': follow_notifications,
        'share_notifications': share_notifications,
    })

@login_required
def message_settings_view(request):
    """Render message notification settings page."""
    user = request.user
    if not hasattr(user, 'userprofile'):
        UserProfile.objects.get_or_create(user=user)

    return render(request, 'core/message_settings.html', {
        'user': user,
    })

@login_required
def bookmarks(request):
    """Display bookmarked tips for the current user."""
    user = request.user
    bookmarked_tips = Tip.objects.filter(bookmarks=user).order_by('-created_at')
    
    return render(request, 'core/bookmarks.html', {
        'bookmarked_tips': bookmarked_tips,
    })

class ToggleBookmarkView(LoginRequiredMixin, View):
    """Handle toggling bookmark status for a tip."""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            tip_id = data.get('tip_id')
            
            if not tip_id:
                return JsonResponse({'success': False, 'error': 'Missing tip_id'}, status=400)
                
            tip = get_object_or_404(Tip, id=tip_id)
            user = request.user
            
            if tip.bookmarks.filter(id=user.id).exists():
                tip.bookmarks.remove(user)
                return JsonResponse({
                    'success': True,
                    'message': 'Tip unbookmarked',
                    'is_bookmarked': False
                })
            else:
                tip.bookmarks.add(user)
                return JsonResponse({
                    'success': True,
                    'message': 'Tip bookmarked',
                    'is_bookmarked': True
                })
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error("Error toggling bookmark: %s", str(e))
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_POST
def like_comment(request):
    """Handle liking/unliking a comment."""
    comment_id = request.POST.get('comment_id')
    comment = get_object_or_404(Comment, id=comment_id)
    
    if comment.likes.filter(id=request.user.id).exists():
        comment.likes.remove(request.user)
        return JsonResponse({'success': True, 'message': 'Unliked', 'is_liked': False})
    else:
        comment.likes.add(request.user)
        return JsonResponse({'success': True, 'message': 'Liked', 'is_liked': True})

@login_required
@require_POST
def share_comment(request):
    """Handle sharing a comment."""
    comment_id = request.POST.get('comment_id')
    comment = get_object_or_404(Comment, id=comment_id)
    
    Share.objects.create(
        user=request.user,
        comment=comment
    )
    
    return JsonResponse({'success': True, 'message': 'Comment shared'})

@login_required
@require_POST
def mark_notification_read(request):
    """Mark a notification as read for the current user."""
    try:
        data = json.loads(request.body)
        notification_id = data.get('notification_id')
        # type = data.get('type')  # Not used, but could be for future
        if not notification_id:
            return JsonResponse({'success': False, 'error': 'Missing notification_id'}, status=400)
        notification = Notification.objects.filter(id=notification_id, user=request.user).first()
        if not notification:
            return JsonResponse({'success': False, 'error': 'Notification not found'}, status=404)
        notification.read = True
        notification.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def get_messages(request):
    """Get all message threads for the current user."""
    user = request.user
    message_threads = (MessageThread.objects.filter(participants=user)
                      .order_by('-updated_at')
                      .prefetch_related('participants__userprofile'))

    threads_data = []
    for thread in message_threads:
        other_participant = thread.participants.exclude(id=user.id).first()
        last_message = thread.messages.last()
        
        threads_data.append({
            'thread_id': thread.id,
            'username': other_participant.username if other_participant else None,
            'avatar': other_participant.userprofile.avatar.url if other_participant and hasattr(other_participant, 'userprofile') and other_participant.userprofile.avatar else None,
            'last_message': last_message.content if last_message else '',
            'last_message_date': last_message.created_at if last_message else thread.updated_at,
            'unread_count': thread.messages.filter(is_read=False).exclude(sender=user).count()
        })

    return JsonResponse(threads_data, safe=False)

@login_required
def start_message_thread(request):
    """Start a new message thread with one or more users."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        user_ids = data.get('user_ids', [])
        
        if not user_ids:
            return JsonResponse({'success': False, 'error': 'No users specified'}, status=400)

        # Get the current user
        current_user = request.user
        
        # Get all participants including current user
        participants = [current_user] + [User.objects.get(id=uid) for uid in user_ids]
        
        # Check if a thread already exists with these exact participants
        existing_thread = MessageThread.objects.filter(participants=current_user)
        for participant in participants[1:]:
            existing_thread = existing_thread.filter(participants=participant)
        
        if existing_thread.exists():
            thread = existing_thread.first()
        else:
            # Create new thread
            thread = MessageThread.objects.create()
            thread.participants.add(*participants)

        # Get the other participant's information
        other_participant = thread.participants.exclude(id=current_user.id).first()
        user_info = None
        if other_participant:
            user_info = {
                'username': other_participant.username,
                'avatar': other_participant.userprofile.avatar.url if hasattr(other_participant, 'userprofile') and other_participant.userprofile.avatar else '/static/images/default-avatar.png'
            }

        return JsonResponse({
            'success': True,
            'thread_id': thread.id,
            'user': user_info
        })

    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'One or more users not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def search_users(request):
    """Search for users by username."""
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