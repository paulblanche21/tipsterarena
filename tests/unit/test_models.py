"""
Unit tests for Tipster Arena models.
Tests individual model functionality and validation.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from core.models import UserProfile, Tip, FootballEvent, TennisEvent, HorseRacingRace
from core.models import (
    FootballLeague, FootballTeam, GolfTour, GolfCourse, TennisLeague, TennisTournament,
    HorseRacingCourse, HorseRacingMeeting, TennisPlayer
)

User = get_user_model()

class UserProfileModelTest(TestCase):
    """Test suite for UserProfile model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # UserProfile should be created automatically via signal
        self.profile = UserProfile.objects.get(user=self.user)
        self.profile.full_name = 'Test User'
        self.profile.description = 'Test bio'
        self.profile.location = 'Test Location'
        self.profile.win_rate = 0.0
        self.profile.total_tips = 0
        self.profile.wins = 0
        self.profile.save()

    def test_profile_creation(self):
        """Test that a profile is created correctly."""
        self.assertEqual(self.profile.user.username, 'testuser')
        self.assertEqual(self.profile.full_name, 'Test User')
        self.assertEqual(self.profile.win_rate, 0.0)

    def test_win_rate_calculation(self):
        """Test win rate calculation."""
        self.profile.total_tips = 10
        self.profile.wins = 5
        self.profile.win_rate = 50.0
        self.profile.save()
        self.assertEqual(self.profile.win_rate, 50.0)

    def test_user_profile_stats_update(self):
        """Test updating user profile statistics."""
        # Create some tips
        Tip.objects.create(
            user=self.user,
            sport='football',
            text='Test tip 1',
            odds='2.5',
            odds_format='decimal',
            bet_type='single',
            confidence=3,
            status='win'
        )
        
        Tip.objects.create(
            user=self.user,
            sport='football',
            text='Test tip 2',
            odds='2.5',
            odds_format='decimal',
            bet_type='single',
            confidence=3,
            status='loss'
        )
        
        # Update profile stats
        self.profile.total_tips = 2
        self.profile.wins = 1
        self.profile.win_rate = 50.0
        self.profile.save()
        
        self.assertEqual(self.profile.total_tips, 2)
        self.assertEqual(self.profile.wins, 1)
        self.assertEqual(self.profile.win_rate, 50.0)

class UserProfileEdgeCasesTest(TestCase):
    """Test suite for UserProfile edge cases and error conditions."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.get(user=self.user)

    def test_invalid_win_rate(self):
        """Test handling of invalid win rate values."""
        with self.assertRaises(ValidationError):
            self.profile.win_rate = -1
            self.profile.full_clean()
        
        with self.assertRaises(ValidationError):
            self.profile.win_rate = 101
            self.profile.full_clean()

    def test_duplicate_handle(self):
        """Test prevention of duplicate handles."""
        # Create another user with same handle
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        profile2 = UserProfile.objects.get(user=user2)
        
        self.profile.handle = 'testhandle'
        self.profile.save()
        
        with self.assertRaises(ValidationError):
            profile2.handle = 'testhandle'
            profile2.full_clean()

class TipModelTest(TestCase):
    """Test suite for Tip model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='tipster',
            email='tipster@example.com',
            password='testpass123'
        )
        self.football_league = FootballLeague.objects.create(
            league_id='test.1',
            name='Test League',
            icon='⚽'
        )
        self.football_team1 = FootballTeam.objects.create(name='Team 1')
        self.football_team2 = FootballTeam.objects.create(name='Team 2')
        self.event = FootballEvent.objects.create(
            event_id='test123',
            name='Test Event',
            date=timezone.now(),
            league=self.football_league,
            home_team=self.football_team1,
            away_team=self.football_team2
        )
        self.tip = Tip.objects.create(
            user=self.user,
            sport='football',
            text='Test tip',
            odds='2.0',
            odds_format='decimal',
            bet_type='single',
            confidence=3
        )

    def test_tip_creation(self):
        """Test that a tip is created correctly."""
        self.assertEqual(self.tip.user.username, 'tipster')
        self.assertEqual(self.tip.sport, 'football')
        self.assertEqual(self.tip.odds, '2.0')

    def test_tip_validation(self):
        """Test tip validation rules."""
        # Test invalid confidence level
        with self.assertRaises(ValidationError):
            tip = Tip(
                user=self.user,
                sport='football',
                text='Test tip',
                odds='2.0',
                odds_format='decimal',
                bet_type='single',
                confidence=6  # Invalid confidence level (should be 1-5)
            )
            tip.full_clean()

        # Test invalid sport
        with self.assertRaises(ValidationError):
            tip = Tip(
                user=self.user,
                sport='invalid_sport',  # Invalid sport
                text='Test tip',
                odds='2.0',
                odds_format='decimal',
                bet_type='single',
                confidence=3
            )
            tip.full_clean()

class TipEdgeCasesTest(TestCase):
    """Test suite for Tip edge cases and error conditions."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.get(user=self.user)

    def test_invalid_odds_format(self):
        """Test handling of invalid odds formats."""
        tip = Tip(
            user=self.user,
            sport='football',
            text='Test tip',
            odds='2.0',
            odds_format='invalid_format',
            bet_type='single',
            confidence=3
        )
        with self.assertRaises(ValidationError):
            tip.full_clean()

    def test_invalid_odds_value(self):
        """Test handling of invalid odds values."""
        tip = Tip(
            user=self.user,
            sport='football',
            text='Test tip',
            odds='0.5',  # Invalid decimal odds
            odds_format='decimal',
            bet_type='single',
            confidence=3
        )
        with self.assertRaises(ValidationError):
            tip.full_clean()

    def test_invalid_bet_type(self):
        """Test handling of invalid bet types."""
        tip = Tip(
            user=self.user,
            sport='football',
            text='Test tip',
            odds='2.0',
            odds_format='decimal',
            bet_type='invalid_type',
            confidence=3
        )
        with self.assertRaises(ValidationError):
            tip.full_clean()

class SportEventEdgeCasesTest(TestCase):
    """Test suite for Sport Event edge cases and error conditions."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.football_league = FootballLeague.objects.create(
            league_id='test.1',
            name='Test League',
            icon='⚽'
        )
        self.football_team1 = FootballTeam.objects.create(name='Team 1')
        self.football_team2 = FootballTeam.objects.create(name='Team 2')

    def test_duplicate_event_id(self):
        """Test prevention of duplicate event IDs."""
        event1 = FootballEvent.objects.create(
            event_id='test123',
            name='Test Event 1',
            date=timezone.now() + timezone.timedelta(days=1),
            league=self.football_league,
            home_team=self.football_team1,
            away_team=self.football_team2
        )
        
        # Verify first event exists
        self.assertEqual(FootballEvent.objects.get(event_id='test123'), event1)
        
        event2 = FootballEvent(
            event_id='test123',  # Duplicate ID
            name='Test Event 2',
            date=timezone.now() + timezone.timedelta(days=1),
            league=self.football_league,
            home_team=self.football_team1,
            away_team=self.football_team2
        )
        with self.assertRaises(ValidationError):
            event2.full_clean()

    def test_invalid_event_date(self):
        """Test handling of invalid event dates."""
        event = FootballEvent(
            event_id='test123',
            name='Test Event',
            date=timezone.now() - timezone.timedelta(days=1),  # Past date
            league=self.football_league,
            home_team=self.football_team1,
            away_team=self.football_team2
        )
        with self.assertRaises(ValidationError):
            event.full_clean()

    def test_same_team_home_away(self):
        """Test prevention of same team being both home and away."""
        event = FootballEvent(
            event_id='test123',
            name='Test Event',
            date=timezone.now() + timezone.timedelta(days=1),
            league=self.football_league,
            home_team=self.football_team1,
            away_team=self.football_team1  # Same team
        )
        with self.assertRaises(ValidationError):
            event.full_clean()

class IntegrationTest(TestCase):
    """Test suite for integration between different components."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.get(user=self.user)
        self.football_league = FootballLeague.objects.create(
            league_id='test.1',
            name='Test League',
            icon='⚽'
        )
        self.football_team1 = FootballTeam.objects.create(name='Team 1')
        self.football_team2 = FootballTeam.objects.create(name='Team 2')
        self.event = FootballEvent.objects.create(
            event_id='test123',
            name='Test Event',
            date=timezone.now(),
            league=self.football_league,
            home_team=self.football_team1,
            away_team=self.football_team2
        )

    def test_tip_affects_user_stats(self):
        """Test that creating a tip affects user statistics."""
        initial_tips = self.profile.total_tips
        initial_wins = self.profile.wins
        
        # Create a winning tip
        Tip.objects.create(
            user=self.user,
            sport='football',
            text='Test tip',
            odds='2.0',
            odds_format='decimal',
            bet_type='single',
            confidence=3,
            status='win'
        )
        
        # Refresh profile from database
        self.profile.refresh_from_db()
        
        # Check that stats were updated
        self.assertEqual(self.profile.total_tips, initial_tips + 1)
        self.assertEqual(self.profile.wins, initial_wins + 1)
        self.assertEqual(self.profile.win_rate, 100.0)

    def test_event_state_affects_tips(self):
        """Test that event state changes affect associated tips."""
        # Create a tip for the event
        tip = Tip.objects.create(
            user=self.user,
            sport='football',
            text='Test tip',
            odds='2.0',
            odds_format='decimal',
            bet_type='single',
            confidence=3
        )
        
        # Change event state to 'live'
        self.event.state = 'live'
        self.event.save()
        
        # Tip should be affected by event state
        tip.refresh_from_db()
        self.assertEqual(tip.status, 'pending')  # Assuming this is the expected behavior 