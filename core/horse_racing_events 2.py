from datetime import datetime, timedelta
from core.models import RaceMeeting
from django.http import JsonResponse

def get_racecards_json():
    """Fetch racecards as JSON for past and upcoming meetings."""
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)  # Include yesterday
    three_days_later = today + timedelta(days=3)
    meetings = RaceMeeting.objects.filter(
        date__gte=yesterday,  # From yesterday
        date__lte=three_days_later  # To 3 days ahead
    ).order_by('date', 'venue')
    
    meetings_data = [
        {
            "venue": meeting.venue,
            "date": meeting.date.isoformat(),  # e.g., "2025-04-09"
            "races": [
                {
                    "race_time": race.race_time.strftime('%H:%M'),  # e.g., "14:30"
                    "name": race.name or "Unnamed Race",
                    "horses": race.horses if race.horses else [],  # List of horse dictionaries
                    "result": {
                        "winner": result.winner,
                        "placed_horses": result.placed_horses
                    } if (result := race.results.first()) else None
                } for race in meeting.races.all().order_by('race_time')
            ]
        } for meeting in meetings
    ]
    return meetings_data