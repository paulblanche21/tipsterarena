"""Views for handling sport-specific pages in Tipster Arena."""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, F
from django.views import View

from ..models import Tip, UserProfile, Follow, User
from django.conf import settings

class SportView(View):
    def get(self, request, sport):
        valid_sports = [
            'football', 'golf', 'tennis', 'horse_racing',
            'american_football', 'baseball', 'basketball', 'boxing', 'cricket',
            'cycling', 'darts', 'gaelic_games', 'greyhound_racing', 'motor_sport',
            'rugby_union', 'snooker', 'volleyball'
        ]
        if sport not in valid_sports:
            return render(request, 'core/404.html', status=404)

        tips = Tip.objects.filter(sport=sport).order_by('-created_at')[:20]
        return render(request, 'core/sport.html', {
            'tips': tips,
            'sport': sport,
        })

class HomeView(View):
    def get(self, request):
        """Render the home page with tips, trending content, and user suggestions."""
        tips = Tip.objects.all().order_by('-created_at')[:20]
        for tip in tips:
            if not hasattr(tip.user, 'userprofile'):
                UserProfile.objects.get_or_create(user=tip.user)

        trending_tips = Tip.objects.annotate(
            total_likes=Count('likes'),
            total_shares=Count('shares')
        ).annotate(
            total_engagement=F('total_likes') + F('total_shares')
        ).order_by('-total_engagement')[:4]

        for tip in trending_tips:
            if not hasattr(tip.user, 'userprofile'):
                UserProfile.objects.get_or_create(user=tip.user)

        current_user = request.user
        followed_users = Follow.objects.filter(follower=current_user).values_list('followed_id', flat=True)
        suggested_users = User.objects.filter(
            tip__isnull=False
        ).exclude(
            id__in=followed_users
        ).exclude(
            id=current_user.id
        ).distinct()[:10]

        suggested_tipsters = []
        for user in suggested_users:
            try:
                profile = user.userprofile
                avatar_url = profile.avatar.url if profile.avatar else settings.STATIC_URL + 'img/default-avatar.png'
                bio = profile.description or "No bio available"
            except UserProfile.DoesNotExist:
                avatar_url = settings.STATIC_URL + 'img/default-avatar.png'
                bio = "No bio available"
            suggested_tipsters.append({
                'username': user.username,
                'avatar_url': avatar_url,
                'bio': bio,
            })

        context = {
            'tips': tips,
            'trending_tips': trending_tips,
            'suggested_tipsters': suggested_tipsters,
        }
        return render(request, 'core/home.html', context) 