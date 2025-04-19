from django.db import migrations, models

def populate_handles(apps, schema_editor):
    UserProfile = apps.get_model('core', 'UserProfile')
    User = apps.get_model('auth', 'User')
    for profile in UserProfile.objects.all():
        if not profile.handle:
            profile.handle = f"@{profile.user.username}"
            profile.save()

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0006_tip_audience'),  # Replace with your last migration
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='handle',
            field=models.CharField(
                blank=True,
                help_text='Your unique handle starting with @ (e.g., @username)',
                max_length=15,
                null=True,  # Allow null initially
                unique=True,
            ),
        ),
        migrations.RunPython(populate_handles),  # Populate handles for existing records
    ]