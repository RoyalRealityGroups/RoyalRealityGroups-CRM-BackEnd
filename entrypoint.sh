#!/bin/sh

set -e

echo "Collecting static files..."
python manage.py collectstatic --noinput || true

echo "Running database migrations..."
python manage.py migrate --skip-checks --verbosity 0

echo "Importing dynamic models data..."
python manage.py import_dynamic_models_data --skip-checks || true

echo "Starting Gunicorn server..."
exec gunicorn 'BaseProject.wsgi' \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --threads 2 \
    --worker-class gthread \
    --worker-tmp-dir /dev/shm \
    --timeout 120 \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --log-level info \
    --access-logfile - \
    --error-logfile -
