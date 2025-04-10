from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
import requests
from core.models import RaceMeeting, Race, RaceResult

BASE_URL = "https://www.irishracing.com"
API_ENDPOINT = f"{BASE_URL}/raceresults?prf=reshdr"

class Command(BaseCommand):
    help = 'Scrape race meetings and details from Irish Racing API'

    def scrape_meetings_and_races(self):
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        test_date = datetime(2025, 4, 9).date()  # Test with known data
        self.stdout.write(f"Scraping meetings from {today} to {tomorrow}, plus test date {test_date}")

        # Clear past meetings
        past_meetings = RaceMeeting.objects.filter(date__lt=today)
        deleted_results = RaceResult.objects.filter(race__meeting__in=past_meetings).delete()[0]
        deleted_races = Race.objects.filter(meeting__in=past_meetings).delete()[0]
        deleted_meetings = past_meetings.delete()[0]
        self.stdout.write(f"Deleted {deleted_meetings} past meetings, {deleted_races} races, and {deleted_results} results")

        meetings = []
        dates_to_scrape = [test_date, today, tomorrow]
        for date in dates_to_scrape:
            prd = f"{date.strftime('%Y%m%d')}0000"  # e.g., "202504090000"
            url = f"{API_ENDPOINT}&prd={prd}"
            self.stdout.write(f"Fetching API data for {prd}: {url}")

            try:
                response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                response.raise_for_status()
                data = response.json()
                self.stdout.write(f"API response for {prd}: {str(data)[:500]}...")
                if data.get("status") != "OK":
                    self.stdout.write(self.style.WARNING(f"API returned non-OK status for {prd}: {data.get('reason')}"))
                    continue
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error fetching API data for {prd}: {e}"))
                continue

            for meeting_data in data.get("meetings", []):
                meeting_date = datetime.strptime(meeting_data["date"], '%Y-%m-%d %H:%M:%S').date()
                venue = meeting_data["coursename"]
                meeting_url = f"{BASE_URL}/racecards/{meeting_date.strftime('%a-%d-%b-%Y').replace(' ', '-')}/{venue.replace(' ', '-')}"
                
                self.stdout.write(f"Processing - URL: {meeting_url}, Date: {meeting_date}, Venue: {venue}")
                try:
                    meeting, created = RaceMeeting.objects.get_or_create(
                        date=meeting_date,
                        venue=venue,
                        defaults={'url': meeting_url}
                    )
                    if created:
                        self.stdout.write(f"Created new meeting: {venue} on {meeting_date}")
                    else:
                        if meeting.url != meeting_url:
                            meeting.url = meeting_url
                            meeting.save()
                            self.stdout.write(f"Updated URL for existing meeting: {venue} on {meeting_date}")
                        else:
                            self.stdout.write(f"Meeting already exists: {venue} on {meeting_date}")
                    meetings.append(meeting)

                    # Process races
                    for race_data in meeting_data.get("races", []):
                        race_time_str = race_data["time"].strip().replace('.', ':')
                        try:
                            # Convert to 24-hour format, assuming PM for times >= 1:00 PM
                            race_time = datetime.strptime(race_time_str, '%H:%M').time()
                            hour = race_time.hour
                            if 1 <= hour <= 11:  # Assume PM for afternoon races
                                race_time = (datetime.combine(datetime.today(), race_time) + timedelta(hours=12)).time()
                        except ValueError as e:
                            self.stdout.write(self.style.WARNING(f"Time parsing error for {race_time_str}: {e}"))
                            continue

                        race_name = race_data["name"]
                        horses = [
                            {
                                "number": int(winner["s"]),
                                "name": winner["h"],
                                "jockey": "Unknown",
                                "odds": winner["sp"],
                                "trainer": "Unknown",
                                "owner": "Unknown"
                            } for winner in race_data.get("wnrs", [])
                        ]

                        race, created = Race.objects.get_or_create(
                            meeting=meeting,
                            race_time=race_time,
                            defaults={'name': race_name, 'horses': horses}
                        )
                        if not created:
                            race.name = race_name
                            race.horses = horses
                            race.save()
                        self.stdout.write(f"Saved race: {race_name} at {race_time} with {len(horses)} horses")

                        # Process results
                        if race_data["racestatus"] == "Result":
                            winner = horses[0]["name"] if horses else ""
                            placed_horses = [
                                {"position": idx + 2, "name": horse["name"]}
                                for idx, horse in enumerate(horses[1:])
                            ]
                            result, created = RaceResult.objects.get_or_create(
                                race=race,
                                defaults={'winner': winner, 'placed_horses': placed_horses}
                            )
                            if not created:
                                result.winner = winner
                                result.placed_horses = placed_horses
                                result.save()
                            self.stdout.write(f"Saved result for race at {race_time}: Winner - {winner}, Placed - {placed_horses}")

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing meeting {venue} on {meeting_date}: {e}"))

        return meetings

    def handle(self, *args, **options):
        self.stdout.write("Scraping upcoming race meetings from Irish Racing API...")
        
        meetings = self.scrape_meetings_and_races()
        if not meetings:
            self.stdout.write(self.style.WARNING("No meetings found in the scraped dates."))
            return
        
        self.stdout.write(self.style.SUCCESS(f"Scraped {len(meetings)} meetings successfully!"))