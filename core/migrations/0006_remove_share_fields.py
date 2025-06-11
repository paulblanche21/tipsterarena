from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_message_is_read'),
    ]

    operations = [
        migrations.RunSQL(
            # Forward SQL
            """
            ALTER TABLE core_tip DROP COLUMN IF EXISTS is_share;
            ALTER TABLE core_tip DROP COLUMN IF EXISTS original_tip_id;
            """,
            # Reverse SQL
            """
            ALTER TABLE core_tip ADD COLUMN is_share boolean DEFAULT false;
            ALTER TABLE core_tip ADD COLUMN original_tip_id integer NULL;
            """
        ),
    ] 