# core/horse_racing_events.py

from datetime import datetime, timedelta
from core.models import RaceMeeting

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