from django.db import migrations, models
import django.db.models.deletion

def fix_tournament_ids(apps, schema_editor):
    GolfEvent = apps.get_model('core', 'GolfEvent')
    GolfTour = apps.get_model('core', 'GolfTour')
    GolfTournament = apps.get_model('core', 'GolfTournament')
    
    # Get or create default tour
    default_tour, created = GolfTour.objects.get_or_create(
        tour_id='default',
        defaults={
            'name': 'Default Tour',
            'icon': '🏌️',
            'priority': 999
        }
    )
    
    # Get or create default tournament
    default_tournament, created = GolfTournament.objects.get_or_create(
        tournament_id='default',
        defaults={
            'name': 'Default Tournament',
            'description': 'Default tournament for existing events',
            'prize_fund': '1000000',
            'tour': default_tour,
            'is_major': False
        }
    )
    
    # Update events with null tournament_id
    GolfEvent.objects.filter(tournament__isnull=True).update(tournament=default_tournament)

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0044_remove_golfevent_tour_golfround_golftournament_and_more'),
    ]

    operations = [
        # First, make the field nullable
        migrations.AlterField(
            model_name='golfevent',
            name='tournament',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='events',
                to='core.golftournament'
            ),
        ),
        # Run the data fix
        migrations.RunPython(fix_tournament_ids),
        # Then make it non-nullable again
        migrations.AlterField(
            model_name='golfevent',
            name='tournament',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='events',
                to='core.golftournament'
            ),
        ),
    ] 