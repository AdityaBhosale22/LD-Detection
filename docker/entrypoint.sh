#!/bin/sh
# Apply database migrations, then start the main process (gunicorn by default).
set -e

python manage.py migrate --noinput

exec "$@"
