from rest_framework import serializers
from .models import GolfTour, GolfCourse, GolfPlayer, GolfEvent, LeaderboardEntry
from .models import FootballLeague, FootballTeam, TeamStats, KeyEvent, BettingOdds, DetailedStats, FootballEvent
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
        fields = ['type', 'time', 'team', 'player', 'is_goal', 'is_yellow_card', 'is_red_card']

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