# Generated by Django 5.1.7 on 2025-04-08 22:04

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0023_remove_tip_stake_tip_confidence"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="raceresult",
            name="horse",
        ),
        migrations.RemoveField(
            model_name="raceresult",
            name="jockey",
        ),
        migrations.RemoveField(
            model_name="raceresult",
            name="meeting",
        ),
        migrations.RemoveField(
            model_name="raceresult",
            name="name",
        ),
        migrations.RemoveField(
            model_name="raceresult",
            name="position",
        ),
        migrations.RemoveField(
            model_name="raceresult",
            name="time",
        ),
        migrations.AddField(
            model_name="raceresult",
            name="placed_horses",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="raceresult",
            name="winner",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.CreateModel(
            name="Race",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("race_time", models.TimeField()),
                ("name", models.CharField(blank=True, max_length=200)),
                ("horses", models.JSONField()),
                (
                    "meeting",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="races",
                        to="core.racemeeting",
                    ),
                ),
            ],
            options={
                "unique_together": {("meeting", "race_time")},
            },
        ),
        migrations.AddField(
            model_name="raceresult",
            name="race",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="results",
                to="core.race",
            ),
        ),
    ]
