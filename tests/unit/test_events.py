"""
Unit tests for Tipster Arena event system.
Tests event creation, validation, and status updates.
"""
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from core.models import Event, Tip
from core.horse_racing_events import (
    HorseRacingEvent,
    EventValidator,
    EventStatusUpdater
)
from datetime import timedelta

User = get_user_model()

class EventSystemTest(TestCase):
    """Test suite for event system."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.validator = EventValidator()
        self.status_updater = EventStatusUpdater()

    def test_event_creation(self):
        """Test event creation."""
        event = HorseRacingEvent.objects.create(
            name='Test Race',
            start_time=timezone.now() + timedelta(days=1),
            status='upcoming',
            venue='Test Venue',
            race_type='flat',
            distance='1200m',
            surface='turf'
        )
        
        self.assertEqual(event.name, 'Test Race')
        self.assertEqual(event.status, 'upcoming')
        self.assertEqual(event.race_type, 'flat')

    def test_event_validation(self):
        """Test event validation."""
        # Test valid event
        valid_event = {
            'name': 'Test Race',
            'start_time': timezone.now() + timedelta(days=1),
            'venue': 'Test Venue',
            'race_type': 'flat',
            'distance': '1200m',
            'surface': 'turf'
        }
        self.assertTrue(self.validator.validate_event(valid_event))

        # Test invalid event (past start time)
        invalid_event = valid_event.copy()
        invalid_event['start_time'] = timezone.now() - timedelta(days=1)
        self.assertFalse(self.validator.validate_event(invalid_event))

    def test_event_status_update(self):
        """Test event status updates."""
        event = HorseRacingEvent.objects.create(
            name='Test Race',
            start_time=timezone.now() + timedelta(hours=1),
            status='upcoming',
            venue='Test Venue',
            race_type='flat',
            distance='1200m',
            surface='turf'
        )
        
        # Update status to in_progress
        self.status_updater.update_status(event, 'in_progress')
        self.assertEqual(event.status, 'in_progress')
        
        # Update status to completed
        self.status_updater.update_status(event, 'completed')
        self.assertEqual(event.status, 'completed')

    def test_event_tips(self):
        """Test event tips association."""
        event = HorseRacingEvent.objects.create(
            name='Test Race',
            start_time=timezone.now() + timedelta(days=1),
            status='upcoming',
            venue='Test Venue',
            race_type='flat',
            distance='1200m',
            surface='turf'
        )
        
        # Create tips for the event
        for i in range(3):
            Tip.objects.create(
                user=self.user,
                event=event,
                prediction=f'Test prediction {i}',
                odds='2.0',
                stake='10.0'
            )
        
        self.assertEqual(event.tips.count(), 3)

    def test_event_results(self):
        """Test event results recording."""
        event = HorseRacingEvent.objects.create(
            name='Test Race',
            start_time=timezone.now() + timedelta(days=1),
            status='upcoming',
            venue='Test Venue',
            race_type='flat',
            distance='1200m',
            surface='turf'
        )
        
        # Record results
        results = {
            'winner': 'Horse A',
            'second': 'Horse B',
            'third': 'Horse C',
            'time': '1:10.5',
            'conditions': 'Good'
        }
        event.record_results(results)
        
        self.assertEqual(event.status, 'completed')
        self.assertEqual(event.results['winner'], 'Horse A')
        self.assertEqual(event.results['time'], '1:10.5') 