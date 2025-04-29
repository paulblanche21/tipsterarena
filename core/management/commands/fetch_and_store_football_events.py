from django.core.management.base import BaseCommand
from core.views import fetch_and_store_football_events
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fetch and store football events from ESPN API'

    def handle(self, *args, **options):
        try:
            logger.info("Starting football events fetch and store process")
            fetch_and_store_football_events()
            logger.info("Football events fetch and store process completed successfully")
            self.stdout.write(self.style.SUCCESS('Successfully fetched and stored football events'))
        except Exception as e:
            logger.error(f"Error in football events fetch and store process: {str(e)}")
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}')) 