from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
import pytz
from core.models import GolfEvent, GolfTour, GolfCourse, LeaderboardEntry
from core.views import fetch_and_store_golf_events

class Command(BaseCommand):
    help = 'Debug and fix GolfEvent data for Tipster Arena'

    def handle(self, *args, **options):
        self.check_golf_events()
        self.fix_event_states_and_dates()
        self.add_test_golf_event()
        self.fetch_espn_data()
        self.check_golf_events()

    def check_golf_events(self):
        self.stdout.write("=== Checking Golf Events ===")
        total_events = GolfEvent.objects.all().count()
        self.stdout.write(f"Total Golf Events: {total_events}")

        events = GolfEvent.objects.all().values('event_id', 'name', 'state', 'date', 'tour__tour_id')
        self.stdout.write("\nGolf Events Details:")
        for event in events:
            self.stdout.write(str(event))

        self.stdout.write("\nEvents by State:")
        for state in ['pre', 'in', 'post', 'unknown']:
            count = GolfEvent.objects.filter(state=state).count()
            self.stdout.write(f"State '{state}': {count} events")

        self.stdout.write("\nGolf Tours:")
        tours = GolfTour.objects.all().values('tour_id', 'name', 'icon', 'priority')
        for tour in tours:
            self.stdout.write(str(tour))

    def fix_event_states_and_dates(self):
        self.stdout.write("\n=== Fixing Golf Events ===")
        future_date = datetime(2025, 4, 28, tzinfo=pytz.UTC)
        for event in GolfEvent.objects.all():
            # Clear existing leaderboards to avoid unique constraint errors
            LeaderboardEntry.objects.filter(event=event).delete()
            event.state = 'pre'
            event.date = future_date
            event.completed = False
            event.save()
            self.stdout.write(f"Updated event {event.event_id}: state={event.state}, date={event.date}")

    def add_test_golf_event(self):
        self.stdout.write("\n=== Adding Test Golf Event ===")
        try:
            tour, created = GolfTour.objects.get_or_create(
                tour_id='pga',
                defaults={'name': 'PGA Tour', 'icon': '🏌️‍♂️', 'priority': 1}
            )
            course, created = GolfCourse.objects.get_or_create(
                name='Test Course',
                defaults={'par': '72', 'yardage': '7000'}
            )
            event, created = GolfEvent.objects.get_or_create(
                event_id='test1',
                defaults={
                    'name': 'Test PGA Event',
                    'short_name': 'Test Event',
                    'date': datetime(2025, 4, 28, tzinfo=pytz.UTC),
                    'state': 'pre',
                    'completed': False,
                    'venue': 'Test Venue',
                    'city': 'Test City',
                    'state_location': 'CA',
                    'tour': tour,
                    'course': course,
                    'purse': '$10,000,000',
                    'broadcast': 'ESPN',
                    'current_round': 1,
                    'total_rounds': 4,
                    'is_playoff': False,
                    'weather_condition': 'Sunny',
                    'weather_temperature': '75°F',
                    'last_updated': timezone.now()
                }
            )
            if created:
                self.stdout.write("Created Test Golf Event")
            else:
                LeaderboardEntry.objects.filter(event=event).delete()
                event.state = 'pre'
                event.date = datetime(2025, 4, 28, tzinfo=pytz.UTC)
                event.completed = False
                event.save()
                self.stdout.write("Updated Test Golf Event")
        except Exception as e:
            self.stdout.write(f"Error adding test event: {str(e)}")

    def fetch_espn_data(self):
        self.stdout.write("\n=== Fetching ESPN Golf Events ===")
        try:
            # Clear all leaderboards to avoid unique constraint errors
            LeaderboardEntry.objects.all().delete()
            fetch_and_store_golf_events()
            self.stdout.write("Fetch completed")
        except Exception as e:
            self.stdout.write(f"Error fetching ESPN data: {str(e)}")