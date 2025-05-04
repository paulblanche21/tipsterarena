"""Views for handling golf events in Tipster Arena."""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes, throttle_classes
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.shortcuts import get_object_or_404
from django.utils import timezone

from ..models import GolfEvent, GolfPlayer, GolfTournament, GolfRound, GolfScore
from ..serializers import GolfEventSerializer, GolfPlayerSerializer, GolfTournamentSerializer

logger = logging.getLogger(__name__)

class GolfEventsList(APIView):
    """View for listing golf events."""
    authentication_classes = []  # Remove authentication requirement for GET requests
    permission_classes = []  # Remove permission requirement for GET requests
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def get(self, request):
        try:
            # Get category from query parameters
            category = request.query_params.get('category', 'fixtures')
            
            # Base queryset for filtering
            queryset = GolfEvent.objects.all().select_related(
                'tournament', 'course'
            ).prefetch_related(
                'players', 'rounds', 'scores'
            )

            now = timezone.now()

            # Apply category filter
            if category == 'fixtures':
                queryset = queryset.filter(state='pre', start_date__gt=now)
            elif category == 'inplay':
                queryset = queryset.filter(state='in')
            elif category == 'results':
                queryset = queryset.filter(state='post')
            else:
                return Response(
                    {'error': 'Invalid category. Must be one of: fixtures, inplay, results'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Order by date
            queryset = queryset.order_by('start_date')

            # Serialize data
            serializer = GolfEventSerializer(queryset, many=True)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error in GolfEventsList view: {str(e)}")
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class GolfEventDetail(APIView):
    """API endpoint for retrieving a single golf event."""
    authentication_classes = []
    permission_classes = []
    throttle_classes = [UserRateThrottle, AnonRateThrottle]
    
    def get(self, request, event_id):
        """Get a single golf event by ID."""
        try:
            # Extract numeric ID if string ID is provided
            if isinstance(event_id, str) and event_id.startswith('golf_event_'):
                event_id = int(event_id.split('_')[-1])
                
            # Get the event with related data
            event = get_object_or_404(
                GolfEvent.objects.select_related(
                    'tournament', 'course'
                ).prefetch_related(
                    'players',
                    'rounds',
                    'scores',
                    'scores__player',
                    'scores__round'
                ),
                id=event_id
            )
            
            # Serialize the event
            serializer = GolfEventSerializer(event)
            return Response(serializer.data)
            
        except ValueError:
            return Response(
                {'error': 'Invalid event ID format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error in GolfEventDetail view: {str(e)}")
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
@throttle_classes([UserRateThrottle, AnonRateThrottle])
def golf_player_stats(request, player_id):
    """Get detailed statistics for a golf player."""
    try:
        player = get_object_or_404(GolfPlayer, id=player_id)
        
        # Get recent tournament history
        recent_tournaments = GolfScore.objects.filter(
            player=player,
            round__event__state='post'
        ).select_related(
            'round__event__tournament'
        ).order_by('-round__event__start_date')[:10]

        # Calculate stats
        tournament_history = []
        total_rounds = 0
        total_score = 0
        wins = 0
        top_10s = 0

        for score in recent_tournaments:
            event = score.round.event
            position = score.final_position
            
            tournament_history.append({
                'tournament': event.tournament.name,
                'date': event.start_date,
                'position': position,
                'score': score.total_score,
                'rounds': [r.score for r in score.round_scores.all()]
            })

            total_rounds += len(score.round_scores.all())
            total_score += score.total_score
            
            if position == 1:
                wins += 1
            if position <= 10:
                top_10s += 1

        # Calculate averages
        average_score = total_score / total_rounds if total_rounds > 0 else None

        stats = {
            'player': GolfPlayerSerializer(player).data,
            'tournament_history': tournament_history,
            'stats': {
                'wins': wins,
                'top_10s': top_10s,
                'average_score': average_score,
                'tournaments_played': len(tournament_history)
            }
        }
        
        return Response(stats)
            
    except Exception as e:
        logger.error(f"Error in golf_player_stats view: {str(e)}")
        return Response(
            {'error': 'Internal server error', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
@throttle_classes([UserRateThrottle, AnonRateThrottle])
def golf_tournament_history(request, tournament_id):
    """Get historical data for a golf tournament."""
    try:
        tournament = get_object_or_404(GolfTournament, id=tournament_id)
        
        # Get past events
        past_events = GolfEvent.objects.filter(
            tournament=tournament,
            state='post'
        ).order_by('-start_date')

        # Calculate tournament stats
        winners = []
        winning_scores = []
        course_records = {}

        for event in past_events:
            winner_score = GolfScore.objects.filter(
                round__event=event,
                final_position=1
            ).first()
            
            if winner_score:
                winners.append({
                    'year': event.start_date.year,
                    'player': winner_score.player.name,
                    'score': winner_score.total_score
                })
                winning_scores.append(winner_score.total_score)

            # Track course records
            lowest_round = GolfRound.objects.filter(
                event=event
            ).order_by('score').first()
            
            if lowest_round:
                course = event.course.name
                if course not in course_records or lowest_round.score < course_records[course]['score']:
                    course_records[course] = {
                        'score': lowest_round.score,
                        'player': lowest_round.player.name,
                        'year': event.start_date.year
                    }

        stats = {
            'tournament': GolfTournamentSerializer(tournament).data,
            'history': {
                'winners': winners,
                'average_winning_score': sum(winning_scores) / len(winning_scores) if winning_scores else None,
                'course_records': course_records
            }
        }
        
        return Response(stats)
            
    except Exception as e:
        logger.error(f"Error in golf_tournament_history view: {str(e)}")
        return Response(
            {'error': 'Internal server error', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 