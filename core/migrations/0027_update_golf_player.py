from django.db import migrations, models

def delete_players_with_null_ids(apps, schema_editor):
    GolfPlayer = apps.get_model('core', 'GolfPlayer')
    LeaderboardEntry = apps.get_model('core', 'LeaderboardEntry')
    
    # Delete leaderboard entries for players with null player_ids
    LeaderboardEntry.objects.filter(player__player_id__isnull=True).delete()
    
    # Delete players with null player_ids
    GolfPlayer.objects.filter(player_id__isnull=True).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0026_golfcourse_golfplayer_golftour_golfevent_and_more'),
    ]

    operations = [
        migrations.RunPython(delete_players_with_null_ids),
        migrations.AlterField(
            model_name='golfplayer',
            name='player_id',
            field=models.CharField(max_length=50, unique=True),
        ),
    ] 