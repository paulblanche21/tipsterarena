"""
Badge system for Tipster Arena.
Handles badge awarding, checking, and management.
"""

from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta


class BadgeAwarder:
    def __init__(self, user_profile):
        self.user_profile = user_profile
        self.user = user_profile.user

    def check_all_badges(self):
        """Check and award all possible badges."""
        self.check_performance_badges()
        self.check_sport_specific_badges()
        self.check_humorous_badges()
        self.check_community_badges()
        self.user_profile.save()

    def check_performance_badges(self):
        """Check and award performance-based badges."""
        from .models import Tip

        # Hot Streak (3 wins) and Blazing Inferno (5 wins)
        recent_tips = Tip.objects.filter(
            user=self.user,
            status__in=['won', 'lost']
        ).order_by('-created_at')[:10]

        current_streak = 0
        for tip in recent_tips:
            if tip.status == 'won':
                current_streak += 1
            else:
                break

        if current_streak >= 3:
            self.user_profile.has_badge_hot_streak = True
        if current_streak >= 5:
            self.user_profile.has_badge_blazing_inferno = True

        # Ice Cold (3 losses)
        current_losing_streak = 0
        for tip in recent_tips:
            if tip.status == 'lost':
                current_losing_streak += 1
            else:
                break
        if current_losing_streak >= 3:
            self.user_profile.has_badge_ice_cold = True

        # Tipster Titan (70%+ win rate over 20 tips)
        total_tips = recent_tips.count()
        if total_tips >= 20:
            wins = recent_tips.filter(status='won').count()
            win_rate = (wins / total_tips) * 100
            if win_rate >= 70:
                self.user_profile.has_badge_tipster_titan = True

        # Rookie Rocket (first win within 24h of joining)
        first_tip = Tip.objects.filter(
            user=self.user,
            status='won',
            created_at__lte=self.user.date_joined + timedelta(days=1)
        ).exists()
        if first_tip:
            self.user_profile.has_badge_rookie_rocket = True

    def check_sport_specific_badges(self):
        """Check and award sport-specific badges."""
        from .models import Tip

        # Soccer Sniper (5 soccer wins in a row)
        soccer_tips = Tip.objects.filter(
            user=self.user,
            sport='football',
            status='won'
        ).order_by('-created_at')[:5]
        if soccer_tips.count() == 5:
            self.user_profile.has_badge_soccer_sniper = True

        # Hole in One (golf tournament winner prediction)
        golf_winner = Tip.objects.filter(
            user=self.user,
            sport='golf',
            status='won',
            bet_type='tournament_winner'
        ).exists()
        if golf_winner:
            self.user_profile.has_badge_hole_in_one = True

    def check_humorous_badges(self):
        """Check and award humorous badges."""
        from .models import Tip

        # Crystal Ball Cracked (5 losses in a row)
        losing_streak = Tip.objects.filter(
            user=self.user,
            status='lost'
        ).order_by('-created_at')[:5].count() == 5
        if losing_streak:
            self.user_profile.has_badge_crystal_ball = True

        # Upset Oracle (win with odds > 5.0)
        upset_win = Tip.objects.filter(
            user=self.user,
            status='won'
        ).filter(
            Q(odds_format='decimal', odds__gt=5.0) |
            Q(odds_format='fractional', odds__in=['4/1', '5/1', '6/1', '7/1', '8/1', '9/1'])
        ).exists()
        if upset_win:
            self.user_profile.has_badge_upset_oracle = True

        # Late Night Gambler (2-4 AM tips)
        late_night = Tip.objects.filter(
            user=self.user,
            created_at__hour__gte=2,
            created_at__hour__lt=4
        ).exists()
        if late_night:
            self.user_profile.has_badge_late_night = True

        # Hail Mary (odds > 10.0)
        hail_mary = Tip.objects.filter(
            user=self.user,
            status='won'
        ).filter(
            Q(odds_format='decimal', odds__gt=10.0) |
            Q(odds_format='fractional', odds__in=['9/1', '10/1', '11/1', '12/1'])
        ).exists()
        if hail_mary:
            self.user_profile.has_badge_hail_mary = True

    def check_community_badges(self):
        """Check and award community engagement badges."""
        from .models import Tip, Comment

        # Crowd Favorite (100+ likes)
        crowd_favorite = Tip.objects.filter(
            user=self.user
        ).annotate(
            like_count=Count('likes')
        ).filter(like_count__gte=100).exists()
        if crowd_favorite:
            self.user_profile.has_badge_crowd_favorite = True

        # Tipster Mentor (10+ helpful comments)
        mentor_comments = Comment.objects.filter(
            user=self.user
        ).values('tip__user').distinct().count() >= 10
        if mentor_comments:
            self.user_profile.has_badge_tipster_mentor = True

        # Anniversary Ace (1 year active)
        if self.user.date_joined <= timezone.now() - timedelta(days=365):
            self.user_profile.has_badge_anniversary = True

        # Viral Visionary (50+ shares)
        viral_tip = Tip.objects.filter(
            user=self.user
        ).annotate(
            share_count=Count('shares')
        ).filter(share_count__gte=50).exists()
        if viral_tip:
            self.user_profile.has_badge_viral = True

def award_badges(user_profile):
    """
    Main function to check and award badges for a user profile.
    Call this after tips are verified or user stats are updated.
    """
    awarder = BadgeAwarder(user_profile)
    awarder.check_all_badges() 