from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from django.utils import timezone

from core.factories import (
    UserFactory, GolfEventFactory, FootballEventFactory,
    TennisEventFactory, HorseRacingMeetingFactory,
    GolfTourFactory,
    HorseRacingRaceFactory,
    NotificationFactory
)

class BaseAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(user=self.user)

class GolfAPITest(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.tour = GolfTourFactory()
        self.golf_event = GolfEventFactory(tour=self.tour)
        self.list_url = reverse('golf-events-list')
        self.detail_url = reverse('golf-event-detail', args=[self.golf_event.event_id])

    def test_list_golf_events(self):
        """Test retrieving a list of golf events"""
        # Create additional events with different states
        pre_event = GolfEventFactory(state='pre', tour=self.tour)
        in_progress = GolfEventFactory(state='in', tour=self.tour)
        completed = GolfEventFactory(state='post', tour=self.tour)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)  # Including the one from setUp
        
        # Verify all events are present
        event_ids = [event['event_id'] for event in response.data]
        self.assertIn(pre_event.event_id, event_ids)
        self.assertIn(in_progress.event_id, event_ids)
        self.assertIn(completed.event_id, event_ids)

    def test_golf_event_detail(self):
        """Test retrieving a single golf event"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['event_id'], self.golf_event.event_id)
        self.assertEqual(response.data['tour']['tour_id'], self.tour.tour_id)

    def test_golf_event_filtering(self):
        """Test filtering golf events by state and tour"""
        # Create events with different states
        pre_event = GolfEventFactory(state='pre', tour=self.tour)
        in_progress = GolfEventFactory(state='in', tour=self.tour)
        completed = GolfEventFactory(state='post', tour=self.tour)

        # Test state filtering
        response = self.client.get(f"{self.list_url}?state=pre")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Including the one from setUp
        
        # Verify correct events are returned
        event_ids = [event['event_id'] for event in response.data]
        self.assertIn(pre_event.event_id, event_ids)
        self.assertNotIn(in_progress.event_id, event_ids)
        self.assertNotIn(completed.event_id, event_ids)

        # Test tour filtering
        response = self.client.get(f"{self.list_url}?tour_id={self.tour.tour_id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)
        for event in response.data:
            self.assertEqual(event['tour']['tour_id'], self.tour.tour_id)

class FootballAPITest(BaseAPITest):
    """Test suite for football API endpoints."""
    def setUp(self):
        super().setUp()
        self.football_event = FootballEventFactory()
        self.list_url = reverse('football-events-list')
        self.detail_url = reverse('football-event-detail', args=[self.football_event.event_id])

    def test_list_football_events(self):
        """Test retrieving a list of football events"""
        # Create additional events
        FootballEventFactory(state='pre')
        FootballEventFactory(state='in')
        FootballEventFactory(state='post')

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_football_event_detail(self):
        """Test retrieving a single football event"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['event_id'], self.football_event.event_id)
        self.assertIn('home_team', response.data)
        self.assertIn('away_team', response.data)
        self.assertIn('home_stats', response.data)
        self.assertIn('away_stats', response.data)

    def test_football_event_filtering(self):
        """Test filtering football events by category"""
        # Create events for different categories
        now = timezone.now()
        
        # Fixture (future event)
        future_event = FootballEventFactory(
            state='pre',
            date=now + timedelta(days=1)
        )
        
        # In-play event
        inplay_event = FootballEventFactory(
            state='in',
            date=now
        )
        
        # Result (past event)
        past_event = FootballEventFactory(
            state='post',
            date=now - timedelta(days=1)
        )

        # Test fixtures filter
        response = self.client.get(f"{self.list_url}?category=fixtures")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        event_ids = [e['event_id'] for e in response.data]
        self.assertIn(future_event.event_id, event_ids)
        self.assertNotIn(inplay_event.event_id, event_ids)
        self.assertNotIn(past_event.event_id, event_ids)
        
        # Test in-play filter
        response = self.client.get(f"{self.list_url}?category=inplay")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        event_ids = [e['event_id'] for e in response.data]
        self.assertIn(inplay_event.event_id, event_ids)
        self.assertNotIn(future_event.event_id, event_ids)
        self.assertNotIn(past_event.event_id, event_ids)
        
        # Test results filter
        response = self.client.get(f"{self.list_url}?category=results")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        event_ids = [e['event_id'] for e in response.data]
        self.assertIn(past_event.event_id, event_ids)
        self.assertNotIn(future_event.event_id, event_ids)
        self.assertNotIn(inplay_event.event_id, event_ids)

class TennisAPITest(BaseAPITest):
    """Test suite for tennis API endpoints."""
    def setUp(self):
        super().setUp()
        self.tennis_event = TennisEventFactory()
        self.list_url = reverse('tennis-events-list')
        self.detail_url = reverse('tennis-event-detail', args=[self.tennis_event.event_id])

    def test_list_tennis_events(self):
        """Test retrieving a list of tennis events"""
        # Create additional events
        TennisEventFactory(state='pre')
        TennisEventFactory(state='in')
        TennisEventFactory(state='post')

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_tennis_event_detail(self):
        """Test retrieving a single tennis event"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['event_id'], self.tennis_event.event_id)
        self.assertIn('player1', response.data)
        self.assertIn('player2', response.data)
        self.assertIn('tournament', response.data)

    def test_tennis_event_stats(self):
        """Test retrieving tennis event statistics"""
        # Add some stats to the event
        self.tennis_event.stats = {
            'sets': [
                {'player1': 6, 'player2': 4},
                {'player1': 7, 'player2': 6}
            ],
            'serve_stats': {
                'player1': {'aces': 10, 'double_faults': 2},
                'player2': {'aces': 8, 'double_faults': 3}
            }
        }
        self.tennis_event.save()

        stats_url = reverse('tennis-event-stats', args=[self.tennis_event.event_id])
        response = self.client.get(stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('sets', response.data)
        self.assertIn('serve_stats', response.data)

    def test_tennis_event_filtering(self):
        """Test filtering tennis events by category and tournament"""
        now = timezone.now()
        
        # Create events for different categories
        future_event = TennisEventFactory(
            state='pre',
            date=now + timedelta(days=1)
        )
        inplay_event = TennisEventFactory(
            state='in',
            date=now
        )
        past_event = TennisEventFactory(
            state='post',
            date=now - timedelta(days=1)
        )

        # Test category filters
        category_event_map = {
            'fixtures': future_event,
            'inplay': inplay_event,
            'results': past_event
        }
        
        for category, expected_event in category_event_map.items():
            response = self.client.get(f"{self.list_url}?category={category}")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            event_ids = [e['event_id'] for e in response.data]
            self.assertIn(expected_event.event_id, event_ids)

class HorseRacingAPITest(BaseAPITest):
    """Test suite for horse racing API endpoints."""
    def setUp(self):
        super().setUp()
        self.meeting = HorseRacingMeetingFactory()
        self.race = HorseRacingRaceFactory(meeting=self.meeting)
        self.list_url = reverse('horse-racing-events')

    def test_list_meetings(self):
        """Test retrieving a list of horse racing meetings"""
        # Create additional meetings
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)
        
        today_meeting = HorseRacingMeetingFactory(date=today)
        tomorrow_meeting = HorseRacingMeetingFactory(date=tomorrow)

        response = self.client.get(f"{self.list_url}?category=upcoming_meetings")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 2)  # Should include today and tomorrow's meetings
        
        # Verify the meetings are present in the response
        meeting_ids = [m['id'] for m in response.data]
        self.assertIn(today_meeting.id, meeting_ids)
        self.assertIn(tomorrow_meeting.id, meeting_ids)

    def test_race_results(self):
        """Test retrieving race results"""
        # Create past races with results
        past_date = timezone.now().date() - timedelta(days=1)
        past_meeting = HorseRacingMeetingFactory(date=past_date)
        past_race = HorseRacingRaceFactory(meeting=past_meeting)

        response = self.client.get(f"{self.list_url}?category=race_results")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        
        # Verify the past race is in the response
        race_ids = [race['race_id'] for race in response.data]
        self.assertIn(past_race.race_id, race_ids)

    def test_at_the_post(self):
        """Test retrieving races at the post"""
        # Create races with different off times
        now = timezone.now()
        
        # Create a race starting in 15 minutes
        upcoming_race = HorseRacingRaceFactory(
            meeting=self.meeting,
            off_time=(now + timedelta(minutes=15)).time().strftime('%H:%M')
        )

        response = self.client.get(f"{self.list_url}?category=at_the_post")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the upcoming race is in the response
        race_ids = [race['race_id'] for race in response.data]
        self.assertIn(upcoming_race.race_id, race_ids)

    def test_invalid_category(self):
        """Test requesting an invalid category"""
        response = self.client.get(f"{self.list_url}?category=invalid")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class APIAuthenticationTest(TestCase):
    """Test suite for API authentication functionality."""
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.admin_user = UserFactory(is_staff=True)
        self.golf_event = GolfEventFactory()
        self.football_event = FootballEventFactory()
        self.tennis_event = TennisEventFactory()
        self.horse_racing_meeting = HorseRacingMeetingFactory()
        self.notification = NotificationFactory(user=self.user)

    def test_public_endpoints(self):
        """Test public API endpoints that don't require authentication"""
        urls = [
            reverse('golf-events-list'),
            reverse('football_events'),
            reverse('tennis-events-list'),
            reverse('horse-racing-events')
        ]
        
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_endpoints(self):
        """Test API endpoints that require authentication"""
        self.client.force_authenticate(user=self.user)
        
        # Test GET endpoints
        get_urls = [
            reverse('tip-list'),
            reverse('get_notifications')
        ]
        
        for url in get_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test POST endpoints
        response = self.client.post(
            reverse('mark_notification_read'),
            {'notification_id': self.notification.id}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(reverse('mark_all_notifications_read'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_access_to_protected_endpoints(self):
        """Test that unauthenticated users cannot access protected endpoints"""
        # Test GET endpoints
        get_urls = [
            reverse('tip-list'),
            reverse('get_notifications')
        ]
        
        for url in get_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test POST endpoints
        response = self.client.post(
            reverse('mark_notification_read'),
            {'notification_id': self.notification.id}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.post(reverse('mark_all_notifications_read'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_endpoints(self):
        """Test API endpoints that require admin privileges"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Test access to admin-only endpoints
        admin_urls = [
            reverse('fetch_golf_events'),
            reverse('fetch_football_events'),
            reverse('verify_tip')
        ]
        
        for url in admin_urls:
            response = self.client.post(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_admin_access_to_admin_endpoints(self):
        """Test that non-admin users cannot access admin endpoints"""
        self.client.force_authenticate(user=self.user)
        
        # Test access to admin-only endpoints
        admin_urls = [
            reverse('fetch_golf_events'),
            reverse('fetch_football_events'),
            reverse('verify_tip')
        ]
        
        for url in admin_urls:
            response = self.client.post(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class APIErrorHandlingTest(TestCase):
    """Test suite for API error handling functionality."""
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory(is_staff=True)
        self.client.force_authenticate(user=self.user)

    def test_invalid_event_id(self):
        """Test handling of invalid event IDs"""
        urls = [
            reverse('golf-event-detail', args=['nonexistent']),
            reverse('football-event-detail', args=['nonexistent']),
            reverse('tennis-event-detail', args=['nonexistent'])
        ]

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_date_filters(self):
        """Test handling of invalid date filters"""
        urls = [
            (reverse('golf-events-list'), {'date': 'invalid-date'}),
            (reverse('football-events-list'), {'date': '2023-13-45'}),
            (reverse('tennis-events-list'), {'date': 'tomorrow'})
        ]
    
        for url, params in urls:
            response = self.client.get(url, params)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_required_fields(self):
        """Test handling of missing required fields"""
        urls = [
            reverse('golf-events-list'),
            reverse('football-events-list'),
            reverse('tennis-events-list')
        ]

        for url in urls:
            response = self.client.post(url, {})
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class APIPaginationTest(TestCase):
    """Test suite for API pagination functionality."""
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory(is_staff=True)
        self.client.force_authenticate(user=self.user)   
        # Create multiple events for pagination testing
        self.golf_events = [GolfEventFactory() for _ in range(15)]
        self.football_events = [FootballEventFactory() for _ in range(15)]
        self.tennis_events = [TennisEventFactory() for _ in range(15)]

    def test_pagination_defaults(self):
        """Test default pagination settings"""
        urls = [
            reverse('golf-events-list'),
            reverse('football-events-list'),
            reverse('tennis-events-list')
        ]

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('results', response.data)
            self.assertIn('count', response.data)
            self.assertIn('next', response.data)
            self.assertIn('previous', response.data)

    def test_custom_page_size(self):
        """Test custom page size parameter"""
        urls = [
            reverse('golf-events-list'),
            reverse('football-events-list'),
            reverse('tennis-events-list')
        ]
 
        for url in urls:
            response = self.client.get(f"{url}?page_size=5")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data['results']), 5)

    def test_invalid_page(self):
        """Test handling of invalid page numbers"""
        urls = [
            reverse('golf-events-list'),
            reverse('football-events-list'),
            reverse('tennis-events-list')
        ]

        for url in urls:
            response = self.client.get(f"{url}?page=999")
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class APIRateLimitTest(TestCase):
    """Test suite for API rate limiting functionality."""
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_rate_limiting(self):
        """Test API rate limiting"""
        url = reverse('golf-events-list')
        
        # Make multiple requests in quick succession
        for _ in range(100):
            response = self.client.get(url)
            
        # The last request should be rate limited
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

class APICachingTest(TestCase):
    """Test suite for API caching functionality."""
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory(is_staff=True)
        self.client.force_authenticate(user=self.user)

    def test_cache_control_headers(self):
        """Test cache control headers in responses"""
        urls = [
            reverse('golf-events-list'),
            reverse('football-events-list'),
            reverse('tennis-events-list')
        ]
        
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('Cache-Control', response['Cache-Control'])

    def test_etag_handling(self):
        """Test ETag handling for caching"""
        url = reverse('golf-events-list')
        
        # First request should return an ETag
        response = self.client.get(url)
        self.assertIn('ETag', response)
        etag = response['ETag']
        
        # Second request with If-None-Match should return 304
        response = self.client.get(url, HTTP_IF_NONE_MATCH=etag)
        self.assertEqual(response.status_code, status.HTTP_304_NOT_MODIFIED) 