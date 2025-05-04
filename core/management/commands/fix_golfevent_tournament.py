from django.core.management.base import BaseCommand
from core.models import GolfEvent, GolfTour

class Command(BaseCommand):
    help = 'Fixes GolfEvent tournament relationships'

    def handle(self, *args, **options):
        # Get all GolfEvents without a tour
        events_without_tour = GolfEvent.objects.filter(tour__isnull=True)
        
        # Create a default tour if it doesn't exist
        default_tour, _ = GolfTour.objects.get_or_create(
            tour_id='default',
            defaults={
                'name': 'Default Tour',
                'icon': '🏌️‍♂️',
                'priority': 999
            }
        )
        
        # Update events without a tour
        count = events_without_tour.update(tour=default_tour)
        
        self.stdout.write(self.style.SUCCESS(f'Updated {count} GolfEvents with default tour')) 