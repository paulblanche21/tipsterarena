#!/bin/bash

# Wait for database to be ready
echo "Waiting for database..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "Database is ready!"

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Start the application
echo "Starting application..."
exec daphne -b 0.0.0.0 -p 8000 tipsterarena.asgi:application 