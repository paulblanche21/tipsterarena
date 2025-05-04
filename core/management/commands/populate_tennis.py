# core/management/commands/populate_tennis.py
import requests
import time
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from requests.exceptions import RequestException
from core.models import TennisLeague, TennisTournament, TennisPlayer, TennisVenue, TennisEvent

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
        # Get dates for the last 7 days and next 7 days
        dates = []
        today = datetime.now()
        for i in range(-7, 8):  # -7 to +7 days
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

            for date in dates:
                self.stdout.write(f"Fetching {league_info['name']} events for date: {date}")
                # Fetch data from ESPN API
                url = f"https://site.api.espn.com/apis/site/v2/sports/tennis/{league_info['id']}/scoreboard?dates={date}"
                response = requests.get(url)
                self.stdout.write(f"Response status for {league_info['name']} on {date}: {response.status_code}")

                if not response.ok:
                    self.stdout.write(self.style.WARNING(f"Failed to fetch {league_info['name']} data for {date}: {response.status_code}"))
                    continue

                data = response.json()
                events = data.get('events', [])
                self.stdout.write(f"Found {len(events)} tennis events for {league_info['name']} on {date}")
                self.stdout.write(f"Raw API response: {data}")

                for tournament in events:
                    self.stdout.write(f"Processing tournament: {tournament.get('name', 'Unknown')}")
                    tournament_obj, _ = TennisTournament.objects.get_or_create(
                        tournament_id=tournament['id'],
                        defaults={
                            'name': tournament.get('name', 'Unknown Tournament'),
                            'league': league,
                            'start_date': datetime.fromisoformat(tournament.get('date', '').replace('Z', '+00:00')).date() if tournament.get('date') else None,
                            'end_date': None,
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
                        # Get match details
                        match_id = competition.get('id')
                        if not match_id:
                            continue

                        # Get competitors
                        competitors = competition.get('competitors', [])
                        if len(competitors) != 2:
                            continue

                        # Get player data
                        player1_data = competitors[0].get('athlete', {})
                        player2_data = competitors[1].get('athlete', {})

                        # Create players even if data is incomplete
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
                            self.stdout.write(f"Skipping match {match_id} - Both players TBD")
                            continue

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

                        # Get match state
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
                        if len(competitors) == 2:
                            p1_scores = [s.get('value', 0) for s in competitors[0].get('linescores', [])]
                            p2_scores = [s.get('value', 0) for s in competitors[1].get('linescores', [])]
                            if p1_scores and p2_scores:
                                score = f"{'-'.join(map(str, p1_scores))} - {'-'.join(map(str, p2_scores))}"
                                for i in range(max(len(p1_scores), len(p2_scores))):
                                    sets.append({
                                        'setNumber': i + 1,
                                        'team1Score': p1_scores[i] if i < len(p1_scores) else '-',
                                        'team2Score': p2_scores[i] if i < len(p2_scores) else '-',
                                    })

                        # Create or update event
                        match_date = datetime.fromisoformat(competition.get('date', '').replace('Z', '+00:00'))
                        match_obj, created = TennisEvent.objects.update_or_create(
                            event_id=match_id,
                            defaults={
                                'tournament': tournament_obj,
                                'date': match_date,
                                'state': state,
                                'completed': status.get('type', {}).get('completed', False),
                                'player1': player1,
                                'player2': player2,
                                'score': score,
                                'sets': sets,
                                'stats': competition.get('stats', {}),
                                'clock': status.get('clock', '0:00'),
                                'period': status.get('period', 0),
                                'round_name': competition.get('round', {}).get('name', 'Unknown Round'),
                                'venue': venue,
                                'match_type': competition.get('type', {}).get('name', 'Unknown'),
                                'player1_rank': player1_data.get('rank', {}).get('current', 'N/A'),
                                'player2_rank': player2_data.get('rank', {}).get('current', 'N/A'),
                                'last_updated': timezone.now()
                            }
                        )

                        if created:
                            self.stdout.write(f"Created new match: {player1.name} vs {player2.name}")
                        else:
                            self.stdout.write(f"Updated match: {player1.name} vs {player2.name}")
                
                # Add a small delay between date requests to avoid rate limiting
                time.sleep(1)