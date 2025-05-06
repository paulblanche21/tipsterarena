"""Management command to populate racing data."""

import logging
import os
import sys
from datetime import datetime, timedelta


from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from tenacity import retry, stop_after_attempt, wait_exponential

from core.models import (
    Horse,
    HorseRacingCourse,
    HorseRacingMeeting,
    HorseRacingRace,
    HorseRacingResult,
    RaceRunner,
    Jockey,
    Trainer,
)
from core.management.commands.rpscrape.scripts.rpscrape import scrape_results
from core.management.commands.rpscrape.scripts.utils.region import get_region
from core.management.commands.rpscrape.scripts.utils.time_utils import standardize_time_format

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fetches and stores horse racing data from Racing Post'

    def __init__(self):
        super().__init__()
        self.cache_timeout = 3600  # 1 hour
        self.update_interval = 60  # 1 minute between updates
        self.max_retries = 3
        
        # Add rpscrape directory to Python path
        rpscrape_dir = os.path.join(os.path.dirname(__file__), 'rpscrape')
        if rpscrape_dir not in sys.path:
            sys.path.append(rpscrape_dir)

        # Import rpscrape modules after adding to path
        from core.management.commands.rpscrape.scripts.racecards import scrape_racecards
        from core.management.commands.rpscrape.scripts.rpscrape import scrape_results
        self.scrape_racecards = scrape_racecards
        self.scrape_results = scrape_results

    def add_arguments(self, parser):
        parser.add_argument(
            '--force-update',
            action='store_true',
            help='Force update regardless of cache',
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def fetch_racing_data(self, date):
        """
        Fetch racing data for a specific date with retry mechanism
        """
        try:
            data = {}
            
            # Convert date to string format if needed
            date_str = date.strftime('%Y-%m-%d') if isinstance(date, datetime) else str(date)
            
            # If date is today or tomorrow, fetch racecards
            today = timezone.now().date()
            if date == today:
                data['racecards'] = self.scrape_racecards('today')
            elif date == today + timedelta(days=1):
                data['racecards'] = self.scrape_racecards('tomorrow')
            
            # For today or past dates, fetch results
            if date <= today:
                # Try both flat and jumps races
                data['results'] = {
                    'flat': scrape_results('flat', date_str),
                    'jumps': scrape_results('jumps', date_str)
                }
            
            return data

        except Exception as e:
            logger.error(f"Error fetching racing data for {date}: {e}")
            raise

    def should_update(self):
        """
        Check if we should update the data based on cache
        """
        last_update = cache.get('last_racing_update')
        if not last_update:
            return True
        
        last_update = datetime.fromisoformat(last_update)
        return (timezone.now() - last_update).seconds > self.update_interval

    @transaction.atomic
    def store_racing_data(self, data, date):
        """
        Store racing data in database with transaction safety
        """
        try:
            # Handle racecards data
            if isinstance(data, list):
                for race_url in data:
                    # Parse race URL to get course_id and race_id
                    url_parts = race_url.split('/')
                    if len(url_parts) < 8:
                        logger.warning(f"Invalid race URL format: {race_url}")
                        continue
                    
                    course_id = url_parts[4]
                    race_id = url_parts[7]
                    course_name = url_parts[5].replace('-', ' ').title()

                    # Create or update course
                    course, _ = HorseRacingCourse.objects.get_or_create(
                        course_id=course_id,
                        defaults={
                            'name': course_name,
                            'region': 'Unknown'  # We'll update this later
                        }
                    )

                    # Create or update meeting
                    meeting, _ = HorseRacingMeeting.objects.get_or_create(
                        course=course,
                        date=date,
                        defaults={}
                    )

                    # Create or update race
                    race_obj, _ = HorseRacingRace.objects.get_or_create(
                        meeting=meeting,
                        race_id=race_id,
                        defaults={}
                    )

            # Handle results data
            if 'results' in data:
                for race_type, races in data['results'].items():
                    for race in races:
                        # Create or update course
                        course, _ = HorseRacingCourse.objects.update_or_create(
                            name=race['course'],
                            defaults={
                                'location': race.get('location', 'Unknown'),
                                'track_type': race.get('track_type', 'Unknown'),
                                'surface': race.get('surface', 'Unknown'),
                                'region': get_region(race['course'])
                            }
                        )

                        # Create or update meeting
                        meeting, _ = HorseRacingMeeting.objects.update_or_create(
                            course=course,
                            date=date,
                            defaults={
                                'url': race.get('url', '')
                            }
                        )

                        # Standardize off_time format
                        off_time = standardize_time_format(race.get('off_time', ''))
                        if not off_time:
                            logger.warning(f"Invalid off_time format: {race.get('off_time')} for race {race.get('race_id')}")
                            continue

                        # Create or update race
                        race_obj, _ = HorseRacingRace.objects.update_or_create(
                            meeting=meeting,
                            race_id=race['race_id'],
                            defaults={
                                'off_time': off_time,
                                'name': race.get('race', ''),
                                'distance': race.get('distance', ''),
                                'going': race.get('going', ''),
                                'prize': race.get('prize', ''),
                                'race_class': race.get('class', ''),
                                'race_type': race_type,
                                'field_size': len(race.get('runners', []))
                            }
                        )

                        # Process runners
                        for runner in race.get('runners', []):
                            # Create or update horse
                            horse, _ = Horse.objects.get_or_create(
                                name=runner['horse'],
                                defaults={'age': runner.get('age', 0)}
                            )

                            # Create or update jockey
                            jockey = None
                            if runner.get('jockey'):
                                jockey, _ = Jockey.objects.get_or_create(
                                    name=runner['jockey']
                                )

                            # Create or update trainer
                            trainer = None
                            if runner.get('trainer'):
                                trainer, _ = Trainer.objects.get_or_create(
                                    name=runner['trainer']
                                )

                            # Create or update runner
                            runner_obj, _ = RaceRunner.objects.update_or_create(
                                race=race_obj,
                                horse=horse,
                                defaults={
                                    'number': runner.get('number', ''),
                                    'jockey': jockey,
                                    'trainer': trainer,
                                    'owner': runner.get('owner', ''),
                                    'form': runner.get('form', ''),
                                    'rpr': runner.get('rpr', ''),
                                    'spotlight': runner.get('spotlight', ''),
                                    'trainer_14_days_runs': runner.get('trainer_14_days', {}).get('runs', 0),
                                    'trainer_14_days_wins': runner.get('trainer_14_days', {}).get('wins', 0),
                                    'trainer_14_days_percent': runner.get('trainer_14_days', {}).get('percent', 0)
                                }
                            )

                            # Create or update result if available
                            if runner.get('position'):
                                result, _ = HorseRacingResult.objects.update_or_create(
                                    race=race_obj,
                                    horse=horse,
                                    defaults={
                                        'position': runner['position'],
                                        'distance_beaten': runner.get('distance_beaten', ''),
                                        'sp': runner.get('sp', ''),
                                        'in_play_high': runner.get('in_play_high', ''),
                                        'in_play_low': runner.get('in_play_low', '')
                                    }
                                )

            # Update cache timestamp
            cache.set('last_racing_update', timezone.now().isoformat(), self.cache_timeout)
            logger.info(f"Successfully stored racing data for {date}")

        except Exception as e:
            logger.error(f"Error storing racing data: {e}")
            raise

    def handle(self, *args, **options):
        """
        Main command handler
        """
        try:
            # Get today's date
            today = timezone.now().date()
            
            # Check if we should update
            if not options['force_update'] and not self.should_update():
                self.stdout.write(self.style.SUCCESS('Data is up to date'))
                return
            
            # Fetch and store data for today and tomorrow
            for date in [today, today + timedelta(days=1)]:
                try:
                    data = self.fetch_racing_data(date)
                    if data:
                        self.store_racing_data(data, date)
                        self.stdout.write(self.style.SUCCESS(f'Successfully updated racing data for {date}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'No racing data found for {date}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error processing data for {date}: {e}'))
            
            self.stdout.write(self.style.SUCCESS('Racing data update complete'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Command failed: {e}'))
            raise 