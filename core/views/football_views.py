"""Views for handling football events in Tipster Arena."""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from ..models import FootballEvent
from ..serializers import FootballEventSerializer

logger = logging.getLogger(__name__)

class FootballEventsList(APIView):
    """View for listing football events."""
    authentication_classes = []  # Remove authentication requirement for GET requests
    permission_classes = []  # Remove permission requirement for GET requests
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def get(self, request):
        try:
            # Get category from query parameters
            category = request.query_params.get('category', 'fixtures')
            
            # Base queryset for filtering
            queryset = FootballEvent.objects.all().select_related(
                'league', 'home_team', 'away_team', 'home_team_stats', 'away_team_stats'
            ).prefetch_related(
                'key_events', 'detailed_stats'
            )

            now = timezone.now()

            # Apply category filter
            if category == 'fixtures':
                queryset = queryset.filter(state='pre', date__gt=now)
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
            queryset = queryset.order_by('date')

            # Serialize data
            serializer = FootballEventSerializer(queryset, many=True)
            
            # Log the response for debugging
            logger.info(f"Returning {len(serializer.data)} events for category: {category}")
            
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error in FootballEventsList view: {str(e)}")
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class FootballEventDetail(APIView):
    """API endpoint for retrieving a single football event."""
    authentication_classes = []
    permission_classes = []
    throttle_classes = [UserRateThrottle, AnonRateThrottle]
    
    def get(self, request, event_id):
        """Get a single football event by ID."""
        try:
            # Extract numeric ID if string ID is provided
            if isinstance(event_id, str) and event_id.startswith('football_event_'):
                event_id = int(event_id.split('_')[-1])
                
            # Get the event with related data
            event = get_object_or_404(
                FootballEvent.objects.select_related(
                    'league', 'home_team', 'away_team', 'home_team_stats', 'away_team_stats'
                ).prefetch_related(
                    'key_events', 'detailed_stats'
                ),
                id=event_id
            )
            
            # Serialize the event
            serializer = FootballEventSerializer(event)
            return Response(serializer.data)
            
        except ValueError:
            return Response(
                {'error': 'Invalid event ID format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error in FootballEventDetail view: {str(e)}")
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(csrf_exempt, name='dispatch')
class FetchFootballEventsView(APIView):
    """View for fetching and storing football events."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            # Import the command class
            from core.management.commands.populate_football import Command
            # Create an instance and run the command
            Command().fetch_and_store_football_events()
            return Response({'success': True, 'message': 'Football events fetched and stored'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Error fetching football events: %s", str(e))
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 