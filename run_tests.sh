#!/bin/bash

# Set database configuration
export DB_USER=paul
export DB_PASSWORD=Frankfurt5!
export DB_HOST=localhost
export DB_PORT=5432

# Generate a unique test database name
TEST_DB_NAME=$(python -c "import os; print(f'test_tipsterarena_{os.urandom(8).hex()}')")

# Terminate any existing connections to the test database
PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '$TEST_DB_NAME' AND pid <> pg_backend_pid();"

# Drop the test database if it exists
PGPASSWORD="$DB_PASSWORD" dropdb -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" "$TEST_DB_NAME" || true

# Create a fresh test database
PGPASSWORD="$DB_PASSWORD" createdb -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" "$TEST_DB_NAME"

# Run the tests with the test settings
DJANGO_SETTINGS_MODULE=core.test_settings python manage.py test "$@"

# Clean up the test database
PGPASSWORD="$DB_PASSWORD" dropdb -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" "$TEST_DB_NAME" 