"""Views for handling horse racing events in Tipster Arena."""

import logging
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes, authentication_classes, throttle_classes
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError


from ..models import (
    HorseRacingMeeting, HorseRacingBettingOdds, HorseRacingRace
)
from ..serializers import (
    HorseRacingMeetingSerializer, HorseRacingBettingOddsSerializer,
    HorseRacingRaceSerializer
)
from ..horse_racing_events import get_racecards_json

logger = logging.getLogger(__name__)

def validate_date_param(date_str):
    """Validate date parameter format."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise ValidationError('Invalid date format. Use YYYY-MM-DD')

def horse_racing_fixtures(request):
    """Return upcoming horse racing fixtures."""
    today = datetime.now().date()
    meetings = HorseRacingMeeting.objects.filter(date__gte=today).order_by('date')

    fixtures = [
        {
            'venue': meeting.venue,
            'date': meeting.date.isoformat(),
            'displayDate': meeting.date.strftime('%b %d, %Y'),
            'url': meeting.url
        }
        for meeting in meetings
    ]

    return JsonResponse({'fixtures': fixtures})

def racecards_json_view(request):
    """Return JSON data for horse racing racecards."""
    try:
        logger.debug("Entering racecards_json_view")
        data = get_racecards_json()
        logger.info("Returning racecards data: %s meetings", len(data))
        logger.debug("Sample data: %s", data[0] if data else 'Empty')
        return JsonResponse(data, safe=False)
    except Exception as e:
        logger.error("Error in racecards_json_view: %s", str(e), exc_info=True)
        return JsonResponse([], safe=False)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
@throttle_classes([UserRateThrottle, AnonRateThrottle])
def horse_racing_events(request):
    """Get a list of horse racing events."""
    # Get query parameters
    date = request.query_params.get('date')
    course_id = request.query_params.get('course_id')

    # Validate parameters
    if date:
        date = validate_date_param(date)

    # Build query
    queryset = HorseRacingMeeting.objects.all()
    if date:
        queryset = queryset.filter(date__date=date)
    if course_id:
        queryset = queryset.filter(course__id=course_id)

    # Order by date and course
    queryset = queryset.order_by('date', 'course__name')

    # Serialize data
    serializer = HorseRacingMeetingSerializer(queryset, many=True)
    return Response(serializer.data)

class HorseRacingMeetingDetail(APIView):
    """API endpoint for retrieving a single horse racing meeting."""
    authentication_classes = []
    permission_classes = []
    throttle_classes = [UserRateThrottle, AnonRateThrottle]
    
    def get(self, request, meeting_id):
        """Get a single horse racing meeting by ID."""
        try:
            # Extract numeric ID if string ID is provided
            if isinstance(meeting_id, str) and meeting_id.startswith('horse_racing_meeting_'):
                meeting_id = int(meeting_id.split('_')[-1])
                
            # Get the meeting with related data
            meeting = get_object_or_404(
                HorseRacingMeeting.objects.select_related(
                    'course'
                ).prefetch_related(
                    'races',
                    'races__runners',
                    'races__runners__horse',
                    'races__runners__jockey',
                    'races__runners__trainer',
                    'races__results',
                    'races__results__horse',
                    'races__results__jockey',
                    'races__results__trainer'
                ),
                id=meeting_id
            )
            
            # Serialize the meeting
            serializer = HorseRacingMeetingSerializer(meeting)
            return Response(serializer.data)
            
        except ValueError:
            return Response(
                {'error': 'Invalid meeting ID format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error in HorseRacingMeetingDetail view: {str(e)}")
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class HorseRacingBettingOddsBulkUpsert(APIView):
    """API endpoint for bulk upserting horse racing betting odds."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle, AnonRateThrottle]
    
    def post(self, request):
        """Bulk upsert horse racing betting odds."""
        try:
            # Get the data
            data = request.data
            if not isinstance(data, list):
                return Response(
                    {'error': 'Data must be a list of odds'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Upsert the odds
            upserted_odds = []
            for odds_data in data:
                odds_id = odds_data.get('id')
                if not odds_id:
                    # Create new odds
                    serializer = HorseRacingBettingOddsSerializer(data=odds_data)
                    if serializer.is_valid():
                        serializer.save()
                        upserted_odds.append(serializer.data)
                else:
                    # Extract numeric ID if string ID is provided
                    if isinstance(odds_id, str) and odds_id.startswith('horse_racing_betting_odds_'):
                        odds_id = int(odds_id.split('_')[-1])
                    
                    # Update existing odds
                    try:
                        odds = HorseRacingBettingOdds.objects.get(id=odds_id)
                        serializer = HorseRacingBettingOddsSerializer(odds, data=odds_data, partial=True)
                        if serializer.is_valid():
                            serializer.save()
                            upserted_odds.append(serializer.data)
                    except HorseRacingBettingOdds.DoesNotExist:
                        # If odds doesn't exist, create new one
                        serializer = HorseRacingBettingOddsSerializer(data=odds_data)
                        if serializer.is_valid():
                            serializer.save()
                            upserted_odds.append(serializer.data)
                            
            return Response(upserted_odds)
            
        except ValueError:
            return Response(
                {'error': 'Invalid odds ID format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error in HorseRacingBettingOddsBulkUpsert view: {str(e)}")
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class RaceMeetingList(APIView):
    """API endpoint for retrieving a list of horse racing meetings."""
    authentication_classes = []
    permission_classes = []
    throttle_classes = [UserRateThrottle, AnonRateThrottle]
    
    def get(self, request):
        """Get a list of horse racing meetings."""
        try:
            # Get query parameters
            date = request.query_params.get('date')
            course_id = request.query_params.get('course_id')
            
            # Validate parameters
            if date:
                date = validate_date_param(date)
            
            # Build query
            queryset = HorseRacingMeeting.objects.all()
            if date:
                queryset = queryset.filter(date__date=date)
            if course_id:
                queryset = queryset.filter(course__id=course_id)
            
            # Order by date and course
            queryset = queryset.order_by('date', 'course__name')
            
            # Serialize data
            serializer = HorseRacingMeetingSerializer(queryset, many=True)
            return Response(serializer.data)
            
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error in RaceMeetingList view: {str(e)}")
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class HorseRacingRacesList(APIView):
    """API endpoint for retrieving a list of horse racing races."""
    authentication_classes = []
    permission_classes = []
    throttle_classes = [UserRateThrottle, AnonRateThrottle]
    
    def get(self, request):
        """Get a list of horse racing races."""
        try:
            # Get query parameters
            meeting_id = request.query_params.get('meeting_id')
            date = request.query_params.get('date')
            course_id = request.query_params.get('course_id')
            
            # Validate parameters
            if date:
                date = validate_date_param(date)
            
            # Build query
            queryset = HorseRacingRace.objects.select_related(
                'meeting', 'meeting__course'
            ).prefetch_related(
                'runners',
                'runners__horse',
                'runners__jockey',
                'runners__trainer',
                'results',
                'results__horse',
                'results__jockey',
                'results__trainer'
            )
            
            # Apply filters
            if meeting_id:
                queryset = queryset.filter(meeting_id=meeting_id)
            if date:
                queryset = queryset.filter(meeting__date__date=date)
            if course_id:
                queryset = queryset.filter(meeting__course__id=course_id)
            
            # Order by meeting date and race time
            queryset = queryset.order_by('meeting__date', 'scheduled_time')
            
            # Serialize data
            serializer = HorseRacingRaceSerializer(queryset, many=True)
            return Response(serializer.data)
            
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error in HorseRacingRacesList view: {str(e)}")
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class HorseRacingRaceDetail(APIView):
    """API endpoint for retrieving a single horse racing race."""
    authentication_classes = []
    permission_classes = []
    throttle_classes = [UserRateThrottle, AnonRateThrottle]
    
    def get(self, request, race_id):
        """Get a single horse racing race by ID."""
        try:
            # Extract numeric ID if string ID is provided
            if isinstance(race_id, str) and race_id.startswith('horse_racing_race_'):
                race_id = int(race_id.split('_')[-1])
                
            # Get the race with related data
            race = get_object_or_404(
                HorseRacingRace.objects.select_related(
                    'meeting', 'meeting__course'
                ).prefetch_related(
                    'runners',
                    'runners__horse',
                    'runners__jockey',
                    'runners__trainer',
                    'results',
                    'results__horse',
                    'results__jockey',
                    'results__trainer'
                ),
                id=race_id
            )
            
            # Serialize the race
            serializer = HorseRacingRaceSerializer(race)
            return Response(serializer.data)
            
        except ValueError:
            return Response(
                {'error': 'Invalid race ID format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error in HorseRacingRaceDetail view: {str(e)}")
            return Response(
                {'error': 'Internal server error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 