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
        ).select_related('course').prefetch_related('races__results').order_by('date', 'course__name')
        
        logger.debug("Found %d meetings", len(meetings))
        
        data = []
        for meeting in meetings:
            races = []
            logger.debug("Processing meeting: %s on %s, Races: %d", meeting.course.name, meeting.date, meeting.races.count())
            for race in meeting.races.all():
                results = race.results.all()
                winner = next((result.horse.name for result in results if result.position == '1'), None)
                horses = [
                    {
                        'number': idx + 1,  # Fallback number
                        'name': result.horse.name,
                        'jockey': result.jockey.name if result.jockey else 'Unknown',
                        'trainer': result.trainer.name if result.trainer else 'Unknown',
                        'owner': 'Unknown',
                        'odds': 'N/A',
                        'form': 'N/A',
                        'rpr': result.rpr or 'N/A',
                        'spotlight': 'N/A',
                        'trainer_14_days': {
                            'runs': 0,
                            'wins': 0,
                            'percent': 0
                        },
                        'finish_status': str(result.position) if result.position else 'Unknown'
                    }
                    for idx, result in enumerate(results)
                ]
                races.append({
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
                })
            data.append({
                'date': meeting.date.isoformat(),
                'displayDate': meeting.date.strftime('%b %d, %Y'),
                'venue': meeting.course.name,
                'url': meeting.url or '#',
                'races': races
            })
        
        logger.info("Fetched %d meetings from database", len(data))
        logger.debug("Sample meeting: %s", data[0] if data else 'None')
        return data

    except (DatabaseError, OperationalError) as e:
        logger.error("Error in get_racecards_json: %s", str(e), exc_info=True)
        return []