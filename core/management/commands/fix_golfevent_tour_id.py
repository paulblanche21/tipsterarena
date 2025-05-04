from django.core.management.base import BaseCommand
from core.models import GolfEvent, GolfTour

class Command(BaseCommand):
    help = 'Fixes null tour_id values in GolfEvent table by setting them to a default tour'

    def handle(self, *args, **options):
        # Get or create a default tour
        default_tour, created = GolfTour.objects.get_or_create(
            tour_id='default',
            defaults={
                'name': 'Default Tour',
                'icon': '🏌️',
                'priority': 999
            }
        )

        # Count null tour_id values
        null_count = GolfEvent.objects.filter(tour_id__isnull=True).count()
        self.stdout.write(f'Found {null_count} GolfEvent records with null tour_id')

        if null_count > 0:
            # Update null tour_id values to the default tour
            updated = GolfEvent.objects.filter(tour_id__isnull=True).update(tour=default_tour)
            self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated} records'))
        else:
            self.stdout.write(self.style.SUCCESS('No null tour_id values found')) 