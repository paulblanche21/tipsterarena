# core/management/commands/populate_tennis.py
import requests
import time
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
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
        # Get today's date in YYYYMMDD format
        today = datetime.now().strftime('%Y%m%d')
        
        # Define ATP and WTA leagues
        leagues = [
            {'league_id': 'atp', 'name': 'ATP Tour', 'url': f'https://site.api.espn.com/apis/site/v2/sports/tennis/atp/scoreboard?dates={today}', 'priority': 1},
            {'league_id': 'wta', 'name': 'WTA Tour', 'url': f'https://site.api.espn.com/apis/site/v2/sports/tennis/wta/scoreboard?dates={today}', 'priority': 2},
        ]

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        for league_info in leagues:
            league, _ = TennisLeague.objects.get_or_create(
                league_id=league_info['league_id'],
                defaults={'name': league_info['name'], 'icon': "🎾", 'priority': league_info['priority']}
            )

            self.stdout.write(f"Fetching events for {league_info['name']}...")
            url = league_info['url']

            for attempt in range(3):
                try:
                    response = requests.get(url, headers=headers, timeout=10)
                    self.stdout.write(f"Response status for {league_info['name']}: {response.status_code}")
                    self.stdout.write(f"Response body: {response.text[:500]}...")
                    response.raise_for_status()
                    data = response.json()
                    break
                except RequestException as e:
                    if attempt == 2:
                        self.stdout.write(self.style.ERROR(f"Failed to fetch data for {league_info['name']} after 3 attempts: {str(e)}"))
                        continue
                    self.stdout.write(self.style.WARNING(f"Attempt {attempt + 1} failed for {league_info['name']}: {str(e)}. Retrying..."))
                    time.sleep(2 ** attempt)

            events = data.get('events', [])
            self.stdout.write(f"Found {len(events)} tennis events for {league_info['name']}")

            for tournament in events:
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

                for comp in competitions:
                    venue_data = comp.get('venue', {})
                    venue_obj, _ = TennisVenue.objects.get_or_create(
                        name=venue_data.get('fullName', 'Location TBD'),
                        defaults={'court': venue_data.get('court', 'Unknown')}
                    )

                    competitors = comp.get('competitors', [])
                    player1_data = competitors[0] if competitors else {'athlete': {}}
                    player2_data = competitors[1] if len(competitors) > 1 else {'athlete': {}}

                    player1, _ = TennisPlayer.objects.get_or_create(
                        name=player1_data.get('athlete', {}).get('displayName', 'TBD'),
                        defaults={
                            'short_name': player1_data.get('athlete', {}).get('shortName', 'TBD'),
                            'world_ranking': player1_data.get('tournamentSeed', 'N/A'),
                        }
                    )
                    player2, _ = TennisPlayer.objects.get_or_create(
                        name=player2_data.get('athlete', {}).get('displayName', 'TBD'),
                        defaults={
                            'short_name': player2_data.get('athlete', {}).get('shortName', 'TBD'),
                            'world_ranking': player2_data.get('tournamentSeed', 'N/A'),
                        }
                    )

                    score = "TBD"
                    sets = []
                    if len(competitors) == 2:
                        p1_scores = [s['value'] for s in competitors[0].get('linescores', [{'value': 0}])]
                        p2_scores = [s['value'] for s in competitors[1].get('linescores', [{'value': 0}])]
                        score = f"{'-'.join(map(str, p1_scores))} - {'-'.join(map(str, p2_scores))}"
                        for i in range(max(len(p1_scores), len(p2_scores))):
                            sets.append({
                                'setNumber': i + 1,
                                'team1Score': p1_scores[i] if i < len(p1_scores) else '-',
                                'team2Score': p2_scores[i] if i < len(p2_scores) else '-',
                            })

                    # Skip TBD matches
                    if player1.name == 'TBD' and player2.name == 'TBD':
                        self.stdout.write(f"Skipping TBD match: {comp['id']}")
                        continue

                    TennisEvent.objects.update_or_create(
                        event_id=comp['id'],
                        defaults={
                            'tournament': tournament_obj,
                            'date': datetime.fromisoformat(comp['date'].replace('Z', '+00:00')),
                            'state': comp.get('status', {}).get('type', {}).get('state', 'unknown'),
                            'completed': comp.get('status', {}).get('type', {}).get('completed', False),
                            'player1': player1,
                            'player2': player2,
                            'score': score,
                            'sets': sets,
                            'stats': {},
                            'clock': comp.get('status', {}).get('displayClock', '0:00'),
                            'period': comp.get('status', {}).get('period', 0),
                            'round_name': comp.get('round', {}).get('displayName', 'Unknown Round'),
                            'venue': venue_obj,
                            'match_type': comp.get('type', {}).get('text', 'Unknown'),
                            'player1_rank': player1_data.get('tournamentSeed', 'N/A'),
                            'player2_rank': player2_data.get('tournamentSeed', 'N/A'),
                        }
                    )