# core/horse_racing_events.py

from datetime import datetime, timedelta
from core.models import RaceMeeting
import logging

logger = logging.getLogger(__name__)

def format_racecard_list(meetings):
    if not meetings:
        return "<p>No upcoming horse racing meetings available.</p>"

    event_html = '<div class="racecard-feed">'
    for meeting in meetings:
        races = meeting.races.all().order_by('race_time')
        if not races:
            continue

        # Meeting header
        event_html += f"""
        <div class="meeting-card">
          <div class="card-header">
            <div class="meeting-info">
              <span class="meeting-name">{meeting.venue} - {meeting.date.strftime('%a %d %b %Y')}</span>
            </div>
          </div>
          <div class="card-content">
        """

        # List races
        for race in races:
            # Format horses with jockeys, odds, trainers, and owners
            horses_list = "".join([
                f"<li>{horse['number']}. {horse['name']} (Jockey: {horse.get('jockey', 'Unknown')}, Odds: {horse.get('odds', 'N/A')}, Trainer: {horse.get('trainer', 'Unknown')}, Owner: {horse.get('owner', 'Unknown')})</li>"
                for horse in race.horses
            ]) if race.horses else "<li>No horses available.</li>"

            # Format results
            result = race.results.first()
            result_content = ""
            if result and result.winner:
                placed_horses = "".join([
                    f"<li>{horse['position']}nd: {horse['name']}</li>"
                    for horse in result.placed_horses
                ]) if result.placed_horses else ""
                result_content = f"""
                <div class="race-result">
                  <p><strong>Winner:</strong> {result.winner}</p>
                  {placed_horses}
                </div>
                """

            event_html += f"""
            <div class="race-details">
              <p><strong>Race Time:</strong> {race.race_time.strftime('%H:%M')}</p>
              <p><strong>Race Name:</strong> {race.name or 'Unnamed Race'}</p>
              <div class="horses-list">
                <p><strong>Horses:</strong></p>
                <ul>{horses_list}</ul>
              </div>
              {result_content}
            </div>
            """

        event_html += """
          </div>
        </div>
        """

    event_html += '</div>'
    return event_html

def get_racecards():
    """Fetch and format racecards for upcoming meetings."""
    today = datetime.now().date()
    three_days_later = today + timedelta(days=3)
    meetings = RaceMeeting.objects.filter(
        date__gte=today,
        date__lte=three_days_later
    ).order_by('date', 'venue')
    return format_racecard_list(meetings)

def get_racecards_json():
    """
    Fetch horse racing racecards as JSON for the last 7 days, including completed races.
    Uses RaceMeeting model; extend with API if available.
    """
    try:
        # Placeholder for external API (e.g., Timeform, Racing Post)
        # Uncomment and configure with real endpoint and key if available
        """
        api_url = "https://api.racingpost.com/v1/racecards"
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            meetings = parse_api_data(data)
            logger.info(f"Fetched {len(meetings)} horse racing meetings from API")
            return meetings
        else:
            logger.warning(f"API request failed: {response.status_code}")
        """
        pass
    except Exception as e:
        logger.error(f"Error fetching racecards from API: {str(e)}")

    # Fallback to RaceMeeting model
    today = datetime.now().date()
    seven_days_ago = today - timedelta(days=7)
    meetings = RaceMeeting.objects.filter(
        date__gte=seven_days_ago,
        date__lte=today
    ).order_by('-date', 'venue')

    racecards = []
    for meeting in meetings:
        races = meeting.races.all().order_by('race_time')
        races_data = [
            {
                'race_time': race.race_time.strftime('%H:%M') if race.race_time else 'N/A',
                'name': race.name or 'Unnamed Race',
                'horses': race.horses or [],
                'result': {
                    'winner': result.winner,
                    'positions': result.placed_horses
                } if (result := race.results.first()) and result.winner else None
            }
            for race in races
        ]
        racecards.append({
            'date': meeting.date.isoformat(),
            'displayDate': meeting.date.strftime('%b %d, %Y'),
            'venue': meeting.venue,
            'races': races_data,
            'url': meeting.url or ''
        })

    logger.info(f"Fetched {len(racecards)} horse racing meetings from RaceMeeting model")
    return racecards

def parse_api_data(data):
    """
    Parse external API response into racecard format.
    Placeholder; customize based on actual API structure.
    """
    meetings = []
    # Example parsing (adjust for real API)
    for event in data.get('events', []):
        meeting = {
            'date': event.get('date', datetime.now().isoformat()),
            'displayDate': datetime.strptime(event.get('date', ''), '%Y-%m-%d').strftime('%b %d, %Y') if event.get('date') else datetime.now().strftime('%b %d, %Y'),
            'venue': event.get('venue', 'Unknown Venue'),
            'races': [
                {
                    'race_time': race.get('time', 'N/A'),
                    'name': race.get('name', 'Unnamed Race'),
                    'horses': race.get('horses', []),
                    'result': race.get('result', None)
                }
                for race in event.get('races', [])
            ],
            'url': event.get('url', '')
        }
        meetings.append(meeting)
    return meetings