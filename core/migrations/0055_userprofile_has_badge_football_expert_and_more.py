# Generated by Django 5.2 on 2025-05-06 22:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0054_remove_tip_required_tier_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='has_badge_football_expert',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='has_badge_high_odds_win',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='has_badge_horse_expert',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='has_badge_tips_10',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='has_badge_tips_100',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='has_badge_tips_50',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='has_badge_win_rate_60',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='has_badge_win_rate_75',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='has_badge_winning_streak_3',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='has_badge_winning_streak_5',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='description',
            field=models.TextField(blank=True, max_length=160),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='handle',
            field=models.CharField(max_length=15, unique=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='location',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='stripe_customer_id',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='total_subscribers',
            field=models.IntegerField(default=0),
        ),
    ]
