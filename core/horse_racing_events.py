# core/horse_racing_events.py
import logging
from datetime import datetime, timedelta
from django.db.utils import DatabaseError, OperationalError
from django.db import models

from core.models import HorseRacingMeeting

logger = logging.getLogger(__name__)

def get_racecards_json():
    """
    Fetch horse racing racecards and results from the database.
    Returns data for today, tomorrow, and results for the last 7 days.
    """
    try:
        logger.debug("Fetching racecard data from database")
        today = datetime.now().date()
        start_date = today - timedelta(days=7)
        end_date = today + timedelta(days=1)
        
        logger.debug("Querying meetings from %s to %s", start_date, end_date)
        meetings: models.QuerySet[HorseRacingMeeting] = HorseRacingMeeting.objects.filter(  # type: ignore[attr-defined]
            date__range=[start_date, end_date]
        ).select_related('course').prefetch_related(
            'races__results',
            'races__runners',
            'races__runners__horse',
            'races__runners__jockey',
            'races__runners__trainer'
        ).order_by('date', 'course__name')
        
        logger.debug("Found %d meetings", len(meetings))
        
        data = []
        for meeting in meetings:
            races = []
            logger.debug("Processing meeting: %s on %s, Races: %d", meeting.course.name, meeting.date, meeting.races.count())
            for race in meeting.races.all():
                results = race.results.all()
                runners = race.runners.all()
                winner = next((result.horse.name for result in results if result.position == '1'), None)
                
                logger.debug("Processing race: %s at %s", race.name, race.off_time)
                logger.debug("Number of runners: %d", runners.count())
                logger.debug("Number of results: %d", results.count())
                
                horses = []
                for runner in runners:
                    horse_data = {
                        'number': runner.number,
                        'name': runner.horse.name,
                        'jockey': runner.jockey.name if runner.jockey else 'Unknown',
                        'trainer': runner.trainer.name if runner.trainer else 'Unknown',
                        'owner': runner.owner or 'Unknown',
                        'odds': 'N/A',
                        'form': runner.form or 'N/A',
                        'rpr': runner.rpr or 'N/A',
                        'spotlight': runner.spotlight or 'N/A',
                        'trainer_14_days': {
                            'runs': runner.trainer_14_days_runs or 0,
                            'wins': runner.trainer_14_days_wins or 0,
                            'percent': runner.trainer_14_days_percent or 0
                        },
                        'finish_status': str(results.filter(horse=runner.horse).first().position) if results.filter(horse=runner.horse).exists() else 'Unknown'
                    }
                    logger.debug("Horse data: %s", horse_data)
                    horses.append(horse_data)
                
                race_data = {
                    'race_time': race.off_time,
                    'name': race.name or 'Unnamed Race',
                    'horses': horses,
                    'result': {
                        'winner': winner,
                        'positions': [
                            {'position': result.position, 'name': result.horse.name}
                            for result in results
                        ]
                    },
                    'going_data': race.going or 'N/A',
                    'runners': f"{race.field_size or len(horses)} runners",
                    'tv': 'N/A'
                }
                logger.debug("Race data: %s", race_data)
                races.append(race_data)
            
            meeting_data = {
                'date': meeting.date.isoformat(),
                'displayDate': meeting.date.strftime('%b %d, %Y'),
                'venue': meeting.course.name,
                'url': meeting.url or '#',
                'races': races
            }
            logger.debug("Meeting data: %s", meeting_data)
            data.append(meeting_data)
        
        logger.info("Fetched %d meetings from database", len(data))
        logger.debug("Sample meeting: %s", data[0] if data else 'None')
        return data

    except (DatabaseError, OperationalError) as e:
        logger.error("Error in get_racecards_json: %s", str(e), exc_info=True)
        return []