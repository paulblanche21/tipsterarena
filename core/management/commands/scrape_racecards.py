# core/management/commands/scrape_racecards.py
from django.core.management.base import BaseCommand
from core.management.commands.rpscrape.scripts.racecards import scrape_racecards

class Command(BaseCommand):
    help = 'Scrape horse racing racecards for today or tomorrow'

    def add_arguments(self, parser):
        parser.add_argument(
            'day',
            choices=['today', 'tomorrow'],
            help='Scrape racecards for today or tomorrow'
        )

    def handle(self, *args, **options):
        day = options['day']
        try:
            scrape_racecards(day)
            self.stdout.write(self.style.SUCCESS(f"Successfully scraped racecards for {day}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error scraping racecards: {str(e)}"))