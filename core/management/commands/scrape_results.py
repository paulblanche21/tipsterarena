from django.core.management.base import BaseCommand
from core.management.commands.rpscrape.scripts.rpscrape import scrape_results
from datetime import datetime

class Command(BaseCommand):
    help = 'Scrape horse racing results for a specific race type and date'

    def add_arguments(self, parser):
        parser.add_argument(
            'race_type',
            choices=['flat', 'jumps'],
            help='Race type to scrape (flat or jumps)'
        )
        parser.add_argument(
            'date',
            help='Date to scrape in YYYY-MM-DD format (default: today)',
            nargs='?',
            default=datetime.now().strftime('%Y-%m-%d')
        )

    def handle(self, *args, **options):
        race_type = options['race_type']
        date = options['date']
        try:
            scrape_results(race_type, date)
            self.stdout.write(self.style.SUCCESS(f"Successfully scraped {race_type} results for {date}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error scraping results: {str(e)}"))