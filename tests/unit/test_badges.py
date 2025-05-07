"""
Unit tests for Tipster Arena badge system.
Tests badge award logic and conditions.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from core.models import UserProfile, Tip
from core.badges import BadgeAwarder

User = get_user_model()

class BadgeSystemTest(TestCase):
    """Test suite for badge system."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.get(user=self.user)
        self.badge_awarder = BadgeAwarder(self.profile)

    def test_hot_streak_badge(self):
        """Test hot streak badge award."""
        # Create 3 winning tips in a row
        for i in range(3):
            Tip.objects.create(
                user=self.user,
                sport='football',
                text=f'Test tip {i}',
                odds='2.0',
                odds_format='decimal',
                bet_type='single',
                status='won'
            )
        
        self.badge_awarder.check_performance_badges()
        self.profile.refresh_from_db()
        
        self.assertTrue(self.profile.has_badge_hot_streak)

    def test_tipster_titan_badge(self):
        """Test tipster titan badge award."""
        # Create 20 tips with 15 wins (75% win rate)
        for i in range(20):
            Tip.objects.create(
                user=self.user,
                sport='football',
                text=f'Test tip {i}',
                odds='2.0',
                odds_format='decimal',
                bet_type='single',
                status='won' if i < 15 else 'lost'
            )
        
        self.badge_awarder.check_performance_badges()
        self.profile.refresh_from_db()
        
        self.assertTrue(self.profile.has_badge_tipster_titan)

    def test_soccer_sniper_badge(self):
        """Test soccer sniper badge award."""
        # Create 5 winning football tips
        for i in range(5):
            Tip.objects.create(
                user=self.user,
                sport='football',
                text=f'Test tip {i}',
                odds='2.0',
                odds_format='decimal',
                bet_type='single',
                status='won'
            )
        
        self.badge_awarder.check_sport_specific_badges()
        self.profile.refresh_from_db()
        
        self.assertTrue(self.profile.has_badge_soccer_sniper)

    def test_upset_oracle_badge(self):
        """Test upset oracle badge award."""
        # Create a winning tip with high odds
        Tip.objects.create(
            user=self.user,
            sport='football',
            text='High odds tip',
            odds='6.0',
            odds_format='decimal',
            bet_type='single',
            status='won'
        )
        
        self.badge_awarder.check_humorous_badges()
        self.profile.refresh_from_db()
        
        self.assertTrue(self.profile.has_badge_upset_oracle)

    def test_anniversary_badge(self):
        """Test anniversary badge award."""
        # Set user join date to over a year ago
        self.user.date_joined = timezone.now() - timedelta(days=366)
        self.user.save()
        
        self.badge_awarder.check_community_badges()
        self.profile.refresh_from_db()
        
        self.assertTrue(self.profile.has_badge_anniversary) 