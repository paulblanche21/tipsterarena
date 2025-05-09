# Generated by Django 5.2 on 2025-05-06 20:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0052_tip_visibility_userprofile_is_tipster_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='tipstersubscription',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterModelOptions(
            name='tipstertier',
            options={'ordering': ['price']},
        ),
        migrations.AddField(
            model_name='tipstersubscription',
            name='last_payment_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='tipstersubscription',
            name='next_payment_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='tipstersubscription',
            name='stripe_customer_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='tipstertier',
            name='is_popular',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='tipstertier',
            name='stripe_price_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='tipstersubscription',
            name='status',
            field=models.CharField(choices=[('active', 'Active'), ('cancelled', 'Cancelled'), ('expired', 'Expired'), ('past_due', 'Past Due'), ('incomplete', 'Incomplete'), ('incomplete_expired', 'Incomplete Expired')], default='incomplete', max_length=20),
        ),
    ]
