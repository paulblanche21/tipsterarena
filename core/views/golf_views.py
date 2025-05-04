"""Views for handling golf events in Tipster Arena."""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes, throttle_classes
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.shortcuts import get_object_or_404
from django.utils import timezone

from ..models import GolfEvent, GolfPlayer, GolfTour, LeaderboardEntry
from ..serializers import GolfEventSerializer, GolfPlayerSerializer, GolfTourSerializer

logger = logging.getLogger(__name__)

class FetchGolfEventsView(APIView):
    """API endpoint for fetching and updating golf events."""
    authentication_classes = []
    permission_classes = []
    throttle_classes = [UserRateThrottle, AnonRateThrottle]
    
    def get(self, request):
        """Fetch and update golf events."""
        try:
            # Get query parameters
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            tour_id = request.query_params.get('tour_id')
            
            # Build base query
            queryset = GolfEvent.objects.all()
            
            # Apply filters
            if start_date:
                queryset = queryset.filter(start_date__gte=start_date)
            if end_date:
                queryset = queryset.filter(start_date__lte=end_date)
            if tour_id:
                queryset = queryset.filter(tour_id=tour_id)
            
            # Order by date
            queryset = queryset.order_by('start_date')
            
            # Serialize data
            serializer = GolfEventSerializer(queryset, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error in FetchGolfEventsView: {str(e)}")
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
        recent_tournaments = LeaderboardEntry.objects.filter(
            player=player,
            event__state='post'
        ).select_related(
            'event__tour'
        ).order_by('-event__date')[:10]

        # Calculate stats
        tournament_history = []
        total_rounds = 0
        total_score = 0
        wins = 0
        top_10s = 0

        for entry in recent_tournaments:
            event = entry.event
            position = entry.position
            
            tournament_history.append({
                'tournament': event.tour.name,
                'date': event.date,
                'position': position,
                'score': entry.score,
                'rounds': entry.rounds
            })

            total_rounds += len(entry.rounds)
            total_score += int(entry.score) if entry.score != "N/A" else 0
            
            if position == "1":
                wins += 1
            if position.isdigit() and int(position) <= 10:
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
        tournament = get_object_or_404(GolfTour, id=tournament_id)
        
        # Get past events
        past_events = GolfEvent.objects.filter(
            tour=tournament,
            state='post'
        ).order_by('-date')

        # Calculate tournament stats
        winners = []
        winning_scores = []
        course_records = {}

        for event in past_events:
            winner_entry = LeaderboardEntry.objects.filter(
                event=event,
                position="1"
            ).first()
            
            if winner_entry:
                winners.append({
                    'year': event.date.year,
                    'player': winner_entry.player.name,
                    'score': winner_entry.score
                })
                winning_scores.append(int(winner_entry.score) if winner_entry.score != "N/A" else 0)

            # Track course records
            lowest_round = min(
                (int(score) for score in winner_entry.rounds if score != "N/A"),
                default=None
            )
            
            if lowest_round:
                course = event.course.name
                if course not in course_records or lowest_round < course_records[course]['score']:
                    course_records[course] = {
                        'score': lowest_round,
                        'player': winner_entry.player.name,
                        'year': event.date.year
                    }

        stats = {
            'tournament': GolfTourSerializer(tournament).data,
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