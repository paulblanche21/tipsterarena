# core/management/commands/scrape_racecards.py
import os
import subprocess
import json
import logging
import csv
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from collections import defaultdict
from core.models import RaceMeeting, Race, RaceResult

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Scrape horse racing racecards and results using rpscrape'

    def add_arguments(self, parser):
        parser.add_argument('--date', help='Date to scrape (e.g., 2025-04-15, today, tomorrow)')
        parser.add_argument('--results', action='store_true', help='Scrape results for past 7 days')

    def handle(self, *args, **options):
        logger.debug("Starting scrape_racecards handle")
        meetings = []
        try:
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)
            rpscrape_dir = os.path.join(os.path.dirname(__file__), 'rpscrape', 'scripts')
            base_rpscrape_dir = os.path.join(os.path.dirname(__file__), 'rpscrape')
            racecards_dir = os.path.join(base_rpscrape_dir, 'racecards')
            csv_dir = os.path.join(base_rpscrape_dir, 'data', 'dates', 'all')

            # Verify directories
            logger.debug(f"rpscrape_dir: {rpscrape_dir}")
            logger.debug(f"base_rpscrape_dir: {base_rpscrape_dir}")
            logger.debug(f"racecards_dir: {racecards_dir}")
            logger.debug(f"csv_dir: {csv_dir}")
            for d in [rpscrape_dir, base_rpscrape_dir, racecards_dir, csv_dir]:
                if not os.path.exists(d):
                    logger.info(f"Creating directory: {d}")
                    os.makedirs(d, exist_ok=True)
                if not os.access(d, os.W_OK):
                    logger.error(f"No write permission for directory: {d}")
                    return "Error: No write permission for directory"

            # Run rpscrape.py for results if needed
            if options['results']:
                logger.info("Running rpscrape.py for results")
                race_types = ['flat', 'jumps']
                for i in range(1, 8):
                    past_date = today - timedelta(days=i)
                    date_str = past_date.strftime('%Y/%m/%d')
                    for race_type in race_types:
                        try:
                            result = subprocess.run(
                                ['python', 'rpscrape.py', '--date', date_str, '--region', 'all', '--type', race_type],
                                cwd=rpscrape_dir,
                                capture_output=True,
                                text=True
                            )
                            logger.debug(f"rpscrape.py stdout for {race_type} on {date_str}: {result.stdout}")
                            logger.debug(f"rpscrape.py stderr for {race_type} on {date_str}: {result.stderr}")
                            if result.returncode != 0:
                                logger.error(f"rpscrape.py failed for {race_type} on {date_str}: {result.stderr}")
                        except Exception as e:
                            logger.error(f"Error running rpscrape.py for {race_type} on {date_str}: {str(e)}")
                            continue

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
                        logger.error('Invalid date format. Use YYYY-MM-DD, today, or tomorrow')
                        return "Error: Invalid date format"

            for date in dates:
                date_str = date.strftime('%Y-%m-%d')
                cmd_arg = 'today' if date == today else 'tomorrow' if date == tomorrow else date_str
                logger.info(f"Scraping racecards for {cmd_arg} ({date_str})")
                try:
                    # Run racecards.py
                    logger.debug(f"Executing: python racecards.py {cmd_arg} in {rpscrape_dir}")
                    result = subprocess.run(
                        ['python', 'racecards.py', cmd_arg],
                        cwd=rpscrape_dir,
                        capture_output=True,
                        text=True,
                        env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
                    )
                    logger.debug(f"racecards.py stdout: {result.stdout}")
                    logger.debug(f"racecards.py stderr: {result.stderr}")
                    if result.returncode != 0:
                        logger.error(f"racecards.py failed for {cmd_arg}: {result.stderr}")
                        continue

                    # Check JSON output
                    json_path = os.path.join(racecards_dir, f'{date_str}.json')
                    logger.info(f"Looking for JSON file: {json_path}")
                    if not os.path.exists(json_path):
                        logger.error(f"No JSON file found at {json_path}")
                        continue

                    logger.debug(f"JSON file exists: {json_path}, size: {os.path.getsize(json_path)} bytes")
                    try:
                        with open(json_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            logger.debug(f"Loaded JSON data, keys: {list(data.keys())[:5]}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in {json_path}: {str(e)}")
                        continue

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
                                    'finish_status': str(i + 1),
                                    'name': runner.get('name', 'Unknown'),
                                    'jockey': runner.get('jockey', 'Unknown'),
                                    'odds': runner.get('odds', 'N/A') or 'N/A',
                                    'trainer': runner.get('trainer', 'Unknown'),
                                    'owner': runner.get('owner', 'Unknown'),
                                    'form': runner.get('form', 'N/A'),
                                    'rpr': runner.get('rpr', 'N/A'),
                                    'spotlight': runner.get('spotlight', runner.get('comment', 'No additional info')),
                                    'trainer_14_days': runner.get('trainer_14_days', {})
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
                    logger.error(f"Error processing racecards for {cmd_arg}: {str(e)}", exc_info=True)
                    continue

            # Handle results for past 7 days from CSV
            if options['results']:
                for i in range(1, 8):
                    past_date = today - timedelta(days=i)
                    date_str = past_date.strftime('%Y_%m_%d')
                    date_display = past_date.strftime('%Y-%m-%d')
                    logger.info(f"Processing results for {date_display}")
                    try:
                        # Read CSV
                        csv_path = os.path.join(csv_dir, f'{date_str}.csv')
                        logger.info(f"Looking for CSV file: {csv_path}")
                        if not os.path.exists(csv_path):
                            logger.warning(f"No CSV file found at {csv_path}")
                            continue
                        if not os.access(csv_path, os.R_OK):
                            logger.error(f"No read permission for CSV file: {csv_path}")
                            continue

                        venue_meetings = {}
                        races_by_venue_time = defaultdict(list)
                        with open(csv_path, 'r', encoding='utf-8') as f:
                            reader = csv.DictReader(f)
                            logger.debug(f"CSV headers: {reader.fieldnames}")
                            for row in reader:
                                venue = row['course'].replace(' (IRE)', '')
                                race_time = row['off']
                                race_name = row['race_name']
                                pos = row['pos']
                                horse = {
                                    'number': pos if pos.isdigit() else '0',
                                    'finish_status': pos,
                                    'name': row['horse'],
                                    'jockey': row['jockey'],
                                    'odds': row.get('odds', 'N/A'),
                                    'trainer': row['trainer'],
                                    'owner': row['owner'],
                                    'form': row.get('form', 'N/A'),
                                    'rpr': row['rpr'] or 'N/A',
                                    'spotlight': row['comment'] or 'No additional info',
                                    'trainer_14_days': {}
                                }
                                sort_pos = int(pos) if pos.isdigit() else 999
                                races_by_venue_time[(venue, race_time, race_name)].append((sort_pos, horse))

                        # Process races
                        for (venue, race_time, race_name), horses_data in races_by_venue_time.items():
                            if venue.lower() == 'down':
                                venue = 'Down Royal'
                            if venue not in venue_meetings:
                                venue_meetings[venue] = {
                                    'date': past_date.isoformat(),
                                    'displayDate': past_date.strftime('%b %d, %Y'),
                                    'venue': venue,
                                    'races': [],
                                    'url': f"https://www.racingpost.com/results/{date_display}/{venue.lower().replace(' ', '-')}"
                                }
                            winner = None
                            placed = []
                            horses = []
                            for sort_pos, horse in sorted(horses_data, key=lambda x: x[0]):
                                pos = horse['finish_status']
                                if pos == '1':
                                    winner = horse['name']
                                elif pos in ('2', '3'):
                                    placed.append({'position': pos, 'name': horse['name']})
                                elif pos in ('PU', 'F', 'UR', 'RR', 'CO', 'BD', 'DSQ'):
                                    logger.debug(f"Including horse {horse['name']} with finish_status: {pos}")
                                horses.append(horse)
                            result_data = {'winner': winner, 'positions': placed} if winner else None
                            venue_meetings[venue]['races'].append({
                                'race_time': race_time,
                                'name': race_name or 'Unnamed Race',
                                'horses': horses,
                                'result': result_data,
                                'going_data': row.get('going', 'N/A'),
                                'runners': row.get('ran', '0') + ' runners',
                                'tv': 'N/A'
                            })

                        meetings.extend(venue_meetings.values())
                        logger.info(f"Processed {len(venue_meetings)} result meetings for {date_display}")
                        logger.debug(f"Completed CSV processing for {csv_path}")

                    except Exception as e:
                        logger.error(f"Error processing results for {date_display}: {str(e)}", exc_info=True)
                        continue

            # Save meetings to database
            for meeting in meetings:
                try:
                    # Create or get RaceMeeting
                    meeting_obj, created = RaceMeeting.objects.get_or_create(
                        date=meeting['date'],
                        venue=meeting['venue'],
                        defaults={'url': meeting['url']}
                    )
                    logger.debug(f"{'Created' if created else 'Retrieved'} meeting: {meeting_obj}")

                    for race in meeting['races']:
                        # Convert race_time to TimeField format (HH:MM:SS)
                        race_time_str = race['race_time']
                        try:
                            race_time = datetime.strptime(race_time_str, '%H:%M').time()
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid race_time format: {race_time_str}, using default")
                            race_time = datetime.strptime('00:00', '%H:%M').time()

                        # Create or get Race
                        race_obj, created = Race.objects.get_or_create(
                            meeting=meeting_obj,
                            race_time=race_time,
                            defaults={
                                'name': race['name'],
                                'horses': race['horses']
                            }
                        )
                        logger.debug(f"{'Created' if created else 'Retrieved'} race: {race_obj}")

                        # Create RaceResult if result data exists (from CSV results)
                        if race['result']:
                            RaceResult.objects.get_or_create(
                                race=race_obj,
                                defaults={
                                    'winner': race['result']['winner'] or '',
                                    'placed_horses': race['result']['positions']
                                }
                            )
                            logger.debug(f"Created result for race: {race_obj}")

                except Exception as e:
                    logger.error(f"Error saving meeting {meeting['venue']} on {meeting['date']}: {str(e)}", exc_info=True)
                    continue

            # Log meetings by date for verification
            date_counts = defaultdict(int)
            for meeting in meetings:
                date_counts[meeting['date']] += 1
            logger.info(f"Meetings by date: {dict(date_counts)}")

            # Return a string to satisfy Django's BaseCommand
            return f"Successfully processed {len(meetings)} meetings"

        except Exception as e:
            logger.error(f"Unexpected error in scrape_racecards: {str(e)}", exc_info=True)
            return f"Error: {str(e)}"