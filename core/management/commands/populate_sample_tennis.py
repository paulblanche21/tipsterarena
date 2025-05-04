from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import TennisLeague, TennisTournament, TennisPlayer, TennisVenue, TennisEvent

class Command(BaseCommand):
    help = 'Populates sample tennis data for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample tennis data...')

        # Create leagues
        atp, _ = TennisLeague.objects.get_or_create(
            league_id='atp',
            defaults={
                'name': 'ATP Tour',
                'icon': '🎾',
                'priority': 1
            }
        )
        wta, _ = TennisLeague.objects.get_or_create(
            league_id='wta',
            defaults={
                'name': 'WTA Tour',
                'icon': '🎾',
                'priority': 2
            }
        )

        # Create venues
        venues = []
        for venue_data in [
            ('Roland Garros', 'Court Philippe-Chatrier'),
            ('Wimbledon', 'Centre Court'),
            ('US Open', 'Arthur Ashe Stadium'),
            ('Australian Open', 'Rod Laver Arena'),
        ]:
            venue, _ = TennisVenue.objects.get_or_create(
                name=venue_data[0],
                defaults={'court': venue_data[1]}
            )
            venues.append(venue)

        # Create ATP players
        atp_players = []
        for player_data in [
            ('Novak Djokovic', 'N. Djokovic', '1'),
            ('Carlos Alcaraz', 'C. Alcaraz', '2'),
            ('Daniil Medvedev', 'D. Medvedev', '3'),
            ('Jannik Sinner', 'J. Sinner', '4'),
        ]:
            player, _ = TennisPlayer.objects.get_or_create(
                name=player_data[0],
                defaults={
                    'short_name': player_data[1],
                    'world_ranking': player_data[2]
                }
            )
            atp_players.append(player)

        # Create WTA players
        wta_players = []
        for player_data in [
            ('Iga Świątek', 'I. Świątek', '1'),
            ('Aryna Sabalenka', 'A. Sabalenka', '2'),
            ('Coco Gauff', 'C. Gauff', '3'),
            ('Elena Rybakina', 'E. Rybakina', '4'),
        ]:
            player, _ = TennisPlayer.objects.get_or_create(
                name=player_data[0],
                defaults={
                    'short_name': player_data[1],
                    'world_ranking': player_data[2]
                }
            )
            wta_players.append(player)

        # Create tournaments
        tournaments = {
            'atp': [],
            'wta': []
        }
        
        for tour_data in [
            ('atp', 'atp_rg_2025', 'Roland Garros 2025', atp, 0),
            ('atp', 'atp_wim_2025', 'Wimbledon 2025', atp, 30),
            ('wta', 'wta_rg_2025', 'Roland Garros 2025', wta, 0),
            ('wta', 'wta_wim_2025', 'Wimbledon 2025', wta, 30),
        ]:
            tournament, _ = TennisTournament.objects.get_or_create(
                tournament_id=tour_data[1],
                defaults={
                    'name': tour_data[2],
                    'league': tour_data[3],
                    'start_date': (timezone.now() + timedelta(days=tour_data[4])).date()
                }
            )
            tournaments[tour_data[0]].append(tournament)

        # Create sample matches
        # ATP Matches - Roland Garros (in progress)
        TennisEvent.objects.get_or_create(
            event_id='atp_rg_2025_sf1',
            defaults={
                'tournament': tournaments['atp'][0],
                'date': timezone.now(),
                'state': 'in',
                'completed': False,
                'player1': atp_players[0],  # Djokovic
                'player2': atp_players[1],  # Alcaraz
                'score': '6-4, 4-6, 2-1',
                'sets': [
                    {'setNumber': 1, 'team1Score': 6, 'team2Score': 4},
                    {'setNumber': 2, 'team1Score': 4, 'team2Score': 6},
                    {'setNumber': 3, 'team1Score': 2, 'team2Score': 1},
                ],
                'clock': '2:15',
                'period': 3,
                'round_name': 'Semi Final',
                'venue': venues[0],
                'match_type': 'Singles',
                'player1_rank': '1',
                'player2_rank': '2'
            }
        )

        TennisEvent.objects.get_or_create(
            event_id='atp_rg_2025_sf2',
            defaults={
                'tournament': tournaments['atp'][0],
                'date': timezone.now(),
                'state': 'pre',
                'completed': False,
                'player1': atp_players[2],  # Medvedev
                'player2': atp_players[3],  # Sinner
                'score': '0-0',
                'sets': [],
                'clock': '0:00',
                'period': 0,
                'round_name': 'Semi Final',
                'venue': venues[0],
                'match_type': 'Singles',
                'player1_rank': '3',
                'player2_rank': '4'
            }
        )

        # WTA Matches - Roland Garros (completed and upcoming)
        TennisEvent.objects.get_or_create(
            event_id='wta_rg_2025_sf1',
            defaults={
                'tournament': tournaments['wta'][0],
                'date': timezone.now() - timedelta(hours=2),
                'state': 'post',
                'completed': True,
                'player1': wta_players[0],  # Świątek
                'player2': wta_players[1],  # Sabalenka
                'score': '6-3, 6-4',
                'sets': [
                    {'setNumber': 1, 'team1Score': 6, 'team2Score': 3},
                    {'setNumber': 2, 'team1Score': 6, 'team2Score': 4},
                ],
                'clock': '1:45',
                'period': 2,
                'round_name': 'Semi Final',
                'venue': venues[0],
                'match_type': 'Singles',
                'player1_rank': '1',
                'player2_rank': '2'
            }
        )

        TennisEvent.objects.get_or_create(
            event_id='wta_rg_2025_sf2',
            defaults={
                'tournament': tournaments['wta'][0],
                'date': timezone.now() + timedelta(hours=2),
                'state': 'pre',
                'completed': False,
                'player1': wta_players[2],  # Gauff
                'player2': wta_players[3],  # Rybakina
                'score': '0-0',
                'sets': [],
                'clock': '0:00',
                'period': 0,
                'round_name': 'Semi Final',
                'venue': venues[0],
                'match_type': 'Singles',
                'player1_rank': '3',
                'player2_rank': '4'
            }
        )

        # ATP Matches - Wimbledon (future)
        TennisEvent.objects.get_or_create(
            event_id='atp_wim_2025_r1',
            defaults={
                'tournament': tournaments['atp'][1],
                'date': timezone.now() + timedelta(days=30),
                'state': 'pre',
                'completed': False,
                'player1': atp_players[0],  # Djokovic
                'player2': atp_players[3],  # Sinner
                'score': '0-0',
                'sets': [],
                'clock': '0:00',
                'period': 0,
                'round_name': 'Round 1',
                'venue': venues[1],
                'match_type': 'Singles',
                'player1_rank': '1',
                'player2_rank': '4'
            }
        )

        # WTA Matches - Wimbledon (future)
        TennisEvent.objects.get_or_create(
            event_id='wta_wim_2025_r1',
            defaults={
                'tournament': tournaments['wta'][1],
                'date': timezone.now() + timedelta(days=30),
                'state': 'pre',
                'completed': False,
                'player1': wta_players[0],  # Świątek
                'player2': wta_players[3],  # Rybakina
                'score': '0-0',
                'sets': [],
                'clock': '0:00',
                'period': 0,
                'round_name': 'Round 1',
                'venue': venues[1],
                'match_type': 'Singles',
                'player1_rank': '1',
                'player2_rank': '4'
            }
        )

        self.stdout.write(self.style.SUCCESS('Successfully created sample tennis data')) 