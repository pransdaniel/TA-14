#!/bin/sh
set -e

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn adaptive_engine.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3
