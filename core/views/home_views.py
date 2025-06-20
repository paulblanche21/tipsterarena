"""Views for handling the home page in Tipster Arena."""

from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.db.models import Count, F, Q
from django.conf import settings

from ..models import User, UserProfile, Tip, Follow

class HomeView(LoginRequiredMixin, View):
    """Class-based view for the home page."""
    
    def get(self, request):
        """Handle GET requests for the home page."""
        # Get recent tips including retweets
        tips = Tip.objects.filter(
            Q(is_retweet=False) | Q(is_retweet=True, user=request.user)
        ).order_by('-created_at')[:20]
        
        for tip in tips:
            if not hasattr(tip.user, 'userprofile'):
                UserProfile.objects.get_or_create(user=tip.user)
            # Annotate with user_has_retweeted for template logic
            tip.user_has_retweeted = tip.retweets.filter(user=request.user).exists()

        # Get trending tips based on engagement
        trending_tips = Tip.objects.annotate(
            total_likes=Count('likes'),
            total_shares=Count('shares')
        ).annotate(
            total_engagement=F('total_likes') + F('total_shares')
        ).order_by('-total_engagement')[:4]

        for tip in trending_tips:
            if not hasattr(tip.user, 'userprofile'):
                UserProfile.objects.get_or_create(user=tip.user)

        # Get suggested tipsters
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
                handle = profile.handle or f"@{user.username}"
            except UserProfile.DoesNotExist:
                avatar_url = settings.STATIC_URL + 'img/default-avatar.png'
                bio = "No bio available"
                handle = f"@{user.username}"
                
            # Calculate user stats
            total_tips = Tip.objects.filter(user=user).count()
            followers_count = Follow.objects.filter(followed=user).count()
            
            # Calculate win rate
            tips = Tip.objects.filter(user=user, status__in=['win', 'loss'])
            total_verified_tips = tips.count()
            wins = tips.filter(status='win').count()
            win_rate = (wins / total_verified_tips * 100) if total_verified_tips > 0 else 0
            
            suggested_tipsters.append({
                'username': user.username,
                'handle': handle,
                'avatar_url': avatar_url,
                'bio': bio,
                'total_tips': total_tips,
                'win_rate': round(win_rate, 1),
                'followers_count': followers_count
            })

        context = {
            'tips': tips,
            'trending_tips': trending_tips,
            'suggested_tipsters': suggested_tipsters,
        }
        return render(request, 'core/home.html', context) 