# core/horse_racing_events.py
import logging
from core.models import RaceMeeting
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
        
        # Query meetings for today, tomorrow, and past 7 days
        meetings = RaceMeeting.objects.filter(
            date__range=[start_date, end_date]
        ).prefetch_related('races__results').order_by('date', 'venue')
        
        data = []
        for meeting in meetings:
            races = []
            for race in meeting.races.all():
                result = race.results.first()
                races.append({
                    'race_time': race.race_time.strftime('%H:%M'),
                    'name': race.name,
                    'horses': race.horses,
                    'result': {
                        'winner': result.winner,
                        'positions': result.placed_horses
                    } if result else None,
                    'going_data': 'N/A',  # Add logic if stored
                    'runners': f"{len(race.horses)} runners",
                    'tv': 'N/A'
                })
            data.append({
                'date': meeting.date.isoformat(),
                'displayDate': meeting.date.strftime('%b %d, %Y'),
                'venue': meeting.venue,
                'url': meeting.url,
                'races': races
            })
        
        logger.info(f"Fetched {len(data)} meetings from database")
        logger.debug(f"Sample meeting: {data[0] if data else 'None'}")
        return data

    except Exception as e:
        logger.error(f"Error in get_racecards_json: {str(e)}", exc_info=True)
        return []