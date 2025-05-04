from django.test.runner import DiscoverRunner
import psycopg2
import time
from django.conf import settings

class CustomTestRunner(DiscoverRunner):
    def _terminate_connections(self):
        """Terminate all connections to the test database"""
        db_name = settings.DATABASES['default']['TEST']['NAME']
        try:
            # Connect to postgres database to terminate connections
            conn = psycopg2.connect(
                dbname='postgres',
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                host=settings.DATABASES['default']['HOST'],
                port=settings.DATABASES['default']['PORT']
            )
            conn.autocommit = True
            with conn.cursor() as cursor:
                # First try to terminate connections gracefully
                cursor.execute("""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = %s
                    AND pid <> pg_backend_pid();
                """, (db_name,))
                time.sleep(1)  # Wait for connections to close
                
                # If connections still exist, force terminate them
                cursor.execute("""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = %s
                    AND pid <> pg_backend_pid();
                """, (db_name,))
        except Exception as e:
            print(f"Error terminating connections: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

    def setup_databases(self, **kwargs):
        """Set up the test databases"""
        self._terminate_connections()
        return super().setup_databases(**kwargs)

    def teardown_databases(self, old_config, **kwargs):
        """Tear down the test databases"""
        self._terminate_connections()
        return super().teardown_databases(old_config, **kwargs) 