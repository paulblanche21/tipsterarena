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
        
        for tour_config in GOLF_TOURS:
            try:
                # Fetch events for this tour
                url = f"https://site.api.espn.com/apis/site/v2/sports/golf/{tour_config['tour_id']}/scoreboard"
                self.stdout.write(f"Fetching events for {tour_config['name']}...")
                
                response = requests.get(url)
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
        
        # Fetch detailed competition data with leaderboard
        url = f"https://site.api.espn.com/apis/site/v2/sports/golf/{golf_tour.name.split()[0].lower()}/leaderboard/{event_id}"
        self.stdout.write(f"Fetching detailed data from: {url}")
        response = requests.get(url)
        if response.status_code == 200:
            detailed_data = response.json()
            competition_data = detailed_data.get('events', [{}])[0]
            self.stdout.write(f"Got detailed data for event {name}")
        else:
            self.stdout.write(self.style.WARNING(f"Failed to fetch detailed data for event {name}"))
            competition_data = event_data

        # Handle different date formats from ESPN API
        start_date_str = competition_data.get('startDate')
        if not start_date_str:
            logger.warning(f"No startDate found for event {name}, using current time")
            start_date = timezone.now()
        else:
            try:
                # Try parsing with timezone format first (e.g., 2024-04-28T14:00+0000)
                start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M%z')
            except ValueError:
                try:
                    # Try parsing with Z format (e.g., 2024-04-28T14:00:00Z)
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%SZ')
                except ValueError:
                    try:
                        # Try parsing without seconds (e.g., 2024-04-28T14:00)
                        start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
                    except ValueError:
                        try:
                            # Try parsing date only (e.g., 2024-04-28)
                            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                        except ValueError:
                            logger.error(f"Could not parse date {start_date_str} for event {name}, using current time")
                            start_date = timezone.now()

        # Ensure datetime is timezone-aware
        if start_date.tzinfo is None:
            start_date = pytz.UTC.localize(start_date)

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

        # Get status information
        status = competition_data.get('status', {}).get('type', {})
        completed = status.get('completed', False)
        state = self.get_event_state(competition_data)

        # Create or update event
        event, created = GolfEvent.objects.update_or_create(
            event_id=event_id,
            defaults={
                'name': name,
                'short_name': competition_data.get('shortName', name),
                'date': start_date,
                'state': state,
                'completed': completed,
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

        # Process leaderboard
        if 'competitions' in competition_data and len(competition_data['competitions']) > 0:
            self.process_leaderboard(event, competition_data['competitions'][0])
        else:
            self.stdout.write(self.style.WARNING(f"No competition data found for event {name}"))

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

                    # Get or create player with unique player_id
                    player_id = athlete.get('id')
                    if not player_id:
                        self.stdout.write(self.style.WARNING(f"No player ID found for athlete in event {event.name}"))
                        continue

                    player, _ = GolfPlayer.objects.get_or_create(
                        player_id=player_id,
                        defaults={
                            'name': athlete.get('displayName', ''),
                            'country': athlete.get('flag', {}).get('alt', ''),
                            'world_ranking': None  # ESPN API no longer provides ranking directly
                        }
                    )

                    # Get rounds data from linescores
                    rounds = []
                    strokes = 0
                    linescores = competitor.get('linescores', [])
                    
                    for linescore in linescores:
                        score = linescore.get('value')
                        if score is not None:
                            rounds.append(int(score))
                            strokes += int(score)

                    # Fill remaining rounds with None
                    while len(rounds) < 4:
                        rounds.append(None)

                    # Get status
                    status = 'active'  # Default status
                    if competitor.get('status', {}).get('type', {}).get('name', '').lower() in ['cut', 'withdrawn', 'disqualified']:
                        status = 'inactive'

                    # Get score
                    score = competitor.get('score', 'E')
                    if score == 'E':
                        score = '0'
                    elif not score:
                        score = 'N/A'

                    # Get position
                    position = competitor.get('order', 0)  # Use 'order' field for position

                    # Create leaderboard entry
                    LeaderboardEntry.objects.create(
                        event=event,
                        player=player,
                        position=str(position),
                        score=str(score),
                        status=status,
                        rounds=rounds,
                        strokes=strokes if strokes > 0 else 'N/A'
                    )

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing competitor in event {event.name}: {str(e)}"))
                    continue

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error processing leaderboard for event {event.name}: {str(e)}"))
            logger.exception("Error processing leaderboard")

    def get_event_state(self, event_data):
        status = event_data.get('status', {}).get('type', {})
        if status.get('completed', False):
            return 'post'
        elif status.get('state', '') == 'in':
            return 'in'
        else:
            return 'pre' 