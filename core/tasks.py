from celery import shared_task
from datetime import timedelta
import requests
import logging
from django.utils import timezone
from core.models import FootballFixture

logger = logging.getLogger(__name__)

@shared_task(max_retries=3)
def fetch_football_fixtures(states=None):
    try:
        leagues = [
            {"league": "eng.1", "name": "Premier League"},
            {"league": "esp.1", "name": "La Liga"},
        ]

        today = timezone.now()
        start_date = today - timedelta(days=7)  # Past 7 days for results
        end_date = today + timedelta(days=7)   # Next 7 days for fixtures
        start_date_str = start_date.strftime('%Y%m%d')
        end_date_str = end_date.strftime('%Y%m%d')

        total_fixtures = 0
        for config in leagues:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{config['league']}/scoreboard?dates={start_date_str}-{end_date_str}"
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()

                events = data.get('events', [])
                for event in events:
                    event_id = event.get('id', 'unknown')
                    logger.debug(f"Processing event {event_id}")

                    competitions = event.get('competitions', [])
                    if not competitions:
                        logger.warning(f"No competitions for event {event_id}, skipping")
                        continue
                    competition = competitions[0]

                    competitors = competition.get('competitors', [])
                    if len(competitors) < 2:
                        logger.warning(f"Insufficient competitors for event {event_id}, skipping")
                        continue
                    home = next((c for c in competitors if c.get('homeAway', '').lower() == 'home'), None)
                    away = next((c for c in competitors if c.get('homeAway', '').lower() == 'away'), None)
                    if not home or not away:
                        logger.warning(f"Missing home or away team for event {event_id}, skipping")
                        continue

                    raw_date = event.get('date', '')
                    if not raw_date:
                        logger.warning(f"No date for event {event_id}, skipping")
                        continue
                    try:
                        match_date = timezone.datetime.fromisoformat(raw_date.replace('Z', '+00:00'))
                    except ValueError as e:
                        logger.error(f"Invalid date format for event {event_id}: {raw_date}, error: {e}")
                        continue

                    home_team = home.get('team', {}).get('displayName', 'TBD')
                    away_team = away.get('team', {}).get('displayName', 'TBD')
                    state = event.get('status', {}).get('type', {}).get('state', 'pre')
                    home_score = home.get('score') if state in ['in', 'post'] else None
                    away_score = away.get('score') if state in ['in', 'post'] else None
                    status_detail = event.get('status', {}).get('type', {}).get('detail', 'N/A')

                    if states and state not in states:
                        continue

                    odds = None
                    key_events = []
                    try:
                        summary_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{config['league']}/summary?event={event_id}"
                        summary_response = requests.get(summary_url, timeout=5)
                        summary_response.raise_for_status()
                        summary_data = summary_response.json()

                        competitions_data = summary_data.get('header', {}).get('competitions', [])
                        if competitions_data and 'odds' in competitions_data[0] and competitions_data[0]['odds']:
                            odds_data = competitions_data[0]['odds'][0]
                            odds = {
                                'homeOdds': odds_data.get('homeTeamOdds', {}).get('moneyLine', 'N/A'),
                                'awayOdds': odds_data.get('awayTeamOdds', {}).get('moneyLine', 'N/A'),
                                'drawOdds': odds_data.get('drawOdds', {}).get('moneyLine', 'N/A'),
                                'provider': odds_data.get('provider', {}).get('name', 'Unknown Provider'),
                            }

                        plays = summary_data.get('plays', [])
                        key_events = [
                            {
                                'type': play.get('type', {}).get('text', 'Unknown'),
                                'time': play.get('clock', {}).get('displayValue', 'N/A'),
                                'team': play.get('team', {}).get('displayName', 'Unknown'),
                                'player': play.get('participants', [{}])[0].get('athlete', {}).get('displayName', 'Unknown') if play.get('participants') else 'Unknown',
                                'isGoal': play.get('type', {}).get('text', '').lower().find('goal') != -1,
                                'isYellowCard': play.get('yellowCard', False),
                                'isRedCard': play.get('redCard', False),
                            }
                            for play in plays
                            if play.get('type', {}).get('text', '').lower().find('goal') != -1 or play.get('yellowCard') or play.get('redCard')
                        ]
                    except requests.RequestException as e:
                        logger.warning(f"Error fetching summary for event {event_id}: {e}")

                    try:
                        FootballFixture.objects.update_or_create(
                            event_id=event_id,
                            defaults={
                                'match_date': match_date,
                                'home_team': home_team,
                                'away_team': away_team,
                                'league': config['name'],
                                'state': state,
                                'home_score': home_score,
                                'away_score': away_score,
                                'status_detail': status_detail,
                                'odds': odds,
                                'key_events': key_events,
                                'last_updated': timezone.now(),
                            }
                        )
                        total_fixtures += 1
                        logger.debug(f"Saved fixture: {event_id}, {home_team} vs {away_team}, {match_date}")
                    except Exception as e:
                        logger.error(f"Error saving fixture for event {event_id}: {e}")
                        continue

                logger.info(f"Fetched {len(events)} fixtures for {config['name']}")

            except requests.RequestException as e:
                logger.error(f"Error fetching {config['name']}: {e}")
                continue

        logger.info(f"Successfully fetched and updated {total_fixtures} football fixtures")
        return total_fixtures

    except Exception as e:
        logger.error(f"Error in fetch_football_fixtures: {e}")
        raise fetch_football_fixtures.retry(exc=e, countdown=60)