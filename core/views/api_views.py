"""Views for Tipster Arena API endpoints."""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os
from django.contrib.auth.models import User
from django.db import models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from core.models import Tip, Follow  # Add Tip and Follow models import
from django.db.models import Q
import logging

__all__ = [
    'current_user_api',
    'upload_chat_image_api',
    'suggested_users_api',
    'trending_tips_api',
    'VerifyTipView',
    'BurstRateThrottle',
    'SustainedRateThrottle'
]

@login_required
def current_user_api(request):
    """Return current user's information."""
    user = request.user
    try:
        profile = user.userprofile
        return JsonResponse({
            'success': True,
            'avatar_url': profile.avatar.url if profile.avatar else None,
            'handle': profile.display_name or user.username,
            'is_admin': user.is_staff,
            'profile': {
                'display_name': profile.display_name or user.username,
                'avatar': profile.avatar.url if profile.avatar else None,
                'description': profile.description or '',
                'kyc_completed': profile.kyc_completed,
                'profile_completed': profile.profile_completed,
                'payment_completed': profile.payment_completed,
            }
        })
    except Exception:  # Removed unused 'e' variable
        # Return a valid profile object with default values
        return JsonResponse({
            'success': True,
            'avatar_url': None,
            'handle': user.username,
            'is_admin': user.is_staff,
            'profile': {
                'display_name': user.username,
                'avatar': None,
                'description': '',
                'kyc_completed': False,
                'profile_completed': False,
                'payment_completed': False,
            }
        })

@login_required
def upload_chat_image_api(request):
    if request.method == 'POST' and request.FILES.get('image'):
        image = request.FILES['image']
        # Validate file type
        if not image.content_type.startswith('image/'):
            return JsonResponse({'success': False, 'error': 'Invalid file type'}, status=400)
        # Save to media/chat_images/
        save_path = os.path.join('chat_images', image.name)
        path = default_storage.save(save_path, ContentFile(image.read()))
        image_url = settings.MEDIA_URL + path
        return JsonResponse({'success': True, 'url': image_url})
    return HttpResponseBadRequest('Invalid request')

@login_required
def suggested_users_api(request):
    """API endpoint to get suggested users to follow."""
    logger = logging.getLogger(__name__)
    try:
        limit = int(request.GET.get('limit', 10))
        
        # Get users that the current user is not following
        following = Follow.objects.filter(follower=request.user).values_list('followed', flat=True)
        suggested_users = User.objects.exclude(
            Q(id__in=following) | Q(id=request.user.id)
        ).select_related('userprofile')[:limit]

        users_data = []
        for user in suggested_users:
            try:
                profile = user.userprofile
                
                # Calculate user stats
                total_tips = Tip.objects.filter(user=user).count()
                followers_count = Follow.objects.filter(followed=user).count()
                
                # Calculate win rate
                tips = Tip.objects.filter(user=user, status__in=['win', 'loss'])
                total_verified_tips = tips.count()
                wins = tips.filter(status='win').count()
                win_rate = (wins / total_verified_tips * 100) if total_verified_tips > 0 else 0
                
                # Ensure avatar_url is always valid
                avatar_url = None
                if profile and profile.avatar:
                    try:
                        avatar_url = profile.avatar.url
                    except (ValueError, IOError):  # Replaced bare except with specific exceptions
                        avatar_url = settings.STATIC_URL + 'img/default-avatar.png'
                else:
                    avatar_url = settings.STATIC_URL + 'img/default-avatar.png'
                
                # Check if current user is following this user
                is_following = Follow.objects.filter(follower=request.user, followed=user).exists()
                
                users_data.append({
                    'username': user.username,
                    'handle': profile.handle if profile and profile.handle else f"@{user.username}",
                    'bio': profile.description if profile and profile.description else '',
                    'avatar_url': avatar_url,
                    'profile_url': f'/profile/{user.username}/',
                    'total_tips': total_tips,
                    'win_rate': round(win_rate, 1),
                    'followers_count': followers_count,
                    'is_following': is_following
                })
                if user.username is None or user.username == 'None' or (profile and (profile.handle is None or profile.handle == 'None')):
                    logger.warning(f"[SUGGESTED USERS API] Invalid username or handle: username='{user.username}', handle='{getattr(profile, 'handle', None)}'")
            except Exception as e:
                logger.error(f"[SUGGESTED USERS API] Exception for user: {str(e)}")
                continue
        logger.info(f"[SUGGESTED USERS API] Returning users: {[u['username'] for u in users_data]}")
        return JsonResponse({
            'success': True,
            'users': users_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def trending_tips_api(request):
    """Return a list of trending tips."""
    logger = logging.getLogger(__name__)
    from core.models import Tip  # Import here to avoid circular imports
    
    # Get tips ordered by popularity (likes + shares + comments)
    trending_tips = Tip.objects.annotate(
        popularity=models.Count('likes') + models.Count('shares') + models.Count('comments')
    ).order_by('-popularity', '-created_at')[:10]  # Limit to 10 tips

    tips_list = []
    for tip in trending_tips:
        tips_list.append({
            'id': tip.id,
            'text': tip.text,
            'username': tip.user.username,
            'likes_count': tip.likes.count(),
            'is_liked': tip.likes.filter(id=request.user.id).exists()
        })
        if tip.user.username is None or tip.user.username == 'None':
            logger.warning(f"[TRENDING TIPS API] Invalid username for tip id={tip.id}: username='{tip.user.username}'")
    logger.info(f"[TRENDING TIPS API] Returning tips for users: {[t['username'] for t in tips_list]}")
    return JsonResponse({'trending_tips': tips_list})

class VerifyTipView(APIView):
    """API view for verifying tips."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, tip_id):
        try:
            tip = Tip.objects.get(id=tip_id)
            if not request.user.is_staff:
                return Response(
                    {'error': 'Only staff members can verify tips'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            status_value = request.data.get('status')
            if not status_value:
                return Response(
                    {'error': 'Status is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if status_value not in ['win', 'loss', 'dead_heat', 'void_non_runner']:
                return Response(
                    {'error': 'Invalid status value'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            tip.status = status_value
            tip.verified = True
            tip.resolution_note = request.data.get('resolution_note', '')
            tip.save()
            
            return Response({
                'message': f'Tip verified as {status_value}',
                'tip_id': tip.id,
                'status': status_value
            })
        except Tip.DoesNotExist:
            return Response(
                {'error': 'Tip not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class BurstRateThrottle(UserRateThrottle):
    """Throttle for burst requests."""
    rate = '5/minute'

class SustainedRateThrottle(UserRateThrottle):
    """Throttle for sustained requests."""
    rate = '100/day' 