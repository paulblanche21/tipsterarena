from rest_framework import serializers
from core.models import FootballFixture

class FootballFixtureSerializer(serializers.ModelSerializer):
    class Meta:
        model = FootballFixture
        fields = [
            'event_id', 'match_date', 'home_team', 'away_team', 'league',
            'state', 'home_score', 'away_score', 'status_detail', 'odds',
            'key_events', 'last_updated'
        ]