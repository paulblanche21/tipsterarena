from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import FootballLeague, FootballTeam, FootballEvent, TeamStats
import requests
import logging
from datetime import datetime, timedelta
import pytz

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fetches football events from ESPN API and populates the database'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting football data population...')
        try:
            self.fetch_and_store_football_events()
            self.stdout.write(self.style.SUCCESS('Successfully populated football data'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error populating football data: {str(e)}'))
            raise

    def fetch_and_store_football_events(self):
        # Define leagues to fetch
        leagues = [
            {'league_id': 'eng.1', 'name': 'Premier League', 'icon': '⚽', 'priority': 1},
            {'league_id': 'esp.1', 'name': 'La Liga', 'icon': '⚽', 'priority': 2},
            {'league_id': 'ita.1', 'name': 'Serie A', 'icon': '⚽', 'priority': 3},
        ]

        # Get date range for fetching events
        today = timezone.now().date()
        start_date = today - timedelta(days=7)  # Get events from 7 days ago
        end_date = today + timedelta(days=14)   # Get events up to 14 days in the future

        for league_info in leagues:
            try:
                # Create or update league
                league, _ = FootballLeague.objects.get_or_create(
                    league_id=league_info['league_id'],
                    defaults={
                        'name': league_info['name'],
                        'icon': league_info['icon'],
                        'priority': league_info['priority']
                    }
                )

                # Fetch events from ESPN API
                url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_info['league_id']}/scoreboard"
                params = {
                    'dates': f"{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}"
                }
                
                response = requests.get(url, params=params)
                if not response.ok:
                    logger.error(f"Failed to fetch data for {league_info['name']}: {response.status_code}")
                    continue

                data = response.json()
                events = data.get('events', [])
                logger.info(f"Found {len(events)} events for {league_info['name']}")

                for event in events:
                    try:
                        competition = event.get('competitions', [{}])[0]
                        competitors = competition.get('competitors', [])
                        
                        if len(competitors) != 2:
                            logger.warning(f"Skipping event {event.get('id')}: Invalid number of competitors")
                            continue

                        # Get home and away teams
                        home_team_data = next((c for c in competitors if c.get('homeAway') == 'home'), None)
                        away_team_data = next((c for c in competitors if c.get('homeAway') == 'away'), None)

                        if not home_team_data or not away_team_data:
                            logger.warning(f"Skipping event {event.get('id')}: Missing team data")
                            continue

                        # Create or update teams
                        home_team, _ = FootballTeam.objects.get_or_create(
                            name=home_team_data.get('team', {}).get('displayName', 'Unknown Team'),
                            defaults={
                                'logo': home_team_data.get('team', {}).get('logo'),
                                'form': home_team_data.get('form', 'N/A'),
                                'record': home_team_data.get('records', [{}])[0].get('summary', 'N/A') if home_team_data.get('records') else 'N/A'
                            }
                        )

                        away_team, _ = FootballTeam.objects.get_or_create(
                            name=away_team_data.get('team', {}).get('displayName', 'Unknown Team'),
                            defaults={
                                'logo': away_team_data.get('team', {}).get('logo'),
                                'form': away_team_data.get('form', 'N/A'),
                                'record': away_team_data.get('records', [{}])[0].get('summary', 'N/A') if away_team_data.get('records') else 'N/A'
                            }
                        )

                        # Create team stats
                        home_stats = TeamStats.objects.create(
                            possession='N/A',
                            shots='N/A',
                            shots_on_target='N/A',
                            corners='N/A',
                            fouls='N/A'
                        )

                        away_stats = TeamStats.objects.create(
                            possession='N/A',
                            shots='N/A',
                            shots_on_target='N/A',
                            corners='N/A',
                            fouls='N/A'
                        )

                        # Parse event status
                        status = event.get('competitions', [{}])[0].get('status', {}).get('type', {})
                        state = status.get('state', 'unknown').lower()
                        if state == 'pre':
                            state = 'pre'
                        elif state in ['in', 'playing']:
                            state = 'in'
                        elif state in ['post', 'final']:
                            state = 'post'
                        else:
                            state = 'unknown'

                        # Get broadcast info
                        broadcasts = competition.get('broadcasts', [])
                        broadcast = ', '.join(broadcasts[0].get('names', [])) if broadcasts else 'N/A'

                        # Parse date with timezone
                        event_date = datetime.strptime(event['date'], '%Y-%m-%dT%H:%MZ')
                        event_date = pytz.utc.localize(event_date)

                        # Create or update event
                        FootballEvent.objects.update_or_create(
                            event_id=event['id'],
                            defaults={
                                'name': event.get('name', f"{home_team.name} vs {away_team.name}"),
                                'date': event_date,
                                'state': state,
                                'status_description': status.get('description', 'Unknown'),
                                'status_detail': status.get('detail', 'N/A'),
                                'league': league,
                                'venue': competition.get('venue', {}).get('fullName', 'Location TBD'),
                                'home_team': home_team,
                                'away_team': away_team,
                                'home_score': home_team_data.get('score', '0'),
                                'away_score': away_team_data.get('score', '0'),
                                'home_stats': home_stats,
                                'away_stats': away_stats,
                                'clock': competition.get('status', {}).get('displayClock', None),
                                'period': competition.get('status', {}).get('period', 0),
                                'broadcast': broadcast
                            }
                        )

                    except Exception as e:
                        logger.error(f"Error processing event {event.get('id')}: {str(e)}")
                        continue

            except Exception as e:
                logger.error(f"Error processing league {league_info['name']}: {str(e)}")
                continue 