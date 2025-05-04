from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Creates the bookmarks table if it does not exist'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("""
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

                    -- Add foreign key constraints
                    ALTER TABLE core_tip_bookmarks
                    ADD CONSTRAINT core_tip_bookmarks_tip_id_fkey
                    FOREIGN KEY (tip_id) REFERENCES core_tip(id) ON DELETE CASCADE;

                    ALTER TABLE core_tip_bookmarks
                    ADD CONSTRAINT core_tip_bookmarks_user_id_fkey
                    FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE;
                END;
                $$;
            """)
            self.stdout.write(self.style.SUCCESS('Successfully created bookmarks table')) 