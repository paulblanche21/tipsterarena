from django.test import TestCase
from core.serializers import (
    GolfEventSerializer, FootballEventSerializer,
    TennisEventSerializer, HorseRacingMeetingSerializer
)
from core.factories import (
    GolfEventFactory, FootballEventFactory,
    TennisEventFactory, HorseRacingMeetingFactory
)

class GolfEventSerializerTest(TestCase):
    """Test suite for golf event serializer functionality."""
    def setUp(self):
        self.golf_event = GolfEventFactory()
        self.serializer = GolfEventSerializer(instance=self.golf_event)

    def test_contains_expected_fields(self):
        """Test that the serializer contains the expected fields"""
        data = self.serializer.data
        expected_fields = {
            'event_id', 'name', 'short_name', 'date', 'state',
            'completed', 'venue', 'city', 'state_location',
            'tour', 'course', 'purse', 'broadcast',
            'current_round', 'total_rounds', 'is_playoff',
            'weather_condition', 'weather_temperature', 'leaderboard'
        }
        self.assertEqual(set(data.keys()), expected_fields)

    def test_nested_serialization(self):
        """Test that nested objects are properly serialized"""
        data = self.serializer.data
        self.assertIn('tour', data)
        self.assertIn('course', data)
        self.assertIn('leaderboard', data)

class FootballEventSerializerTest(TestCase):
    """Test suite for football event serializer functionality."""
    def setUp(self):
        self.football_event = FootballEventFactory()
        self.serializer = FootballEventSerializer(instance=self.football_event)

    def test_contains_expected_fields(self):
        """Test that the serializer contains the expected fields"""
        data = self.serializer.data
        expected_fields = {
            'event_id', 'name', 'date', 'state',
            'status_description', 'status_detail', 'league',
            'venue', 'home_team', 'away_team', 'home_score',
            'away_score', 'home_stats', 'away_stats', 'clock',
            'period', 'broadcast', 'key_events', 'odds',
            'detailed_stats'
        }
        self.assertEqual(set(data.keys()), expected_fields)

    def test_team_stats_serialization(self):
        """Test that team statistics are properly serialized"""
        data = self.serializer.data
        stats_fields = {'possession', 'shots', 'shots_on_target', 'corners', 'fouls'}
        self.assertEqual(set(data['home_stats'].keys()), stats_fields)
        self.assertEqual(set(data['away_stats'].keys()), stats_fields)

class TennisEventSerializerTest(TestCase):
    """Test suite for tennis event serializer functionality."""
    def setUp(self):
        self.tennis_event = TennisEventFactory()
        self.serializer = TennisEventSerializer(instance=self.tennis_event)

    def test_contains_expected_fields(self):
        """Test that the serializer contains the expected fields"""
        data = self.serializer.data
        expected_fields = {
            'event_id', 'tournament', 'date', 'state',
            'completed', 'player1', 'player2', 'score',
            'sets', 'stats', 'clock', 'period', 'round_name',
            'venue', 'match_type', 'player1_rank', 'player2_rank',
            'odds'
        }
        self.assertEqual(set(data.keys()), expected_fields)

    def test_player_serialization(self):
        """Test that player information is properly serialized"""
        data = self.serializer.data
        player_fields = {'name', 'short_name', 'world_ranking'}
        self.assertEqual(set(data['player1'].keys()), player_fields)
        self.assertEqual(set(data['player2'].keys()), player_fields)

class HorseRacingSerializerTest(TestCase):
    """Test suite for horse racing serializer functionality."""
    def setUp(self):
        self.meeting = HorseRacingMeetingFactory()
        self.serializer = HorseRacingMeetingSerializer(instance=self.meeting)

    def test_contains_expected_fields(self):
        """Test that the serializer contains the expected fields"""
        data = self.serializer.data
        expected_fields = {'date', 'course', 'races'}
        self.assertEqual(set(data.keys()), expected_fields)

    def test_race_serialization(self):
        """Test that races are properly serialized"""
        data = self.serializer.data
        self.assertIn('races', data)
        if data['races']:
            race_fields = {
                'race_id', 'off_time', 'name', 'distance_round',
                'distance', 'pattern', 'race_class', 'type',
                'age_band', 'rating_band', 'prize', 'field_size',
                'going', 'rail_movements', 'stalls', 'weather',
                'surface', 'results'
            }
            self.assertEqual(set(data['races'][0].keys()), race_fields) 