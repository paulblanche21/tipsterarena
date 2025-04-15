import logging
from datetime import datetime, timedelta
from core.models import RaceMeeting, Race, RaceResult
from django.core.management import call_command

logger = logging.getLogger(__name__)

def get_racecards_json():
    """
    Fetch horse racing racecards for today and tomorrow, and results for the last 7 days using rpscrape.
    """
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    seven_days_ago = today - timedelta(days=7)
    meetings = []

    try:
        # Scrape racecards for today and tomorrow
        logger.debug("Fetching racecards and results via scrape_racecards command")
        meetings = call_command('scrape_racecards', results=True)
        if not meetings:
            logger.warning("No meetings returned from scrape_racecards")
        else:
            logger.info(f"Fetched {len(meetings)} meetings from rpscrape")

        return meetings

    except Exception as e:
        logger.error(f"Error fetching racecards with rpscrape: {str(e)}")
        # Fallback to RaceMeeting model
        meetings = RaceMeeting.objects.filter(
            date__gte=seven_days_ago,
            date__lte=tomorrow
        ).order_by('-date', 'venue')

        racecards = []
        for meeting in meetings:
            races = meeting.races.all().order_by('race_time')
            races_data = [
                {
                    'race_time': race.race_time.strftime('%H:%M') if race.race_time else 'N/A',
                    'name': race.name or 'Unnamed Race',
                    'horses': race.horses or [],
                    'result': {
                        'winner': result.winner,
                        'positions': result.placed_horses
                    } if (result := race.results.first()) and result.winner else None,
                    'going_data': 'N/A',
                    'runners': 'N/A',
                    'tv': 'N/A'
                }
                for race in races
            ]
            racecards.append({
                'date': meeting.date.isoformat(),
                'displayDate': meeting.date.strftime('%b %d, %Y'),
                'venue': meeting.venue,
                'races': races_data,
                'url': f"https://www.racingpost.com/racecards/{meeting.date.strftime('%Y-%m-%d')}/{meeting.venue.lower().replace(' ', '-')}"
            })
        logger.info(f"Fallback: Fetched {len(racecards)} meetings from RaceMeeting model")
        return racecards