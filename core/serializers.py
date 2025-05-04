from rest_framework import serializers
from .models import GolfTour, GolfCourse, GolfPlayer, GolfEvent, LeaderboardEntry
from .models import FootballLeague, FootballTeam, TeamStats, KeyEvent, BettingOdds, DetailedStats, FootballEvent
from .models import TennisLeague, TennisTournament, TennisPlayer, TennisVenue, TennisEvent, TennisBettingOdds
from .models import HorseRacingMeeting, HorseRacingRace, HorseRacingResult, Horse, Trainer, Jockey
from .models import HorseRacingCourse, HorseRacingBettingOdds, RaceRunner
from rest_framework.serializers import ModelSerializer

class GolfTourSerializer(serializers.ModelSerializer):
    class Meta:
        model = GolfTour
        fields = ['tour_id', 'name', 'icon', 'priority']

class GolfCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = GolfCourse
        fields = ['name', 'par', 'yardage']

class GolfPlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = GolfPlayer
        fields = ['name', 'world_ranking']

class LeaderboardEntrySerializer(serializers.ModelSerializer):
    player = GolfPlayerSerializer(read_only=True)
    rounds = serializers.JSONField()

    class Meta:
        model = LeaderboardEntry
        fields = ['position', 'player', 'score', 'rounds', 'strokes', 'status']
        depth = 1  # This ensures the player relationship is properly serialized

class GolfEventSerializer(serializers.ModelSerializer):
    tour = GolfTourSerializer()
    course = GolfCourseSerializer()
    leaderboard = LeaderboardEntrySerializer(many=True, read_only=True)

    class Meta:
        model = GolfEvent
        fields = [
            'event_id', 'name', 'short_name', 'date', 'state', 'completed', 'venue', 'city', 'state_location',
            'tour', 'course', 'purse', 'broadcast', 'current_round', 'total_rounds', 'is_playoff',
            'weather_condition', 'weather_temperature', 'leaderboard'
        ]
        depth = 2  # This ensures nested relationships are properly serialized
        
# Serializers for FootballEvent and related models
class FootballLeagueSerializer(ModelSerializer):
    class Meta:
        model = FootballLeague
        fields = ['league_id', 'name', 'icon', 'priority']

class FootballTeamSerializer(ModelSerializer):
    class Meta:
        model = FootballTeam
        fields = ['name', 'logo', 'form', 'record']

class TeamStatsSerializer(ModelSerializer):
    class Meta:
        model = TeamStats
        fields = ['possession', 'shots', 'shots_on_target', 'corners', 'fouls']

class KeyEventSerializer(ModelSerializer):
    class Meta:
        model = KeyEvent
        fields = ['type', 'time', 'team', 'player', 'assist', 'is_goal', 'is_yellow_card', 'is_red_card']

class BettingOddsSerializer(ModelSerializer):
    class Meta:
        model = BettingOdds
        fields = ['home_odds', 'away_odds', 'draw_odds', 'provider']

class DetailedStatsSerializer(ModelSerializer):
    class Meta:
        model = DetailedStats
        fields = ['possession', 'home_shots', 'away_shots', 'goals']

class FootballEventSerializer(ModelSerializer):
    league = FootballLeagueSerializer()
    home_team = FootballTeamSerializer()
    away_team = FootballTeamSerializer()
    home_stats = TeamStatsSerializer()
    away_stats = TeamStatsSerializer()
    key_events = KeyEventSerializer(many=True)
    odds = BettingOddsSerializer(many=True)
    detailed_stats = DetailedStatsSerializer(many=True)

    class Meta:
        model = FootballEvent
        fields = [
            'event_id', 'name', 'date', 'state', 'status_description', 'status_detail', 'league', 'venue',
            'home_team', 'away_team', 'home_score', 'away_score', 'home_stats', 'away_stats', 'clock',
            'period', 'broadcast', 'key_events', 'odds', 'detailed_stats'
        ]

class TennisLeagueSerializer(ModelSerializer):
    class Meta:
        model = TennisLeague
        fields = ['league_id', 'name', 'icon', 'priority']

class TennisTournamentSerializer(ModelSerializer):
    league = TennisLeagueSerializer()
    
    class Meta:
        model = TennisTournament
        fields = ['tournament_id', 'name', 'league', 'start_date', 'end_date']

class TennisPlayerSerializer(ModelSerializer):
    class Meta:
        model = TennisPlayer
        fields = ['name', 'short_name', 'world_ranking']

class TennisVenueSerializer(ModelSerializer):
    class Meta:
        model = TennisVenue
        fields = ['name', 'court']

class TennisBettingOddsSerializer(ModelSerializer):
    class Meta:
        model = TennisBettingOdds
        fields = ['player1_odds', 'player2_odds', 'provider']

class TennisEventSerializer(ModelSerializer):
    tournament = TennisTournamentSerializer()
    player1 = TennisPlayerSerializer()
    player2 = TennisPlayerSerializer()
    venue = TennisVenueSerializer()
    odds = TennisBettingOddsSerializer(many=True)

    class Meta:
        model = TennisEvent
        fields = [
            'event_id', 'tournament', 'date', 'state', 'completed',
            'player1', 'player2', 'score', 'sets', 'stats', 'clock',
            'period', 'round_name', 'venue', 'match_type',
            'player1_rank', 'player2_rank', 'odds'
        ]

class HorseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Horse
        fields = ['name', 'age', 'sex', 'colour', 'region']

class TrainerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trainer
        fields = ['name', 'location']

class JockeySerializer(serializers.ModelSerializer):
    class Meta:
        model = Jockey
        fields = ['name']

class HorseRacingResultSerializer(serializers.ModelSerializer):
    horse = HorseSerializer()
    trainer = TrainerSerializer()
    jockey = JockeySerializer()

    class Meta:
        model = HorseRacingResult
        fields = [
            'position', 'horse', 'trainer', 'jockey', 'time', 'prize',
            'official_rating', 'rpr', 'comment'
        ]

class HorseRacingRaceSerializer(serializers.ModelSerializer):
    results = HorseRacingResultSerializer(many=True, read_only=True)

    class Meta:
        model = HorseRacingRace
        fields = [
            'race_id', 'off_time', 'name', 'distance_round', 'distance',
            'pattern', 'race_class', 'type', 'age_band', 'rating_band',
            'prize', 'field_size', 'going', 'rail_movements', 'stalls',
            'weather', 'surface', 'results'
        ]

class HorseRacingMeetingSerializer(serializers.ModelSerializer):
    races = HorseRacingRaceSerializer(many=True, read_only=True)

    class Meta:
        model = HorseRacingMeeting
        fields = ['id', 'date', 'course', 'races']

class HorseRacingCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = HorseRacingCourse
        fields = ['name', 'location', 'track_type', 'surface']

class HorseRacingBettingOddsSerializer(serializers.ModelSerializer):
    class Meta:
        model = HorseRacingBettingOdds
        fields = ['runner', 'bookmaker', 'odds', 'created_at', 'updated_at']

class RaceRunnerSerializer(serializers.ModelSerializer):
    horse = HorseSerializer()
    trainer = TrainerSerializer()
    jockey = JockeySerializer()

    class Meta:
        model = RaceRunner
        fields = ['horse', 'trainer', 'jockey', 'weight', 'number', 'draw']