"""Views for handling user profiles in Tipster Arena."""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import JsonResponse, Http404
from django.db.models import Q, Sum, Avg
from django.views import View
from django.utils import timezone
from datetime import timedelta
import logging

from ..models import UserProfile, Tip, Follow
from ..forms import UserProfileForm

logger = logging.getLogger(__name__)

class ProfileView(LoginRequiredMixin, View):
    """Class-based view for displaying user profiles."""
    
    def get(self, request, username):
        """Handle GET requests for profile display."""
        logger.info(f"[PROFILE VIEW] Incoming username param: '{username}' (type: {type(username)})")
        
        # Check for invalid usernames
        if not username or username == 'None' or username.strip() == '':
            logger.warning(f"[PROFILE VIEW] Invalid username param: '{username}' - redirecting to home.")
            return redirect('home')
            
        try:
            user = get_object_or_404(User, username=username)
            logger.info(f"[PROFILE VIEW] Resolved user: id={user.id}, username='{user.username}'")
        except Http404:
            logger.warning(f"[PROFILE VIEW] User not found for username: '{username}' - redirecting to home.")
            return redirect('home')
            
        try:
            user_profile = user.userprofile
        except UserProfile.DoesNotExist:
            user_profile = UserProfile.objects.get_or_create(user=user)[0]

        # Filter user's own tips and retweeted tips
        user_tips = Tip.objects.filter(
            Q(user=user) | Q(is_retweet=True, user=user)
        ).order_by('-created_at').select_related('user__userprofile', 'original_tip__user__userprofile').distinct()

        for tip in user_tips:
            tip.user_has_retweeted = tip.retweets.filter(user=request.user).exists()

        following_count = Follow.objects.filter(follower=user).count()
        followers_count = Follow.objects.filter(followed=user).count()

        is_owner = request.user == user
        form = UserProfileForm(instance=user_profile) if is_owner else None
        is_following = False if is_owner else Follow.objects.filter(follower=request.user, followed=user).exists()

        # Calculate user stats
        win_rate = user_profile.win_rate
        total_tips = user_profile.total_tips
        wins = user_profile.wins

        # Calculate average odds
        user_own_tips = Tip.objects.filter(user=user)
        average_odds = None
        if user_own_tips.exists():
            total_odds = 0
            valid_tips = 0
            for tip in user_own_tips:
                try:
                    if tip.odds is None or tip.odds_format is None:
                        continue
                    if tip.odds_format.lower() == 'decimal':
                        odds_value = float(tip.odds)
                    elif tip.odds_format.lower() == 'fractional':
                        numerator, denominator = map(float, tip.odds.split('/'))
                        odds_value = (numerator / denominator) + 1
                    else:
                        continue
                    total_odds += odds_value
                    valid_tips += 1
                except (ValueError, ZeroDivisionError):
                    continue
            if valid_tips > 0:
                average_odds = total_odds / valid_tips

        # Calculate premium tip stats
        premium_tips_count = user.tip_set.filter(is_premium_tip=True).count()
        premium_tips_views = user.tip_set.filter(is_premium_tip=True).aggregate(
            total_views=Sum('premium_tip_views')
        )['total_views'] or 0

        # Calculate leaderboard rank
        leaderboard_rank = None
        try:
            # Get all users with minimum activity (similar to TopTipstersLeaderboardView)
            all_users = User.objects.filter(
                userprofile__is_tipster=True
            ).prefetch_related('tip', 'followers', 'tip__likes', 'tip__comments', 'tip__shares')
            
            user_scores = []
            for u in all_users:
                tips = u.tip.all()
                total_tips = tips.count()
                
                if total_tips < 5:  # Skip users with less than 5 tips
                    continue
                
                # Calculate win/loss statistics
                wins = tips.filter(status='win').count()
                total_verified = tips.filter(status__in=['win', 'loss', 'dead_heat', 'void_non_runner']).count()
                win_rate = (wins / total_verified * 100) if total_verified > 0 else 0
                
                # Get engagement statistics
                total_likes = sum(tip.likes.count() for tip in tips)
                total_comments = sum(tip.comments.count() for tip in tips)
                total_shares = sum(tip.shares.count() for tip in tips)
                engagement_score = (total_likes * 1) + (total_comments * 2) + (total_shares * 3)
                
                # Calculate consistency score (recent activity)
                thirty_days_ago = timezone.now() - timedelta(days=30)
                recent_tips = tips.filter(created_at__gte=thirty_days_ago).count()
                consistency_score = min(recent_tips * 10, 100)
                
                # Calculate confidence score
                confidence_tips = tips.exclude(confidence__isnull=True)
                avg_confidence = confidence_tips.aggregate(Avg('confidence'))['confidence__avg'] or 0
                confidence_score = (avg_confidence / 5) * 50
                
                # Calculate comprehensive score
                base_score = win_rate * 2
                volume_score = min(total_tips * 2, 100)
                engagement_bonus = min(engagement_score / 10, 50)
                total_score = base_score + volume_score + engagement_bonus + consistency_score + confidence_score
                
                user_scores.append((u, total_score))
            
            # Sort by total score (highest first)
            user_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Find user's rank
            for rank, (u, score) in enumerate(user_scores, 1):
                if u == user:
                    leaderboard_rank = rank
                    break
                    
        except Exception as e:
            logger.error(f"Error calculating leaderboard rank for user {user.username}: {str(e)}")
            leaderboard_rank = None

        context = {
            'user': user,
            'user_profile': user_profile,
            'user_tips': user_tips,
            'following_count': following_count,
            'followers_count': followers_count,
            'form': form,
            'is_owner': is_owner,
            'is_following': is_following,
            'win_rate': win_rate,
            'total_tips': total_tips,
            'wins': wins,
            'average_odds': average_odds,
            'premium_tips_count': premium_tips_count,
            'premium_tips_views': premium_tips_views,
            'leaderboard_rank': leaderboard_rank,
        }
        return render(request, 'core/profile.html', context)

class ProfileEditView(LoginRequiredMixin, View):
    """Class-based view for editing user profiles."""
    
    def get(self, request, username):
        """Handle GET requests for profile editing."""
        user = get_object_or_404(User, username=username)
        if request.user.username != username:
            return redirect('profile', username=username)
            
        form = UserProfileForm(instance=user.userprofile)
        return render(request, 'core/profile.html', {
            'form': form,
            'user_profile': user.userprofile
        })
    
    def post(self, request, username):
        """Handle POST requests for profile updates."""
        user = get_object_or_404(User, username=username)
        if request.user.username != username:
            return redirect('profile', username=username)
            
        form = UserProfileForm(request.POST, request.FILES, instance=user.userprofile)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'Invalid form data'}) 