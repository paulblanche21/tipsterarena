import logging
from datetime import datetime, timedelta
from core.models import RaceMeeting, Race, RaceResult
from django.db import transaction
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def get_racecards_json():
    """
    Scrape horse racing racecards and results from Racing Post for the last 7 days.
    Falls back to RaceMeeting model if scraping fails.
    """
    today = datetime.now().date()
    seven_days_ago = today - timedelta(days=7)
    meetings = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })

            for i in range(8):
                date = today - timedelta(days=i)
                date_str = date.strftime('%Y-%m-%d')
                logger.debug(f"Scraping date: {date_str}")

                # Racecards
                racecard_url = f"https://www.racingpost.com/racecards/{date_str}"
                logger.debug(f"Fetching racecards: {racecard_url}")
                page.goto(racecard_url, wait_until="networkidle", timeout=60000)
                racecard_soup = BeautifulSoup(page.content(), 'html.parser')

                # Results
                result_url = f"https://www.racingpost.com/results/{date_str}"
                logger.debug(f"Fetching results: {result_url}")
                page.goto(result_url, wait_until="networkidle", timeout=60000)
                result_soup = BeautifulSoup(page.content(), 'html.parser')

                day_meetings = parse_racecard_page(racecard_soup, result_soup, date)
                logger.debug(f"Parsed {len(day_meetings)} meetings for {date_str}")
                meetings.extend(day_meetings)
                page.wait_for_timeout(2000)

            browser.close()

        logger.info(f"Scraped {len(meetings)} horse racing meetings from Racing Post")
        return meetings

    except Exception as e:
        logger.error(f"Error scraping Racing Post: {str(e)}")
        # Fallback to RaceMeeting model
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
                'url': f"https://www.racingpost.com/racecards/{meeting.date.strftime('%Y-%m-%d')}/{meeting.venue.lower().replace(' ', '-')}"
            })
        logger.info(f"Fallback: Fetched {len(racecards)} meetings from RaceMeeting model")
        return racecards

def parse_racecard_page(racecard_soup, result_soup, date):
    """
    Parse Racing Post racecard and results pages into frontend-compatible format.
    """
    meetings = []
    # Try racecard meeting sections
    meeting_sections = racecard_soup.select('div[class*="MeetingContainer"], div.rp-resultsBettingsOffer')
    logger.debug(f"Found {len(meeting_sections)} meeting sections in racecards")

    for section in meeting_sections:
        venue_elem = section.select_one('h3[class*="MeetingName"], h1[class*="CourseName"]')
        if not venue_elem:
            logger.warning("No venue element found in racecard section")
            continue
        venue = venue_elem.text.strip().split(' - ')[0].replace(' Results', '').strip()
        logger.debug(f"Processing venue: {venue}")

        races = []
        race_cards = section.select('div[class*="RaceCardContainer"], div.rp-raceCourse__panel__race__info')
        logger.debug(f"Found {len(race_cards)} race cards for {venue}")

        for race_card in race_cards:
            race_time_elem = race_card.select_one('span[class*="RaceTime"], span[data-test-selector="text-raceTime"]')
            race_name_elem = race_card.select_one('h4[class*="RaceName"], a.rp-raceCourse__panel__race__info__title__link > span')
            horses_list = race_card.select('div[class*="RunnerDetails"], ol.rp-raceCourse__panel__race__info__results li')
            race_id = race_card.get('data-diffusion-race-id', '')

            race_time = race_time_elem.text.strip() if race_time_elem else 'N/A'
            race_name = race_name_elem.text.strip() if race_name_elem else 'Unnamed Race'
            logger.debug(f"Race: {race_name} at {race_time}")

            horses = []
            for horse in horses_list:
                horse_data = {
                    'number': 'N/A',
                    'name': 'Unknown',
                    'jockey': 'Unknown',
                    'odds': 'N/A',
                    'trainer': 'Unknown',
                    'owner': 'Unknown'
                }
                # Try racecard selectors first
                number_elem = horse.select_one('span[class*="RunnerNumber"]')
                name_elem = horse.select_one('a[class*="RunnerName"]')
                jockey_elem = horse.select_one('span[class*="Jockey"]')
                odds_elem = horse.select_one('span[class*="Odds"]')
                trainer_elem = horse.select_one('span[class*="Trainer"]')
                owner_elem = horse.select_one('span[class*="Owner"]')
                # Fallback to results selectors
                if not name_elem:
                    name_elem = horse.select_one('div.rp-raceCourse__panel__race__info__results__name__table__row')
                    odds_elem = horse.select_one('div.rp-raceCourse__panel__race__info__results__name__table__price')
                    jockey_elem = horse.select_one('a[href*="/jockey"]')
                    trainer_elem = horse.select_one('a[href*="/trainer"]')
                    owner_elem = horse.select_one('a[href*="/owner"]')

                if name_elem:
                    horse_data['name'] = name_elem.text.strip().split('. ')[-1] if '. ' in name_elem.text else name_elem.text.strip()
                if number_elem:
                    horse_data['number'] = number_elem.text.strip()
                if jockey_elem:
                    horse_data['jockey'] = jockey_elem.text.strip()
                if odds_elem:
                    horse_data['odds'] = odds_elem.text.strip()
                if trainer_elem:
                    horse_data['trainer'] = trainer_elem.text.strip()
                if owner_elem:
                    horse_data['owner'] = owner_elem.text.strip()
                
                horses.append(horse_data)
            
            logger.debug(f"Parsed {len(horses)} horses for {race_name}")

            # Parse results
            result = None
            result_race = result_soup.select_one(f'div.rp-raceCourse__panel__race[data-diffusion-race-id="{race_id}"]') or \
                         result_soup.select_one(f'div.rp-raceCourse__panel__race[data-diffusion-racetime="{race_time.replace(":", ":")}"]')
            if result_race:
                results_list = result_race.select('ol.rp-raceCourse__panel__race__info__results li')
                logger.debug(f"Found {len(results_list)} result items")
                winner = None
                placed = []
                for idx, result_item in enumerate(results_list, 1):
                    horse_name_elem = result_item.select_one('div.rp-raceCourse__panel__race__info__results__name__table__row')
                    if not horse_name_elem:
                        continue
                    horse_name = horse_name_elem.text.strip().split('. ')[-1]
                    outcome = result_item.get('data-outcome-desc', '')
                    if outcome == '1st':
                        winner = horse_name
                    elif outcome in ('2nd', '3rd'):
                        placed.append({
                            'position': outcome.replace('nd', '').replace('rd', ''),
                            'name': horse_name
                        })
                if winner:
                    result = {'winner': winner, 'positions': placed}
                    logger.debug(f"Result: winner={winner}, placed={len(placed)}")

            races.append({
                'race_time': race_time,
                'name': race_name,
                'horses': horses,
                'result': result
            })

        meetings.append({
            'date': date.isoformat(),
            'displayDate': date.strftime('%b %d, %Y'),
            'venue': venue,
            'races': races,
            'url': f"https://www.racingpost.com/racecards/{date.strftime('%Y-%m-%d')}/{venue.lower().replace(' ', '-')}"
        })

    logger.debug(f"Returning {len(meetings)} meetings for {date}")
    return meetings