from django.views.decorators.csrf import csrf_exempt
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
    except Exception as e:
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
                    except:
                        avatar_url = settings.STATIC_URL + 'img/default-avatar.png'
                else:
                    avatar_url = settings.STATIC_URL + 'img/default-avatar.png'
                
                users_data.append({
                    'username': user.username,
                    'handle': profile.handle if profile and profile.handle else f"@{user.username}",
                    'bio': profile.description if profile and profile.description else '',
                    'avatar_url': avatar_url,
                    'profile_url': f'/profile/{user.username}/',
                    'total_tips': total_tips,
                    'win_rate': round(win_rate, 1),
                    'followers_count': followers_count
                })
            except Exception as e:
                # Skip users with invalid profiles
                continue

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

    return JsonResponse({'trending_tips': tips_list})

class VerifyTipView(APIView):
    """API view for verifying tips."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, tip_id):
        try:
            tip = Tip.objects.get(id=tip_id)
            if tip.author != request.user:
                return Response(
                    {'error': 'You can only verify your own tips'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            tip.verified = True
            tip.save()
            
            return Response({
                'message': 'Tip verified successfully',
                'tip_id': tip.id
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