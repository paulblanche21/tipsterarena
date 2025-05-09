# Generated by Django 5.1.7 on 2025-04-20 14:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_remove_raceresult_horse_remove_raceresult_jockey_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='FootballEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_id', models.CharField(max_length=50, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('date', models.DateTimeField()),
                ('state', models.CharField(choices=[('pre', 'Pre'), ('in', 'In Progress'), ('post', 'Post'), ('unknown', 'Unknown')], default='pre', max_length=20)),
                ('status_description', models.CharField(default='Unknown', max_length=100)),
                ('status_detail', models.CharField(default='N/A', max_length=100)),
                ('venue', models.CharField(default='Location TBD', max_length=200)),
                ('home_score', models.CharField(default='0', max_length=10)),
                ('away_score', models.CharField(default='0', max_length=10)),
                ('clock', models.CharField(blank=True, max_length=10, null=True)),
                ('period', models.PositiveIntegerField(default=0)),
                ('broadcast', models.CharField(default='N/A', max_length=100)),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='FootballLeague',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('league_id', models.CharField(max_length=50, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('icon', models.CharField(default='⚽', max_length=10)),
                ('priority', models.PositiveIntegerField(default=999)),
            ],
        ),
        migrations.CreateModel(
            name='FootballTeam',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('logo', models.URLField(blank=True, null=True)),
                ('form', models.CharField(blank=True, max_length=50, null=True)),
                ('record', models.CharField(blank=True, max_length=50, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='TeamStats',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('possession', models.CharField(default='N/A', max_length=10)),
                ('shots', models.CharField(default='N/A', max_length=10)),
                ('shots_on_target', models.CharField(default='N/A', max_length=10)),
                ('corners', models.CharField(default='N/A', max_length=10)),
                ('fouls', models.CharField(default='N/A', max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='DetailedStats',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('possession', models.CharField(default='N/A', max_length=50)),
                ('home_shots', models.CharField(default='N/A', max_length=10)),
                ('away_shots', models.CharField(default='N/A', max_length=10)),
                ('goals', models.JSONField(default=list)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detailed_stats', to='core.footballevent')),
            ],
        ),
        migrations.CreateModel(
            name='BettingOdds',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('home_odds', models.CharField(default='N/A', max_length=20)),
                ('away_odds', models.CharField(default='N/A', max_length=20)),
                ('draw_odds', models.CharField(default='N/A', max_length=20)),
                ('provider', models.CharField(default='Unknown Provider', max_length=100)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='odds', to='core.footballevent')),
            ],
        ),
        migrations.AddField(
            model_name='footballevent',
            name='league',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='core.footballleague'),
        ),
        migrations.AddField(
            model_name='footballevent',
            name='away_team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='away_events', to='core.footballteam'),
        ),
        migrations.AddField(
            model_name='footballevent',
            name='home_team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='home_events', to='core.footballteam'),
        ),
        migrations.CreateModel(
            name='KeyEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(default='Unknown', max_length=50)),
                ('time', models.CharField(default='N/A', max_length=10)),
                ('team', models.CharField(default='Unknown', max_length=100)),
                ('player', models.CharField(default='Unknown', max_length=100)),
                ('is_goal', models.BooleanField(default=False)),
                ('is_yellow_card', models.BooleanField(default=False)),
                ('is_red_card', models.BooleanField(default=False)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='key_events', to='core.footballevent')),
            ],
        ),
        migrations.AddField(
            model_name='footballevent',
            name='away_stats',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='away_stats', to='core.teamstats'),
        ),
        migrations.AddField(
            model_name='footballevent',
            name='home_stats',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='home_stats', to='core.teamstats'),
        ),
    ]
