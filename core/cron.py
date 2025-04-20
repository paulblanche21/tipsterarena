import logging
from core.views import fetch_and_store_football_events
from core.models import FootballEvent
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

def update_football_events():
    """
    Fetch and store football events (fixtures, in-play, results) for Premier League, La Liga, and Serie A.
    Runs every 24 hours.
    """
    try:
        logger.info("Starting cron job to fetch football events")
        fetch_and_store_football_events()
        logger.info("Successfully fetched and stored football events")
    except Exception as e:
        logger.error(f"Error in update_football_events cron job: {str(e)}", exc_info=True)

def check_inplay_matches():
    """
    Check for in-play football matches every 10 minutes to verify system functionality.
    Logs the number of in-play matches and fetches minimal data if needed.
    """
    try:
        logger.info("Starting cron job to check in-play matches")
        # Check current in-play matches in the database
        inplay_count = FootballEvent.objects.filter(state='in').count()
        logger.info(f"Found {inplay_count} in-play matches in the database")

        # Optionally, fetch minimal data to ensure in-play matches are up-to-date
        today = timezone.now().date()
        start_date = today
        end_date = today
        start_date_str = start_date.strftime('%Y%m%d')
        end_date_str = end_date.strftime('%Y%m%d')

        from core.views import FOOTBALL_LEAGUES
        for league_config in FOOTBALL_LEAGUES:
            league_id = league_config['league_id']
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_id}/scoreboard?dates={start_date_str}-{end_date_str}"
            try:
                import requests
                response = requests.get(url)
                if not response.ok:
                    logger.error(f"Failed to fetch in-play data for {league_config['name']}: {response.status_code}")
                    continue
                data = response.json()
                inplay_events = [event for event in data.get('events', []) if event.get('status', {}).get('type', {}).get('state') == 'in']
                logger.info(f"Fetched {len(inplay_events)} in-play events for {league_config['name']}")
                # Update only in-play events to minimize database writes
                for event in inplay_events:
                    event_id = event.get('id')
                    competitions = event.get('competitions', [{}])[0]
                    competitors = competitions.get('competitors', [])
                    home = next((c for c in competitors if c.get('homeAway', '').lower() == 'home'), competitors[0] if competitors else {})
                    away = next((c for c in competitors if c.get('homeAway', '').lower() == 'away'), competitors[1] if competitors else {})
                    FootballEvent.objects.update_or_create(
                        event_id=event_id,
                        defaults={
                            'state': 'in',
                            'status_description': event.get('status', {}).get('type', {}).get('description', 'In Progress'),
                            'status_detail': event.get('status', {}).get('type', {}).get('detail', 'N/A'),
                            'home_score': home.get('score', '0'),
                            'away_score': away.get('score', '0'),
                            'clock': event.get('status', {}).get('type', {}).get('clock', '0:00'),
                            'period': event.get('status', {}).get('type', {}).get('period', 0)
                        }
                    )
            except requests.RequestException as e:
                logger.error(f"Error fetching in-play data for {league_config['name']}: {str(e)}")
    except Exception as e:
        logger.error(f"Error in check_inplay_matches cron job: {str(e)}", exc_info=True)