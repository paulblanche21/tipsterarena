"""
Unit tests for Tipster Arena utility functions.
Tests helper functions and utility methods.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import UserProfile, Tip
from django.core.exceptions import ValidationError



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
        # Get the automatically created profile
        self.profile = UserProfile.objects.get(user=self.user)
        self.profile.full_name = 'Test User'
        self.profile.description = 'Test bio'
        self.profile.location = 'Test Location'
        self.profile.save()

    def test_win_rate_calculation(self):
        """Test win rate calculation."""
        # Create some tips
        for i in range(10):
            Tip.objects.create(
                user=self.user,
                text=f'Test prediction {i}',
                sport='football',  # Required field
                odds='2.0',
                odds_format='decimal',
                bet_type='single',  # Required field
                release_schedule={'1': '2025-01-01T00:00:00Z'},  # Required field with valid format
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
        tip = Tip(
            user=self.user,
            text='Test prediction',
            sport='football',  # Required field
            odds='2.5',
            odds_format='decimal',
            bet_type='single',  # Required field
            release_schedule={'1': '2025-01-01T00:00:00Z'}  # Required field with valid format
        )
        tip.full_clean()  # Validate before saving
        tip.save()
        self.assertEqual(tip.odds, '2.5')
        
        # Invalid decimal odds (less than 1.0)
        with self.assertRaises(ValidationError):
            tip = Tip(
                user=self.user,
                text='Test prediction',
                sport='football',  # Required field
                odds='0.5',
                odds_format='decimal',
                bet_type='single',  # Required field
                release_schedule={'1': '2025-01-01T00:00:00Z'}  # Required field with valid format
            )
            tip.full_clean()  # This should raise ValidationError

    def test_fractional_odds_validation(self):
        """Test fractional odds validation."""
        # Valid fractional odds
        tip = Tip(
            user=self.user,
            text='Test prediction',
            sport='football',  # Required field
            odds='2/1',
            odds_format='fractional',
            bet_type='single',  # Required field
            release_schedule={'1': '2025-01-01T00:00:00Z'}  # Required field with valid format
        )
        tip.full_clean()  # Validate before saving
        tip.save()
        self.assertEqual(tip.odds, '2/1')
        
        # Invalid fractional odds (zero denominator)
        with self.assertRaises(ValidationError):
            tip = Tip(
                user=self.user,
                text='Test prediction',
                sport='football',  # Required field
                odds='2/0',
                odds_format='fractional',
                bet_type='single',  # Required field
                release_schedule={'1': '2025-01-01T00:00:00Z'}  # Required field with valid format
            )
            tip.full_clean()  # This should raise ValidationError

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
        tip = Tip(
            user=self.user,
            text='Test prediction',
            sport='football',  # Required field
            odds='2.0',
            odds_format='decimal',
            bet_type='single',  # Required field
            release_schedule={'1': '2025-01-01T00:00:00Z'},  # Required field with valid format
            confidence=3  # 3 stars confidence
        )
        tip.full_clean()  # Validate before saving
        tip.save()
        self.assertEqual(tip.confidence, 3)
        
        # Invalid confidence (should be 1-5)
        with self.assertRaises(ValidationError):
            tip = Tip(
                user=self.user,
                text='Test prediction',
                sport='football',  # Required field
                odds='2.0',
                odds_format='decimal',
                bet_type='single',  # Required field
                release_schedule={'1': '2025-01-01T00:00:00Z'},  # Required field with valid format
                confidence=6  # Invalid confidence level
            )
            tip.full_clean()  # This should raise ValidationError 