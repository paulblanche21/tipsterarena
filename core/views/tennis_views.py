"""Views for handling tennis events in Tipster Arena."""

import logging
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes, throttle_classes
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q

from ..models import TennisEvent
from ..serializers import TennisEventSerializer

logger = logging.getLogger(__name__)

def validate_state_param(state):
    """Validate state parameter for tennis events."""
    valid_states = ['pre', 'in', 'post', 'inplay']  # Add 'inplay' as a valid state
    if state not in valid_states:
        raise ValidationError(f'Invalid state. Must be one of: {", ".join(valid_states)}')
    # Map 'inplay' to 'in' for database query
    return 'in' if state == 'inplay' else state

class TennisEventsList(APIView):
    """View for listing tennis events."""
    authentication_classes = []  # Remove authentication requirement for GET requests
    permission_classes = []  # Remove permission requirement for GET requests
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def get(self, request):
        """Get a list of tennis events."""
        # Get query parameters
        category = request.query_params.get('category')
        tournament_id = request.query_params.get('tournament_id')
        
        # Map category to state
        state = None
        if category == 'fixtures':
            state = 'pre'
        elif category == 'inplay':
            state = 'in'
        elif category == 'results':
            state = 'post'

        # Build query
        queryset = TennisEvent.objects.all()
        
        # Apply state filter if category was provided
        if state:
            queryset = queryset.filter(state=state)
            
            # Additional date filtering
            now = timezone.now()
            if state == 'pre':
                # Only future matches for fixtures
                queryset = queryset.filter(date__gt=now)
            elif state == 'post':
                # Only matches from last 30 days for results
                thirty_days_ago = now - timedelta(days=30)
                queryset = queryset.filter(date__gte=thirty_days_ago)

        # Apply tournament filter if provided
        if tournament_id:
            queryset = queryset.filter(tournament__tournament_id=tournament_id)

        # Order by date
        if state == 'pre':
            queryset = queryset.order_by('date')  # Ascending for fixtures
        else:
            queryset = queryset.order_by('-date')  # Descending for results and inplay

        # Serialize data
        serializer = TennisEventSerializer(queryset, many=True)
        return Response(serializer.data)

class TennisEventDetail(APIView):
    """API endpoint for retrieving a single tennis event."""
    authentication_classes = []
    permission_classes = []
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def get(self, request, event_id):
        """Get details of a specific tennis event."""
        event = get_object_or_404(TennisEvent, event_id=event_id)
        serializer = TennisEventSerializer(event)
        return Response(serializer.data)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
@throttle_classes([UserRateThrottle, AnonRateThrottle])
def tennis_event_stats(request, event_id):
    """Get detailed statistics for a tennis event."""
    event = get_object_or_404(TennisEvent, event_id=event_id)
    
    # Get head-to-head stats
    h2h_stats = get_head_to_head_stats(event.player1, event.player2)
    
    # Get player form
    player1_form = get_player_form(event.player1)
    player2_form = get_player_form(event.player2)
    
    # Get tournament history
    player1_tournament_history = get_tournament_history(event.player1, event.tournament)
    player2_tournament_history = get_tournament_history(event.player2, event.tournament)
    
    data = {
        'head_to_head': h2h_stats,
        'player1_form': player1_form,
        'player2_form': player2_form,
        'player1_tournament_history': player1_tournament_history,
        'player2_tournament_history': player2_tournament_history
    }
    
    return Response(data)

def get_head_to_head_stats(player1, player2):
    """Get head-to-head statistics between two tennis players."""
    h2h_matches = TennisEvent.objects.filter(
        Q(player1=player1, player2=player2) | Q(player1=player2, player2=player1),
        state='post'  # Only completed matches
    ).order_by('-date')

    stats = {
        'total_matches': h2h_matches.count(),
        'player1_wins': 0,
        'player2_wins': 0,
        'last_5_matches': [],
        'surface_breakdown': {
            'hard': {'player1': 0, 'player2': 0},
            'clay': {'player1': 0, 'player2': 0},
            'grass': {'player1': 0, 'player2': 0}
        }
    }

    for match in h2h_matches:
        winner = match.winner
        surface = match.venue.surface if match.venue else 'unknown'

        if winner == player1:
            stats['player1_wins'] += 1
            if surface in stats['surface_breakdown']:
                stats['surface_breakdown'][surface]['player1'] += 1
        elif winner == player2:
            stats['player2_wins'] += 1
            if surface in stats['surface_breakdown']:
                stats['surface_breakdown'][surface]['player2'] += 1

        if len(stats['last_5_matches']) < 5:
            stats['last_5_matches'].append({
                'date': match.date,
                'tournament': match.tournament.name,
                'winner': winner.name,
                'score': match.score
            })

    return stats

def get_player_form(player):
    """Get recent form statistics for a tennis player."""
    recent_matches = TennisEvent.objects.filter(
        Q(player1=player) | Q(player2=player),
        state='post'  # Only completed matches
    ).order_by('-date')[:10]  # Last 10 matches

    form = {
        'matches_played': recent_matches.count(),
        'wins': 0,
        'losses': 0,
        'recent_matches': []
    }

    for match in recent_matches:
        winner = match.winner
        is_winner = (winner == player)

        if is_winner:
            form['wins'] += 1
        else:
            form['losses'] += 1

        form['recent_matches'].append({
            'date': match.date,
            'tournament': match.tournament.name,
            'opponent': match.player2.name if match.player1 == player else match.player1.name,
            'result': 'W' if is_winner else 'L',
            'score': match.score
        })

    return form

def get_tournament_history(player, tournament):
    """Get player's history in a specific tournament."""
    tournament_matches = TennisEvent.objects.filter(
        Q(player1=player) | Q(player2=player),
        tournament=tournament,
        state='post'  # Only completed matches
    ).order_by('-date')

    history = {
        'matches_played': tournament_matches.count(),
        'wins': 0,
        'losses': 0,
        'best_result': None,
        'last_appearances': []
    }

    for match in tournament_matches:
        winner = match.winner
        is_winner = (winner == player)

        if is_winner:
            history['wins'] += 1
        else:
            history['losses'] += 1

        if len(history['last_appearances']) < 5:
            history['last_appearances'].append({
                'year': match.date.year,
                'round': match.round,
                'result': 'W' if is_winner else 'L',
                'opponent': match.player2.name if match.player1 == player else match.player1.name,
                'score': match.score
            })

        # Update best result if this match was in a later round
        if not history['best_result'] or match.round_rank > history['best_result']['round_rank']:
            history['best_result'] = {
                'year': match.date.year,
                'round': match.round,
                'round_rank': match.round_rank
            }

    return history 