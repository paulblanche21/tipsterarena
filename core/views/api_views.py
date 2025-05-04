"""API views for Tipster Arena."""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import api_view
from rest_framework.throttling import  AnonRateThrottle
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
from django.db.models import Count, F
from django.core.exceptions import ValidationError

from ..models import Tip, Follow, User

logger = logging.getLogger(__name__)

class BurstRateThrottle(AnonRateThrottle):
    rate = '60/minute'

class SustainedRateThrottle(AnonRateThrottle):
    rate = '1000/day'

@api_view(['GET'])
def current_user_api(request):
    """Get current user information."""
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)
        user = request.user
        profile = getattr(user, 'userprofile', None)
        avatar_url = profile.avatar.url if profile and profile.avatar else settings.STATIC_URL + 'img/default-avatar.png'
        handle = profile.handle or user.username if profile else user.username
        return JsonResponse({
            'success': True,
            'avatar_url': avatar_url,
            'handle': handle,
            'username': user.username,
            'is_admin': user.is_staff or user.is_superuser
        })
    except (ValueError, TypeError) as e:
        logger.error("Error in current_user_api: %s", str(e))
        return JsonResponse({'success': False, 'error': 'Internal server error'}, status=500)

@api_view(['GET'])
def suggested_users_api(request):
    """Get suggested users for the current user."""
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)
        logger.info("Fetching suggested users for user: %s", request.user.username)
        current_user = request.user
        followed_users = Follow.objects.filter(follower=current_user).values_list('followed_id', flat=True)
        logger.debug("Followed users: %s", list(followed_users))
        suggested_users = User.objects.filter(
            tip__isnull=False
        ).exclude(
            id__in=followed_users
        ).exclude(
            id=current_user.id
        ).distinct()[:10]
        logger.debug("Suggested users count: %s", suggested_users.count())

        users_data = []
        for user in suggested_users:
            profile = getattr(user, 'userprofile', None)
            avatar_url = profile.avatar.url if profile and profile.avatar else settings.STATIC_URL + 'img/default-avatar.png'
            bio = profile.description or "No bio available" if profile else "No bio available"
            users_data.append({
                'username': user.username,
                'avatar_url': avatar_url,
                'bio': bio,
                'profile_url': f"/profile/{user.username}/"
            })

        logger.info("Returning %s suggested users", len(users_data))
        return JsonResponse({'success': True, 'users': users_data})
    except Exception as e:
        logger.error("Error in suggested_users_api: %s", str(e))
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@api_view(['GET'])
def trending_tips_api(request):
    """Get trending tips."""
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)
        logger.info("Fetching trending tips for user: %s", request.user.username)
        trending_tips = Tip.objects.annotate(
            total_likes=Count('likes'),
            total_shares=Count('shares')
        ).annotate(
            total_engagement=F('total_likes') + F('total_shares')
        ).order_by('-total_engagement')[:4]
        logger.debug("Trending tips count: %s", trending_tips.count())

        tips_data = []
        for tip in trending_tips:
            profile = getattr(tip.user, 'userprofile', None)
            avatar_url = profile.avatar.url if profile and profile.avatar else settings.STATIC_URL + 'img/default-avatar.png'
            handle = profile.handle.lstrip('@') if profile and profile.handle else tip.user.username
            tips_data.append({
                'username': tip.user.username,
                'handle': handle,
                'avatar_url': avatar_url,
                'text': tip.text[:50],
                'likes': tip.total_likes,
                'profile_url': f"/profile/{tip.user.username}/",
            })

        logger.info("Returning %s trending tips", len(tips_data))
        return JsonResponse({'success': True, 'trending_tips': tips_data})
    except Exception as e:
        logger.error("Error in trending_tips_api: %s", str(e))
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

class VerifyTipView(APIView):
    """API endpoint for verifying tips."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

    def post(self, request):
        print("VerifyTipView hit!")
        print(f"Request user: {request.user}, Is staff: {request.user.is_staff}")
        print(f"Request data: {request.data}")

        tip_id = request.data.get('tip_id')
        new_status = request.data.get('status')
        resolution_note = request.data.get('resolution_note', '')

        VALID_STATUSES = ['pending', 'win', 'loss', 'dead_heat', 'void_non_runner']
        if new_status not in VALID_STATUSES:
            return Response({'success': False, 'error': f'Invalid status: {new_status}'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            tip = Tip.objects.get(id=tip_id)
            if tip.status != 'pending':
                return Response({'success': False, 'error': 'Tip is already verified'}, status=status.HTTP_400_BAD_REQUEST)

            tip.status = new_status
            tip.resolution_note = resolution_note
            tip.verified_at = timezone.now()
            tip.save()

            user = tip.user
            user_tips = Tip.objects.filter(user=user, status__in=['win', 'loss', 'dead_heat', 'void_non_runner'])
            total_tips = user_tips.count()
            wins = user_tips.filter(status='win').count()
            win_rate = (wins / total_tips * 100) if total_tips > 0 else 0

            user.userprofile.win_rate = win_rate
            user.userprofile.total_tips = total_tips
            user.userprofile.wins = wins
            user.userprofile.save()

            return Response({'success': True, 'win_rate': win_rate}, status=status.HTTP_200_OK)
        except Tip.DoesNotExist:
            return Response({'success': False, 'error': 'Tip not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST) 