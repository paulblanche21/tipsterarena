"""
Unit tests for Tipster Arena badge system.
Tests badge award logic and conditions.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import UserProfile, Tip, Event
from core.badges import (
    BadgeAwarder,
    WinStreakBadge,
    TipCountBadge,
    AccuracyBadge
)

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
        self.profile = UserProfile.objects.create(
            user=self.user,
            display_name='Test User'
        )
        self.event = Event.objects.create(
            name='Test Event',
            start_time='2024-01-01 12:00:00',
            status='upcoming'
        )
        self.badge_awarder = BadgeAwarder()

    def test_win_streak_badge(self):
        """Test win streak badge award."""
        # Create 5 winning tips in a row
        for i in range(5):
            Tip.objects.create(
                user=self.user,
                event=self.event,
                prediction=f'Test prediction {i}',
                odds='2.0',
                stake='10.0',
                status='win'
            )
        
        self.badge_awarder.check_win_streak(self.profile)
        self.profile.refresh_from_db()
        
        self.assertIn('win_streak_5', self.profile.badges)

    def test_tip_count_badge(self):
        """Test tip count badge award."""
        # Create 50 tips
        for i in range(50):
            Tip.objects.create(
                user=self.user,
                event=self.event,
                prediction=f'Test prediction {i}',
                odds='2.0',
                stake='10.0'
            )
        
        self.badge_awarder.check_tip_count(self.profile)
        self.profile.refresh_from_db()
        
        self.assertIn('tip_count_50', self.profile.badges)

    def test_accuracy_badge(self):
        """Test accuracy badge award."""
        # Create 20 tips with 15 wins (75% accuracy)
        for i in range(20):
            Tip.objects.create(
                user=self.user,
                event=self.event,
                prediction=f'Test prediction {i}',
                odds='2.0',
                stake='10.0',
                status='win' if i < 15 else 'loss'
            )
        
        self.badge_awarder.check_accuracy(self.profile)
        self.profile.refresh_from_db()
        
        self.assertIn('accuracy_75', self.profile.badges)

    def test_multiple_badges(self):
        """Test multiple badge awards."""
        # Create tips that should trigger multiple badges
        for i in range(50):
            Tip.objects.create(
                user=self.user,
                event=self.event,
                prediction=f'Test prediction {i}',
                odds='2.0',
                stake='10.0',
                status='win' if i < 40 else 'loss'  # 80% accuracy
            )
        
        self.badge_awarder.check_all_badges(self.profile)
        self.profile.refresh_from_db()
        
        self.assertIn('tip_count_50', self.profile.badges)
        self.assertIn('accuracy_80', self.profile.badges)

    def test_badge_progression(self):
        """Test badge progression."""
        # Test progression from bronze to silver to gold
        for i in range(100):
            Tip.objects.create(
                user=self.user,
                event=self.event,
                prediction=f'Test prediction {i}',
                odds='2.0',
                stake='10.0',
                status='win' if i < 80 else 'loss'  # 80% accuracy
            )
        
        self.badge_awarder.check_all_badges(self.profile)
        self.profile.refresh_from_db()
        
        self.assertIn('tip_count_bronze', self.profile.badges)
        self.assertIn('tip_count_silver', self.profile.badges)
        self.assertIn('tip_count_gold', self.profile.badges) 