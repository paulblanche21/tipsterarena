# core/management/commands/populate_tennis.py
import requests
import time
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from requests.exceptions import RequestException
from core.models import TennisLeague, TennisTournament, TennisPlayer, TennisVenue, TennisEvent, TennisPlayerStats

class Command(BaseCommand):
    help = 'Fetches tennis events from ESPN API (ATP and WTA) and populates the database'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting tennis data population...')
        try:
            self.fetch_and_store_tennis_events()
            self.stdout.write(self.style.SUCCESS('Successfully populated tennis data'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error populating tennis data: {str(e)}'))
            raise

    def fetch_and_store_tennis_events(self):
        # Get dates for the last 30 days and next 30 days for better tournament coverage
        dates = []
        today = datetime.now()
        for i in range(-30, 31):  # -30 to +30 days
            date = today + timedelta(days=i)
            dates.append(date.strftime('%Y%m%d'))
        
        # Configure leagues
        leagues = [
            {'id': 'atp', 'name': 'ATP Tour', 'icon': '🎾', 'priority': 1},
            {'id': 'wta', 'name': 'WTA Tour', 'icon': '🎾', 'priority': 2}
        ]

        for league_info in leagues:
            self.stdout.write(f"Fetching events for {league_info['name']}...")
            
            # Create or get league
            league, _ = TennisLeague.objects.get_or_create(
                league_id=league_info['id'],
                defaults={
                    'name': league_info['name'],
                    'icon': league_info['icon'],
                    'priority': league_info['priority']
                }
            )

            # Fetch events for each date
            for date in dates:
                try:
                    url = f"https://site.api.espn.com/apis/site/v2/sports/tennis/{league_info['id']}/scoreboard?dates={date}"
                    response = requests.get(url)
                    response.raise_for_status()
                    data = response.json()
                    
                    if 'events' not in data:
                        continue

                    events = data['events']
                    self.stdout.write(f"Processing {len(events)} events for {date}")

                    for tournament in events:
                        self.stdout.write(f"Processing tournament: {tournament.get('name', 'Unknown')}")
                        
                        # Determine tournament type and surface
                        tournament_type = self.determine_tournament_type(tournament.get('name', ''), league_info['id'])
                        surface = self.determine_surface(tournament.get('name', ''), tournament.get('venue', {}).get('fullName', ''))
                        
                        # Create or update tournament
                        tournament_obj, _ = TennisTournament.objects.get_or_create(
                            tournament_id=tournament['id'],
                            defaults={
                                'name': tournament.get('name', 'Unknown Tournament'),
                                'league': league,
                                'start_date': datetime.fromisoformat(tournament.get('date', '').replace('Z', '+00:00')).date() if tournament.get('date') else None,
                                'end_date': None,
                                'tournament_type': tournament_type,
                                'surface': surface,
                                'status': self.determine_tournament_status(tournament),
                                'location': tournament.get('venue', {}).get('fullName', ''),
                                'website': tournament.get('links', [{}])[0].get('href', '')
                            }
                        )

                        # Handle competitions directly or under groupings
                        competitions = []
                        if 'groupings' in tournament:
                            for grouping in tournament.get('groupings', []):
                                competitions.extend(grouping.get('competitions', []))
                        else:
                            competitions = tournament.get('competitions', [])

                        for competition in competitions:
                            self.process_competition(competition, tournament_obj, league_info['id'])

                except RequestException as e:
                    self.stdout.write(self.style.WARNING(f"Error fetching data for {date}: {str(e)}"))
                    continue
                
                # Add a small delay between date requests to avoid rate limiting
                time.sleep(1)

    def determine_tournament_type(self, name, league_id):
        """Determine tournament type based on name and league"""
        name_lower = name.lower()
        if 'grand slam' in name_lower or any(gs in name_lower for gs in ['australian open', 'french open', 'wimbledon', 'us open']):
            return 'grand_slam'
        elif 'masters' in name_lower or '1000' in name_lower:
            return 'masters'
        elif league_id == 'atp':
            if '500' in name_lower:
                return 'atp_500'
            return 'atp_250'
        else:  # WTA
            if '1000' in name_lower:
                return 'wta_1000'
            elif '500' in name_lower:
                return 'wta_500'
            return 'wta_250'

    def determine_surface(self, tournament_name, venue_name):
        """Determine surface type based on tournament and venue names"""
        name_lower = (tournament_name + ' ' + venue_name).lower()
        if 'clay' in name_lower or 'roland garros' in name_lower:
            return 'clay'
        elif 'grass' in name_lower or 'wimbledon' in name_lower:
            return 'grass'
        elif 'hard' in name_lower or 'us open' in name_lower or 'australian open' in name_lower:
            return 'hard'
        return 'hard'  # Default to hard court

    def determine_tournament_status(self, tournament):
        """Determine tournament status based on dates and competition state"""
        now = timezone.now()
        start_date = datetime.fromisoformat(tournament.get('date', '').replace('Z', '+00:00')) if tournament.get('date') else None
        
        if not start_date:
            return 'upcoming'
            
        if start_date > now:
            return 'upcoming'
            
        # Check if any competitions are in progress
        competitions = []
        if 'groupings' in tournament:
            for grouping in tournament.get('groupings', []):
                competitions.extend(grouping.get('competitions', []))
        else:
            competitions = tournament.get('competitions', [])
            
        for competition in competitions:
            if competition.get('status', {}).get('type', {}).get('state') == 'in':
                return 'active'
                
        return 'completed'

    def process_competition(self, competition, tournament, league_id):
        """Process a single tennis competition/match"""
        match_id = competition.get('id')
        if not match_id:
            return

        # Get competitors
        competitors = competition.get('competitors', [])
        if len(competitors) != 2:
            return

        # Get player data
        player1_data = competitors[0].get('athlete', {})
        player2_data = competitors[1].get('athlete', {})

        # Create or update players
        player1, _ = TennisPlayer.objects.get_or_create(
            name=player1_data.get('displayName', 'TBD'),
            defaults={
                'short_name': player1_data.get('shortName', ''),
                'world_ranking': player1_data.get('rank', {}).get('current', 'N/A')
            }
        )
        
        player2, _ = TennisPlayer.objects.get_or_create(
            name=player2_data.get('displayName', 'TBD'),
            defaults={
                'short_name': player2_data.get('shortName', ''),
                'world_ranking': player2_data.get('rank', {}).get('current', 'N/A')
            }
        )

        # Skip if both players are TBD
        if player1.name == 'TBD' and player2.name == 'TBD':
            return

        # Get venue
        venue_data = competition.get('venue', {})
        venue = None
        if venue_data:
            venue, _ = TennisVenue.objects.get_or_create(
                name=venue_data.get('fullName', 'Unknown Venue'),
                defaults={
                    'court': venue_data.get('court', 'Unknown Court')
                }
            )

        # Get match state and details
        status = competition.get('status', {})
        state_type = status.get('type', {}).get('state', 'pre')
        state_map = {
            'pre': 'pre',
            'in': 'in',
            'post': 'post'
        }
        state = state_map.get(state_type, 'unknown')

        # Get score data
        score = "TBD"
        sets = []
        tiebreak_sets = []
        if len(competitors) == 2:
            p1_scores = [s.get('value', 0) for s in competitors[0].get('linescores', [])]
            p2_scores = [s.get('value', 0) for s in competitors[1].get('linescores', [])]
            if p1_scores and p2_scores:
                score = f"{'-'.join(map(str, p1_scores))} - {'-'.join(map(str, p2_scores))}"
                for i in range(max(len(p1_scores), len(p2_scores))):
                    set_data = {
                        'setNumber': i + 1,
                        'team1Score': p1_scores[i] if i < len(p1_scores) else '-',
                        'team2Score': p2_scores[i] if i < len(p2_scores) else '-',
                    }
                    sets.append(set_data)
                    
                    # Check for tiebreak
                    if p1_scores[i] == 7 and p2_scores[i] == 6 or p1_scores[i] == 6 and p2_scores[i] == 7:
                        tiebreak_sets.append(i + 1)

        # Get service stats
        def get_stat_value(competitor, stat_name):
            stats = competitor.get('statistics', [])
            if isinstance(stats, list):
                for stat in stats:
                    if stat.get('name') == stat_name:
                        return stat.get('value', 0)
                return 0
            elif isinstance(stats, dict):
                return stats.get(stat_name, 0)
            return 0

        service_stats = {
            'player1': {
                'aces': get_stat_value(competitors[0], 'aces'),
                'double_faults': get_stat_value(competitors[0], 'doubleFaults'),
                'first_serve_percentage': get_stat_value(competitors[0], 'firstServePercentage'),
                'service_points_won': get_stat_value(competitors[0], 'servicePointsWon')
            },
            'player2': {
                'aces': get_stat_value(competitors[1], 'aces'),
                'double_faults': get_stat_value(competitors[1], 'doubleFaults'),
                'first_serve_percentage': get_stat_value(competitors[1], 'firstServePercentage'),
                'service_points_won': get_stat_value(competitors[1], 'servicePointsWon')
            }
        }

        # Create or update event
        match_date = datetime.fromisoformat(competition.get('date', '').replace('Z', '+00:00'))
        match_obj, created = TennisEvent.objects.update_or_create(
            event_id=match_id,
            defaults={
                'tournament': tournament,
                'date': match_date,
                'state': state,
                'completed': status.get('type', {}).get('completed', False),
                'player1': player1,
                'player2': player2,
                'score': score,
                'sets': sets,
                'tiebreak_sets': tiebreak_sets,
                'service_stats': service_stats,
                'stats': competition.get('statistics', {}),
                'clock': status.get('clock', '0:00'),
                'period': status.get('period', 0),
                'round_name': competition.get('round', {}).get('name', 'Unknown Round'),
                'venue': venue,
                'match_type': competition.get('type', {}).get('name', 'Unknown'),
                'player1_rank': player1_data.get('rank', {}).get('current', 'N/A'),
                'player2_rank': player2_data.get('rank', {}).get('current', 'N/A'),
                'weather': competition.get('weather', {}),
                'court_conditions': competition.get('conditions', 'Normal'),
                'last_updated': timezone.now()
            }
        )

        if created:
            self.stdout.write(f"Created new match: {player1.name} vs {player2.name}")
        else:
            self.stdout.write(f"Updated match: {player1.name} vs {player2.name}")

        # Update player stats
        if state == 'post' and status.get('type', {}).get('completed', False):
            for player in [player1, player2]:
                stats, _ = TennisPlayerStats.objects.get_or_create(player=player)
                stats.update_stats()