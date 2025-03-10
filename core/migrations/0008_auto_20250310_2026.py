from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0007_userprofile_handle'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='handle',
            field=models.CharField(
                max_length=15,
                unique=True,
                blank=True,
                help_text="Your unique handle starting with @ (e.g., @username)"
            ),
        ),
    ]