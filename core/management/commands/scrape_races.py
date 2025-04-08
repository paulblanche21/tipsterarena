# horse_racing_scraper.py

from django.core.management.base import BaseCommand
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from core.models import RaceMeeting, Race, RaceResult

BASE_URL = "https://www.irishracing.com"

class Command(BaseCommand):
    help = 'Scrape race meetings, race details, and results for Ireland and UK from Irish Racing using Selenium'

    def fetch_page(self, url):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)
            driver.implicitly_wait(5)
            return driver
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error fetching {url} with Selenium: {e}"))
            return None

    def scrape_meetings_from_tab(self, driver, tab_id):
        driver.execute_script(f"document.querySelector('#{tab_id}').click();")
        driver.implicitly_wait(5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        meetings = []
        fixture_container = soup.find('div', id=tab_id)
        if not fixture_container:
            self.stdout.write(self.style.WARNING(f"Tab container (#{tab_id}) not found."))
            return meetings

        self.stdout.write(f"Found #{tab_id}: {len(str(fixture_container))} characters")

        fixture_rows = fixture_container.find_all('div', class_='fixrow')
        if not fixture_rows:
            self.stdout.write(self.style.WARNING(f"No 'fixrow' rows found in #{tab_id}. Trying alternative..."))
            fixture_rows = [row for row in fixture_container.find_all('div', class_='row')
                           if row.find('a', href=lambda href: href and '/fixture/' in href)]

        self.stdout.write(f"Found {len(fixture_rows)} fixture rows in #{tab_id}")

        for row in fixture_rows:
            link_elem = row.find('a', href=True)
            if link_elem and '/fixture/' in link_elem['href']:
                meeting_url = BASE_URL + link_elem['href'] if link_elem['href'].startswith('/') else link_elem['href']
                
                date_elem = row.find('div', class_='col-xs-4')
                venue_elem = row.find('div', class_='racename')
                
                if date_elem and venue_elem:
                    date_str = date_elem.text.strip()
                    venue = venue_elem.text.split()[0].strip()
                else:
                    url_parts = link_elem['href'].split('/')
                    date_str = url_parts[-2].replace('-', ' ')
                    venue_elem = row.find('div', class_='racename') or row.find('div', class_='col-xs-offset-4')
                    venue = venue_elem.text.split()[0].strip() if venue_elem else url_parts[-1].replace('-', ' ')
                
                for suffix in ['st', 'nd', 'rd', 'th']:
                    date_str = date_str.replace(suffix, '')
                date_parts = date_str.split()
                day = date_parts[1].zfill(2)
                date_str = f"{date_parts[0]} {day} {date_parts[2]} 2025"
                
                try:
                    meeting_date = datetime.strptime(date_str, '%a %d %b %Y').date()
                except ValueError as e:
                    self.stdout.write(self.style.WARNING(f"Date parsing error for {date_str}: {e}"))
                    continue

                today = datetime.now().date()
                seven_days_later = today + timedelta(days=7)
                if today <= meeting_date <= seven_days_later:
                    self.stdout.write(f"Saving - URL: {meeting_url}, Date: {date_str}, Venue: {venue}")
                    meeting, created = RaceMeeting.objects.get_or_create(
                        url=meeting_url,
                        defaults={'date': meeting_date, 'venue': venue}
                    )
                    if not created:
                        meeting.date = meeting_date
                        meeting.venue = venue
                        meeting.save()
                    meetings.append(meeting)
                else:
                    self.stdout.write(f"Skipping - URL: {meeting_url}, Date: {date_str} (outside 7-day window)")
        
        return meetings

    def scrape_race_details(self, meeting):
        """Scrape race times and horses for a given meeting."""
        driver = self.fetch_page(meeting.url)
        if not driver:
            return

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        race_rows = soup.find_all('div', class_='race-row')

        if not race_rows:
            self.stdout.write(self.style.WARNING(f"No races found for meeting at {meeting.url}"))
            driver.quit()
            return

        for row in race_rows:
            time_elem = row.find('div', class_='race-time')
            race_name_elem = row.find('a', class_='race-name')
            horses_container = row.find('div', class_='racecard-horses')

            if not time_elem or not race_name_elem:
                self.stdout.write(self.style.WARNING(f"Missing time or name for race in {meeting.venue}"))
                continue

            race_time_str = time_elem.text.strip()
            try:
                race_time = datetime.strptime(race_time_str, '%H:%M').time()
            except ValueError as e:
                self.stdout.write(self.style.WARNING(f"Time parsing error for {race_time_str}: {e}"))
                continue

            race_name = race_name_elem.text.strip()
            horses = []

            if horses_container:
                horse_elems = horses_container.find_all('div', class_='horse')
                for idx, horse_elem in enumerate(horse_elems, 1):
                    horse_name = horse_elem.find('a', class_='horse-name')
                    if horse_name:
                        horses.append({"number": idx, "name": horse_name.text.strip()})
            else:
                self.stdout.write(self.style.WARNING(f"No horses found for race at {race_time} in {meeting.venue}"))

            # Save race details
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

        driver.quit()

    def scrape_race_results(self, meeting):
        """Scrape results (winner and placed horses) for a given meeting if the races have finished."""
        today = datetime.now().date()
        if meeting.date > today:
            self.stdout.write(f"Skipping results for {meeting.venue} on {meeting.date} (future meeting)")
            return

        driver = self.fetch_page(meeting.url)
        if not driver:
            return

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        race_rows = soup.find_all('div', class_='race-row')

        for row in race_rows:
            time_elem = row.find('div', class_='race-time')
            result_elem = row.find('div', class_='race-result')

            if not time_elem or not result_elem:
                self.stdout.write(self.style.WARNING(f"Missing time or result for race in {meeting.venue}"))
                continue

            race_time_str = time_elem.text.strip()
            try:
                race_time = datetime.strptime(race_time_str, '%H:%M').time()
            except ValueError:
                self.stdout.write(self.style.WARNING(f"Time parsing error for {race_time_str}"))
                continue

            race = Race.objects.filter(meeting=meeting, race_time=race_time).first()
            if not race:
                self.stdout.write(self.style.WARNING(f"Race at {race_time} not found for {meeting.venue}"))
                continue

            # Clear existing results for this race
            RaceResult.objects.filter(race=race).delete()

            winner = ""
            placed_horses = []
            result_text = result_elem.text.strip()
            if "1st" in result_text.lower():
                winner_elem = result_elem.find('a', class_='winner')
                if winner_elem:
                    winner = winner_elem.text.strip()
                else:
                    self.stdout.write(self.style.WARNING(f"No winner found for race at {race_time} in {meeting.venue}"))

                placed_elems = result_elem.find_all('a', class_='placed')
                for idx, placed_elem in enumerate(placed_elems, 2):
                    placed_horses.append({"position": idx, "name": placed_elem.text.strip()})
            else:
                self.stdout.write(self.style.WARNING(f"No '1st' found in result text for race at {race_time} in {meeting.venue}"))

            # Save race result
            result, created = RaceResult.objects.get_or_create(
                race=race,
                defaults={'winner': winner, 'placed_horses': placed_horses}
            )
            if not created:
                result.winner = winner
                result.placed_horses = placed_horses
                result.save()

            self.stdout.write(f"Saved result for race at {race_time}: Winner - {winner}, Placed - {placed_horses}")

        driver.quit()

    def scrape_upcoming_meetings(self):
        url = f"{BASE_URL}/fixtures"
        driver = self.fetch_page(url)
        if not driver:
            return []

        today = datetime.now().date()
        seven_days_later = today + timedelta(days=7)
        self.stdout.write(f"Scraping meetings from {today} to {seven_days_later}")

        past_meetings = RaceMeeting.objects.filter(date__lt=today)
        deleted_results = RaceResult.objects.filter(race__meeting__in=past_meetings).delete()[0]
        deleted_races = Race.objects.filter(meeting__in=past_meetings).delete()[0]
        deleted_meetings = past_meetings.delete()[0]
        self.stdout.write(f"Deleted {deleted_meetings} past meetings, {deleted_races} races, and {deleted_results} results")

        ireland_meetings = self.scrape_meetings_from_tab(driver, 'tab-ire')
        uk_meetings = self.scrape_meetings_from_tab(driver, 'tab-gb')

        driver.quit()

        meetings = ireland_meetings + uk_meetings
        if not meetings:
            self.stdout.write(self.style.WARNING("No meetings found within the next 7 days."))
        return meetings

    def handle(self, *args, **options):
        self.stdout.write("Scraping upcoming race meetings from Irish Racing...")
        meetings = self.scrape_upcoming_meetings()
        
        if not meetings:
            self.stdout.write(self.style.WARNING("No upcoming meetings found for the next 7 days."))
            return

        # Scrape race details and results for each meeting
        for meeting in meetings:
            self.stdout.write(f"Scraping race details for {meeting.venue} on {meeting.date}")
            self.scrape_race_details(meeting)
            self.stdout.write(f"Scraping race results for {meeting.venue} on {meeting.date}")
            self.scrape_race_results(meeting)

        self.stdout.write(self.style.SUCCESS(f"Scraped {len(meetings)} meetings successfully!"))