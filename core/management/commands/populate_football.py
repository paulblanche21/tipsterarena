from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import FootballLeague, FootballTeam, FootballEvent, TeamStats, KeyEvent
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

    def fetch_match_stats(self, event_id, league_id):
        """Fetch detailed match statistics from ESPN API."""
        try:
            # First try the summary endpoint for detailed stats
            summary_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_id}/summary"
            scoreboard_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_id}/scoreboard"
            
            # Try summary endpoint first
            response = requests.get(summary_url, params={'event': event_id})
            if response.ok:
                data = response.json()
                boxscore = data.get('boxscore', {})
                teams = boxscore.get('teams', [])
            else:
                # Fallback to scoreboard endpoint
                response = requests.get(scoreboard_url)
                if not response.ok:
                    logger.error(f"Failed to fetch stats for event {event_id}")
                    return None, None
                    
                data = response.json()
                event = next((e for e in data.get('events', []) if e.get('id') == event_id), None)
                if not event:
                    return None, None
                    
                competition = event.get('competitions', [{}])[0]
                teams = competition.get('competitors', [])
            
            if len(teams) != 2:
                logger.warning(f"Invalid number of teams for event {event_id}")
                return None, None

            home_stats = {}
            away_stats = {}

            for team in teams:
                stats_dict = {}
                for stat in team.get('statistics', []):
                    name = stat.get('name')
                    value = stat.get('displayValue', 'N/A')
                    
                    # Map ESPN API stat names to our field names
                    if name == 'possessionPct':
                        stats_dict['possession'] = f"{value}%"
                    elif name == 'totalShots':
                        stats_dict['shots'] = value
                    elif name == 'shotsOnTarget':
                        stats_dict['shots_on_target'] = value
                    elif name == 'wonCorners':
                        stats_dict['corners'] = value
                    elif name == 'foulsCommitted':
                        stats_dict['fouls'] = value

                # Set default values for any missing stats
                stats_dict.setdefault('possession', 'N/A')
                stats_dict.setdefault('shots', 'N/A')
                stats_dict.setdefault('shots_on_target', 'N/A')
                stats_dict.setdefault('corners', 'N/A')
                stats_dict.setdefault('fouls', 'N/A')

                if team.get('homeAway') == 'home':
                    home_stats = stats_dict
                else:
                    away_stats = stats_dict

            logger.info(f"Fetched stats for event {event_id}: Home - {home_stats}, Away - {away_stats}")
            return home_stats, away_stats

        except Exception as e:
            logger.error(f"Error fetching match stats for event {event_id}: {str(e)}")
            return None, None

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
                        event_obj, created = FootballEvent.objects.update_or_create(
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
                                'clock': competition.get('status', {}).get('displayClock', None),
                                'period': competition.get('status', {}).get('period', 0),
                                'broadcast': broadcast
                            }
                        )

                        # Process key events (goals, cards, etc.)
                        if competition.get('boxscore', {}).get('events'):
                            for event_data in competition['boxscore']['events']:
                                if event_data.get('type', {}).get('name') == 'Goal':
                                    # Create key event for goal
                                    KeyEvent.objects.create(
                                        event=event_obj,
                                        type='Goal',
                                        time=event_data.get('clock', {}).get('displayValue', 'N/A'),
                                        team=event_data.get('team', {}).get('name', 'Unknown'),
                                        player=event_data.get('athlete', {}).get('displayName', 'Unknown'),
                                        assist=event_data.get('assist', {}).get('displayName', 'Unassisted'),
                                        is_goal=True
                                    )
                                elif event_data.get('type', {}).get('name') in ['Yellow Card', 'Red Card']:
                                    # Create key event for cards
                                    KeyEvent.objects.create(
                                        event=event_obj,
                                        type=event_data.get('type', {}).get('name'),
                                        time=event_data.get('clock', {}).get('displayValue', 'N/A'),
                                        team=event_data.get('team', {}).get('name', 'Unknown'),
                                        player=event_data.get('athlete', {}).get('displayName', 'Unknown'),
                                        is_yellow_card=event_data.get('type', {}).get('name') == 'Yellow Card',
                                        is_red_card=event_data.get('type', {}).get('name') == 'Red Card'
                                    )

                        # Process match statistics
                        if state in ['in', 'post']:
                            self.process_events([event], league_info['name'], league_info['league_id'])

                    except Exception as e:
                        logger.error(f"Error processing event {event.get('id')}: {str(e)}")
                        continue

            except Exception as e:
                logger.error(f"Error processing league {league_info['name']}: {str(e)}")
                continue

    def process_events(self, events, league_name, league_id):
        """Process football events and store them in the database."""
        logger.info(f"Found {len(events)} events for {league_name}")
        
        for event in events:
            try:
                event_id = event.get('id')
                if not event_id:
                    continue

                # Get match details from scoreboard
                competition = event.get('competitions', [{}])[0]
                details = competition.get('details', [])

                # Process match events (goals, cards, etc.)
                if details:
                    event_obj = FootballEvent.objects.filter(event_id=event_id).first()
                    if event_obj:
                        # Clear existing key events
                        KeyEvent.objects.filter(event=event_obj).delete()
                        
                        for detail in details:
                            event_type = detail.get('type', {}).get('text')
                            clock = detail.get('clock', {}).get('displayValue', 'N/A')
                            team_id = detail.get('team', {}).get('id')
                            athletes = detail.get('athletesInvolved', [])
                            
                            if not athletes:
                                continue
                                
                            player = athletes[0].get('displayName', 'Unknown')
                            team_name = next(
                                (t.name for t in [event_obj.home_team, event_obj.away_team] 
                                 if str(team_id) == str(t.id)), 
                                'Unknown Team'
                            )

                            if event_type == 'Goal' or event_type == 'Penalty - Scored':
                                KeyEvent.objects.create(
                                    event=event_obj,
                                    type='Goal',
                                    time=clock,
                                    team=team_name,
                                    player=player,
                                    is_goal=True,
                                    is_penalty=event_type == 'Penalty - Scored'
                                )
                            elif event_type == 'Yellow Card':
                                KeyEvent.objects.create(
                                    event=event_obj,
                                    type='Yellow Card',
                                    time=clock,
                                    team=team_name,
                                    player=player,
                                    is_yellow_card=True
                                )
                            elif event_type == 'Red Card':
                                KeyEvent.objects.create(
                                    event=event_obj,
                                    type='Red Card',
                                    time=clock,
                                    team=team_name,
                                    player=player,
                                    is_red_card=True
                                )

                # Fetch match stats using the league ID
                if event.get('state', '').lower() in ['in', 'post']:
                    home_match_stats, away_match_stats = self.fetch_match_stats(event_id, league_id)
                    if home_match_stats and away_match_stats:
                        try:
                            # Create team stats objects
                            home_stats = TeamStats.objects.create(
                                possession=home_match_stats.get('possession', 'N/A'),
                                shots=home_match_stats.get('shots', 'N/A'),
                                shots_on_target=home_match_stats.get('shots_on_target', 'N/A'),
                                corners=home_match_stats.get('corners', 'N/A'),
                                fouls=home_match_stats.get('fouls', 'N/A')
                            )
                            away_stats = TeamStats.objects.create(
                                possession=away_match_stats.get('possession', 'N/A'),
                                shots=away_match_stats.get('shots', 'N/A'),
                                shots_on_target=away_match_stats.get('shots_on_target', 'N/A'),
                                corners=away_match_stats.get('corners', 'N/A'),
                                fouls=away_match_stats.get('fouls', 'N/A')
                            )
                            
                            # Update the event with the stats objects
                            event_obj = FootballEvent.objects.filter(event_id=event_id).first()
                            if event_obj:
                                # Delete any existing stats to avoid duplicates
                                if event_obj.home_team_stats:
                                    event_obj.home_team_stats.delete()
                                if event_obj.away_team_stats:
                                    event_obj.away_team_stats.delete()
                                    
                                event_obj.home_team_stats = home_stats
                                event_obj.away_team_stats = away_stats
                                event_obj.save()
                                logger.info(f"Updated stats for event {event_id}")
                        except Exception as stats_error:
                            logger.error(f"Error creating stats for event {event_id}: {str(stats_error)}")
            except Exception as e:
                logger.error(f"Error processing event: {str(e)}")
                continue 