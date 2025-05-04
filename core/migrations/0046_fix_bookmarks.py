from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0045_fix_golfevent_tournament'),
    ]

    operations = [
        migrations.RunSQL(
            """
            DO $$
            BEGIN
                -- Drop the table if it exists
                DROP TABLE IF EXISTS core_tip_bookmarks;
                
                -- Create the table
                CREATE TABLE core_tip_bookmarks (
                    id SERIAL PRIMARY KEY,
                    tip_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    UNIQUE (tip_id, user_id)
                );

                -- Add foreign key constraints if the referenced tables exist
                IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'core_tip') THEN
                    ALTER TABLE core_tip_bookmarks
                    ADD CONSTRAINT core_tip_bookmarks_tip_id_fkey
                    FOREIGN KEY (tip_id) REFERENCES core_tip(id) ON DELETE CASCADE;
                END IF;

                IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'auth_user') THEN
                    ALTER TABLE core_tip_bookmarks
                    ADD CONSTRAINT core_tip_bookmarks_user_id_fkey
                    FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE;
                END IF;
            END;
            $$;
            """,
            "DROP TABLE IF EXISTS core_tip_bookmarks;"
        ),
    ] 