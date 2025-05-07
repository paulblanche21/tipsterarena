"""
Unit tests for Tipster Arena utility functions.
Tests helper functions and utility methods.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import UserProfile, Tip



User = get_user_model()

class WinRateCalculationTest(TestCase):
    """Test suite for win rate calculation."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            display_name='Test User',
            bio='Test bio',
            location='Test Location'
        )

    def test_win_rate_calculation(self):
        """Test win rate calculation."""
        # Create some tips
        for i in range(10):
            Tip.objects.create(
                user=self.user,
                prediction=f'Test prediction {i}',
                odds='2.0',
                odds_format='decimal',
                status='win' if i < 5 else 'loss'
            )
        
        # Refresh profile from db
        self.profile.refresh_from_db()
        
        # Check win rate calculation
        self.assertEqual(self.profile.win_rate, 50.0)  # 5 wins out of 10 tips = 50%

class OddsValidationTest(TestCase):
    """Test suite for odds validation."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_decimal_odds_validation(self):
        """Test decimal odds validation."""
        # Valid decimal odds
        tip = Tip.objects.create(
            user=self.user,
            prediction='Test prediction',
            odds='2.5',
            odds_format='decimal'
        )
        self.assertEqual(tip.odds, '2.5')
        
        # Invalid decimal odds (less than 1.0)
        with self.assertRaises(Exception):
            Tip.objects.create(
                user=self.user,
                prediction='Test prediction',
                odds='0.5',
                odds_format='decimal'
            )

    def test_fractional_odds_validation(self):
        """Test fractional odds validation."""
        # Valid fractional odds
        tip = Tip.objects.create(
            user=self.user,
            prediction='Test prediction',
            odds='2/1',
            odds_format='fractional'
        )
        self.assertEqual(tip.odds, '2/1')
        
        # Invalid fractional odds (zero denominator)
        with self.assertRaises(Exception):
            Tip.objects.create(
                user=self.user,
                prediction='Test prediction',
                odds='2/0',
                odds_format='fractional'
            )

class TipValidationTest(TestCase):
    """Test suite for tip validation."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_tip_validation(self):
        """Test tip validation rules."""
        # Valid tip
        tip = Tip.objects.create(
            user=self.user,
            prediction='Test prediction',
            odds='2.0',
            odds_format='decimal',
            confidence=3  # 3 stars confidence
        )
        self.assertEqual(tip.confidence, 3)
        
        # Invalid confidence (should be 1-5)
        with self.assertRaises(Exception):
            Tip.objects.create(
                user=self.user,
                prediction='Test prediction',
                odds='2.0',
                odds_format='decimal',
                confidence=6  # Invalid confidence level
            ) 