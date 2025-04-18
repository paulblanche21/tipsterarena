from celery import shared_task
from datetime import datetime, timedelta
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
            {"league": "ita.1", "name": "Serie A"},
            {"league": "fra.1", "name": "Ligue 1"},
            {"league": "uefa.champions", "name": "Champions League"},
            {"league": "uefa.europa", "name": "Europa League"},
            {"league": "eng.fa", "name": "FA Cup"},
            {"league": "eng.2", "name": "EFL Championship"},
            {"league": "por.1", "name": "Primeira Liga"},
            {"league": "ned.1", "name": "Eredivisie"},
            {"league": "nir.1", "name": "Irish League"},
            {"league": "usa.1", "name": "MLS"},
            {"league": "sco.1", "name": "Scottish Premiership"},
        ]

        today = timezone.now()
        start_date = today - timedelta(days=7)
        end_date = today + timedelta(days=14)
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
                    competitions = event.get('competitions', [{}])[0]
                    competitors = competitions.get('competitors', [])
                    home = next((c for c in competitors if c.get('homeAway', '').lower() == 'home'), competitors[0] if competitors else {})
                    away = next((c for c in competitors if c.get('homeAway', '').lower() == 'away'), competitors[1] if len(competitors) > 1 else {})

                    raw_date = event.get('date', '')
                    if not raw_date:
                        logger.warning(f"No date for event {event.get('id', 'unknown')}, skipping")
                        continue
                    try:
                        match_date = timezone.datetime.fromisoformat(raw_date.replace('Z', '+00:00'))
                    except ValueError as e:
                        logger.error(f"Invalid date format for event {event.get('id', 'unknown')}: {raw_date}, error: {e}")
                        continue

                    event_id = event.get('id', '')
                    if not event_id:
                        logger.warning("No event ID for event, skipping")
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
                        summary_response = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{config['league']}/summary?event={event_id}", timeout=5)
                        summary_response.raise_for_status()
                        summary_data = summary_response.json()

                        odds_data = summary_data.get('header', {}).get('competitions', [{}])[0].get('odds', [{}])[0]
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
                                'player': play.get('participants', [{}])[0].get('athlete', {}).get('displayName', 'Unknown'),
                                'isGoal': play.get('type', {}).get('text', '').lower().includes('goal'),
                                'isYellowCard': play.get('yellowCard', False),
                                'isRedCard': play.get('redCard', False),
                            }
                            for play in plays
                            if play.get('type', {}).get('text', '').lower().includes('goal') or play.get('yellowCard') or play.get('redCard')
                        ]
                    except requests.RequestException as e:
                        logger.warning(f"Error fetching summary for event {event_id}: {e}")

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

                logger.info(f"Fetched {len(events)} fixtures for {config['name']}")

            except requests.RequestException as e:
                logger.error(f"Error fetching {config['name']}: {e}")
                continue

        logger.info(f"Successfully fetched and updated {total_fixtures} football fixtures")
        return total_fixtures

    except Exception as e:
        logger.error(f"Error in fetch_football_fixtures: {e}")
        raise fetch_football_fixtures.retry(exc=e, countdown=60)