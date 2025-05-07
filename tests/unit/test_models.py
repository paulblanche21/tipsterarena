"""
Unit tests for Tipster Arena models.
Tests individual model functionality and validation.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from core.models import UserProfile, Tip, Event
from decimal import Decimal

User = get_user_model()

class UserProfileModelTest(TestCase):
    """Test suite for UserProfile model."""
    
    def setUp(self):
        """Set up test data."""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        self.user = User.objects.create_user(**self.user_data)
        self.profile = UserProfile.objects.create(
            user=self.user,
            display_name='Test User',
            bio='Test bio',
            location='Test Location',
            win_rate=Decimal('0.0'),
            total_tips=0,
            total_wins=0,
            total_losses=0,
            total_voids=0
        )

    def test_profile_creation(self):
        """Test that a profile is created correctly."""
        self.assertEqual(self.profile.user.username, 'testuser')
        self.assertEqual(self.profile.display_name, 'Test User')
        self.assertEqual(self.profile.win_rate, Decimal('0.0'))

    def test_win_rate_calculation(self):
        """Test win rate calculation."""
        self.profile.total_tips = 10
        self.profile.total_wins = 5
        self.profile.save()
        self.assertEqual(self.profile.win_rate, Decimal('0.5'))

class TipModelTest(TestCase):
    """Test suite for Tip model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='tipster',
            email='tipster@example.com',
            password='testpass123'
        )
        self.event = Event.objects.create(
            name='Test Event',
            start_time=timezone.now(),
            status='upcoming'
        )
        self.tip = Tip.objects.create(
            user=self.user,
            event=self.event,
            prediction='Test prediction',
            odds=Decimal('2.0'),
            stake=Decimal('10.0')
        )

    def test_tip_creation(self):
        """Test that a tip is created correctly."""
        self.assertEqual(self.tip.user.username, 'tipster')
        self.assertEqual(self.tip.event.name, 'Test Event')
        self.assertEqual(self.tip.odds, Decimal('2.0'))

    def test_tip_validation(self):
        """Test tip validation rules."""
        # Test negative stake
        with self.assertRaises(ValidationError):
            Tip.objects.create(
                user=self.user,
                event=self.event,
                prediction='Test prediction',
                odds=Decimal('2.0'),
                stake=Decimal('-10.0')
            )

        # Test invalid odds
        with self.assertRaises(ValidationError):
            Tip.objects.create(
                user=self.user,
                event=self.event,
                prediction='Test prediction',
                odds=Decimal('0.5'),  # Odds should be >= 1.0
                stake=Decimal('10.0')
            ) 