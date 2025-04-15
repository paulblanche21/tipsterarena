import os
import subprocess
import json
import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Scrape horse racing racecards and results using rpscrape'

    def add_arguments(self, parser):
        parser.add_argument('--date', help='Date to scrape (e.g., 2025-04-15, today, tomorrow)')
        parser.add_argument('--results', action='store_true', help='Scrape results for past 7 days')

    def handle(self, *args, **options):
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        seven_days_ago = today - timedelta(days=7)
        rpscrape_dir = os.path.join(os.path.dirname(__file__), 'rpscrape', 'scripts')
        base_rpscrape_dir = os.path.join(os.path.dirname(__file__), 'rpscrape')
        meetings = []

        # Handle racecards
        dates = [today, tomorrow] if not options['date'] else []
        if options['date']:
            if options['date'] == 'today':
                dates = [today]
            elif options['date'] == 'tomorrow':
                dates = [tomorrow]
            else:
                try:
                    dates = [datetime.strptime(options['date'], '%Y-%m-%d').date()]
                except ValueError:
                    self.stdout.write(self.style.ERROR('Invalid date format. Use YYYY-MM-DD, today, or tomorrow'))
                    return

        for date in dates:
            date_str = date.strftime('%Y-%m-%d')
            cmd_arg = 'today' if date == today else 'tomorrow' if date == tomorrow else date_str
            logger.info(f"Scraping racecards for {cmd_arg} ({date_str})")
            try:
                # Run racecards.py
                result = subprocess.run(
                    ['python', 'racecards.py', cmd_arg],
                    cwd=rpscrape_dir,
                    capture_output=True,
                    text=True,
                    env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
                )
                if result.returncode != 0:
                    logger.error(f"racecards.py failed for {cmd_arg}: {result.stderr}")
                    continue

                # Read JSON output
                json_path = os.path.join(base_rpscrape_dir, 'racecards', f'{date_str}.json')
                if not os.path.exists(json_path):
                    logger.warning(f"No JSON output found for {cmd_arg}")
                    continue

                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Handle nested JSON structure
                if not isinstance(data, dict):
                    logger.warning(f"Expected dict for {cmd_arg}, got {type(data)}")
                    continue

                # Flatten nested structure
                races = []
                for region, courses in data.items():
                    for course, times in courses.items():
                        for time, race in times.items():
                            if isinstance(race, dict):
                                races.append(race)
                            else:
                                logger.warning(f"Invalid race entry for {cmd_arg} at {course} {time}: {race}")

                if not races:
                    logger.warning(f"No valid races found for {cmd_arg}")
                    continue

                # Group by venue
                venue_meetings = {}
                for race in races:
                    if not isinstance(race, dict):
                        logger.warning(f"Invalid race entry for {cmd_arg}: {race}")
                        continue
                    venue = race.get('course', 'Unknown')
                    if venue.lower() == 'down':
                        venue = 'Down Royal'
                    if venue not in venue_meetings:
                        venue_meetings[venue] = {
                            'date': date.isoformat(),
                            'displayDate': date.strftime('%b %d, %Y'),
                            'venue': venue,
                            'races': [],
                            'url': f"https://www.racingpost.com/racecards/{date_str}/{venue.lower().replace(' ', '-')}"
                        }
                    venue_meetings[venue]['races'].append({
                        'race_time': race.get('off_time', 'N/A'),
                        'name': race.get('race_name', 'Unnamed Race'),
                        'horses': [
                            {
                                'number': str(i + 1),
                                'name': runner.get('name', 'Unknown'),
                                'jockey': runner.get('jockey', 'Unknown'),
                                'odds': runner.get('odds', 'N/A') or 'N/A',
                                'trainer': runner.get('trainer', 'Unknown'),
                                'owner': runner.get('owner', 'Unknown')
                            } for i, runner in enumerate(race.get('runners', []))
                        ],
                        'result': None,
                        'going_data': race.get('going', 'N/A'),
                        'runners': f"{race.get('field_size', 0)} runners",
                        'tv': race.get('tv', 'N/A') or 'N/A'
                    })

                meetings.extend(venue_meetings.values())
                logger.info(f"Processed {len(venue_meetings)} meetings for {cmd_arg}")

            except Exception as e:
                logger.error(f"Error processing racecards for {cmd_arg}: {str(e)}")

        # Handle results for past 7 days
        if options['results']:
            for i in range(1, 8):
                past_date = today - timedelta(days=i)
                date_str = past_date.strftime('%Y-%m-%d')
                date_arg = past_date.strftime('%Y/%m/%d')
                logger.info(f"Scraping results for {date_str}")
                try:
                    # Run rpscrape.py for results
                    result = subprocess.run(
                        ['python', 'rpscrape.py', '-d', date_arg],
                        cwd=rpscrape_dir,
                        capture_output=True,
                        text=True,
                        env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
                    )
                    if result.returncode != 0:
                        logger.error(f"rpscrape.py failed for {date_str}: {result.stderr}")
                        continue

                    # Read JSON output
                    json_path = os.path.join(base_rpscrape_dir, 'results', f'{date_str}.json')
                    if not os.path.exists(json_path):
                        logger.warning(f"No results JSON found for {date_str}")
                        continue

                    with open(json_path, 'r', encoding='utf-8') as f:
                        races_data = json.load(f)

                    # Handle unexpected string output
                    if isinstance(races_data, str):
                        logger.warning(f"Received string instead of list for results {date_str}: {races_data}")
                        continue

                    # Ensure races is a list
                    races = races_data if isinstance(races_data, list) else []
                    if not races:
                        logger.warning(f"Empty races list for results {date_str}")
                        continue

                    # Process results
                    venue_meetings = {}
                    for race in races:
                        if not isinstance(race, dict):
                            logger.warning(f"Invalid race entry for results {date_str}: {race}")
                            continue
                        venue = race.get('course', 'Unknown')
                        if venue.lower() == 'down':
                            venue = 'Down Royal'
                        if venue not in venue_meetings:
                            venue_meetings[venue] = {
                                'date': past_date.isoformat(),
                                'displayDate': past_date.strftime('%b %d, %Y'),
                                'venue': venue,
                                'races': [],
                                'url': f"https://www.racingpost.com/results/{date_str}/{venue.lower().replace(' ', '-')}"
                            }
                        result_data = None
                        if race.get('results'):
                            winner = None
                            placed = []
                            for pos, horse in enumerate(race['results'], 1):
                                if pos == 1:
                                    winner = horse.get('name', 'Unknown')
                                elif pos in (2, 3):
                                    placed.append({
                                        'position': str(pos),
                                        'name': horse.get('name', 'Unknown')
                                    })
                            if winner:
                                result_data = {'winner': winner, 'positions': placed}

                        venue_meetings[venue]['races'].append({
                            'race_time': race.get('off_time', 'N/A'),
                            'name': race.get('race_name', 'Unnamed Race'),
                            'horses': [],
                            'result': result_data,
                            'going_data': race.get('going', 'N/A'),
                            'runners': 'N/A',
                            'tv': race.get('tv', 'N/A') or 'N/A'
                        })

                    meetings.extend(venue_meetings.values())
                    logger.info(f"Processed {len(venue_meetings)} result meetings for {date_str}")

                except Exception as e:
                    logger.error(f"Error processing results for {date_str}: {str(e)}")

        # Output status message as string
        self.stdout.write(self.style.SUCCESS(f"Scraped {len(meetings)} meetings"))
        # Return meetings for call_command
        return meetings