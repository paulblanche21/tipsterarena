from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import GolfTour, GolfCourse, GolfPlayer, GolfEvent, LeaderboardEntry
import requests
import logging
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

# Configuration for golf tours
GOLF_TOURS = [
    {"tour_id": "pga", "name": "PGA Tour", "icon": "🏌️‍♂️", "priority": 1},
    {"tour_id": "lpga", "name": "LPGA Tour", "icon": "🏌️‍♀️", "priority": 2},
]

class Command(BaseCommand):
    help = 'Fetches golf events from ESPN API and populates the database'

    def handle(self, *args, **kwargs):
        verbosity = kwargs.get('verbosity', 1)
        if verbosity > 1:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        self.stdout.write('Starting golf data population...')
        
        # Calculate date range for events
        today = timezone.now().date()
        start_date = today - timezone.timedelta(days=7)  # Get events from 7 days ago
        end_date = today + timezone.timedelta(days=30)   # Get events up to 30 days in future
        date_range = f"{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}"
        
        for tour_config in GOLF_TOURS:
            try:
                # Fetch events for this tour
                url = f"https://site.api.espn.com/apis/site/v2/sports/golf/{tour_config['tour_id']}/scoreboard"
                params = {
                    'dates': date_range,
                    'limit': 100  # Request more events
                }
                self.stdout.write(f"Fetching events for {tour_config['name']} from {start_date} to {end_date}...")
                
                response = requests.get(url, params=params)
                response.raise_for_status()  # Raise exception for bad status codes
                data = response.json()

                # Get or create the tour
                tour, _ = GolfTour.objects.get_or_create(
                    tour_id=tour_config['tour_id'],
                    defaults={
                        'name': tour_config['name'],
                        'icon': tour_config['icon'],
                        'priority': tour_config['priority']
                    }
                )

                # Process each event
                events = data.get('events', [])
                if not events:
                    self.stdout.write(self.style.WARNING(f"No events found for {tour_config['name']}"))
                    continue

                self.stdout.write(f"Found {len(events)} events for {tour_config['name']}")
                for event in events:
                    try:
                        self.process_event(event, tour)
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error processing event {event.get('name', 'Unknown')}: {str(e)}"))
                        logger.exception("Error processing event")
                        continue

            except requests.RequestException as e:
                self.stdout.write(self.style.ERROR(f"Error fetching data for {tour_config['name']}: {str(e)}"))
                logger.exception("Error fetching tour data")
                continue
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Unexpected error processing {tour_config['name']}: {str(e)}"))
                logger.exception("Unexpected error")
                continue

        self.stdout.write(self.style.SUCCESS('Successfully populated golf data'))

    def process_event(self, event_data, golf_tour):
        # Extract event details
        event_id = event_data.get('id')
        name = event_data.get('name', '')
        
        # Get competition data directly from the event data
        competition_data = event_data
        
        # Get start date
        start_date_str = competition_data.get('date') or competition_data.get('startDate')
        if not start_date_str:
            logger.warning(f"No date found for event {name}, using current time")
            start_date = timezone.now()
        else:
            try:
                # Try parsing with timezone format first (e.g., 2024-04-28T14:00+0000)
                start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M%z')
            except ValueError:
                try:
                    # Try parsing with Z format (e.g., 2024-04-28T14:00:00Z)
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%SZ')
                    start_date = pytz.UTC.localize(start_date)
                except ValueError:
                    try:
                        # Try parsing without seconds (e.g., 2024-04-28T14:00)
                        start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
                        start_date = pytz.UTC.localize(start_date)
                    except ValueError:
                        try:
                            # Try parsing date only (e.g., 2024-04-28)
                            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                            # Set time to noon UTC for date-only events
                            start_date = start_date.replace(hour=12, minute=0)
                            start_date = pytz.UTC.localize(start_date)
                        except ValueError:
                            logger.error(f"Could not parse date {start_date_str} for event {name}, using current time")
                            start_date = timezone.now()

        # Get status information
        status = competition_data.get('status', {}).get('type', {})
        state = status.get('state', '').lower()
        
        # Determine state based on date and status
        now = timezone.now()
        if state == 'pre' and start_date < now:
            state = 'post'  # Event is in the past
        elif state == 'post' and start_date > now:
            state = 'pre'  # Event is in the future
        elif not state:
            if start_date > now:
                state = 'pre'
            else:
                state = 'post'

        # Get course information
        course_data = competition_data.get('course') or {}
        course_name = course_data.get('name', 'Unknown Course')
        course, _ = GolfCourse.objects.get_or_create(
            name=course_name,
            defaults={
                'par': course_data.get('par', 'N/A'),
                'yardage': course_data.get('yardage', 'N/A')
            }
        )

        # Get venue information
        venue_data = competition_data.get('venue', {})
        venue_name = venue_data.get('fullName', 'Location TBD')
        city = venue_data.get('address', {}).get('city', 'Unknown')
        state_location = venue_data.get('address', {}).get('state', 'Unknown')

        # Create or update event
        event, created = GolfEvent.objects.update_or_create(
            event_id=event_id,
            defaults={
                'name': name,
                'short_name': competition_data.get('shortName', name),
                'date': start_date,
                'state': state,
                'completed': status.get('completed', False),
                'venue': venue_name,
                'city': city,
                'state_location': state_location,
                'tour': golf_tour,
                'course': course,
                'purse': competition_data.get('purse', 'N/A'),
                'broadcast': competition_data.get('broadcast', 'N/A'),
                'current_round': status.get('period', 1),
                'total_rounds': competition_data.get('rounds', 4),
                'is_playoff': status.get('playoff', False),
                'weather_condition': competition_data.get('weather', {}).get('condition', 'N/A'),
                'weather_temperature': competition_data.get('weather', {}).get('temperature', 'N/A'),
            }
        )

        # Process competitors
        if 'competitors' in competition_data:
            self.process_leaderboard(event, competition_data)
        else:
            self.stdout.write(self.style.WARNING(f"No competitors found for event {name}"))

    def process_leaderboard(self, event, competition_data):
        try:
            # Clear existing leaderboard entries for this event
            LeaderboardEntry.objects.filter(event=event).delete()

            competitors = competition_data.get('competitors', [])
            if not competitors:
                self.stdout.write(self.style.WARNING(f"No competitors found for event {event.name}"))
                return

            for competitor in competitors:
                try:
                    # Get athlete data
                    athlete = competitor.get('athlete', {})
                    if not athlete:
                        continue

                    # Get or create player
                    player, _ = GolfPlayer.objects.get_or_create(
                        player_id=athlete.get('id', f"temp_{athlete.get('displayName', 'unknown')}"),
                        defaults={
                            'name': athlete.get('displayName', ''),
                            'country': athlete.get('flag', {}).get('alt', ''),
                            'world_ranking': None
                        }
                    )

                    # Create leaderboard entry
                    LeaderboardEntry.objects.create(
                        event=event,
                        player=player,
                        position=competitor.get('position', {}).get('displayValue', 'N/A'),
                        score=competitor.get('score', 'N/A'),
                        rounds=competitor.get('linescores', []),
                        strokes=competitor.get('strokes', 'N/A'),
                        status=competitor.get('status', {}).get('type', {}).get('name', 'active')
                    )

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing competitor in event {event.name}: {str(e)}"))
                    continue

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error processing leaderboard for event {event.name}: {str(e)}"))

    def get_event_state(self, event_data):
        """Determine the event state from the data."""
        status = event_data.get('status', {}).get('type', {})
        state = status.get('state', '').lower()
        
        if state in ['pre', 'post']:
            return state
        elif state in ['in']:
            return 'in'
        else:
            return 'pre'  # Default to pre if unknown 