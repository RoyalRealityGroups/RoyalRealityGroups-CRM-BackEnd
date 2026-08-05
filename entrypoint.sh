#!/bin/sh

python manage.py collectstatic --noinput || true
python manage.py migrate

gunicorn 'BaseProject.wsgi' --bind=0.0.0.0:8000 --log-level info --timeout 180 --workers 3

