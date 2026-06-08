#!/usr/bin/env bash
set -e

# Collect static files into ./staticfiles
python manage.py collectstatic --no-input

# Run migrations
python manage.py makemigrations --no-input
python manage.py migrate --no-input
