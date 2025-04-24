# core/horse_racing_events.py
import logging
from core.models import HorseRacingMeeting, HorseRacingRace, HorseRacingResult, RaceRunner
from datetime import datetime, timedelta

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
        
        meetings = HorseRacingMeeting.objects.filter(
            date__range=[start_date, end_date]
        ).select_related('course').prefetch_related('races__results', 'races__runners').order_by('date', 'course__name')
        
        data = []
        for meeting in meetings:
            races = []
            for race in meeting.races.all():
                runners = race.runners.all()
                result = race.results.first()
                horses = [
                    {
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
                        'finish_status': result.position if result and result.horse == runner.horse else runner.number
                    }
                    for runner in runners
                ]
                races.append({
                    'race_time': race.off_time,
                    'name': race.name or 'Unnamed Race',
                    'horses': horses,
                    'result': {
                        'winner': result.horse.name if result else None,
                        'positions': [
                            {'position': result.position, 'name': result.horse.name}
                            for result in race.results.all()
                        ] if result else []
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
        
        logger.info(f"Fetched {len(data)} meetings from database")
        logger.debug(f"Sample meeting: {data[0] if data else 'None'}")
        return data

    except Exception as e:
        logger.error(f"Error in get_racecards_json: {str(e)}", exc_info=True)
        return []