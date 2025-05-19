from django.core.management.base import BaseCommand
from core.models import FootballEvent, FootballLeague, FootballTeam
from core.views import fetch_and_store_football_events

class Command(BaseCommand):
    help = 'Debug database state and fetch events'

    def handle(self, *args, **options):
        # Debug football events
        self.stdout.write('Debugging football events...')
        football_events = FootballEvent.objects.all()
        self.stdout.write(f'Found {football_events.count()} football events')
        
        # Debug football leagues
        leagues = FootballLeague.objects.all()
        self.stdout.write(f'Found {leagues.count()} football leagues')
        
        # Debug football teams
        teams = FootballTeam.objects.all()
        self.stdout.write(f'Found {teams.count()} football teams')
        
        # Fetch new football events
        self.stdout.write('Fetching new football events...')
        fetch_and_store_football_events()
        
        self.stdout.write(self.style.SUCCESS('Debug complete'))