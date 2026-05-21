#!/bin/sh
set -e

# Wait for Postgres before starting Django.
if [ "$DB_ENGINE" = "django.db.backends.postgresql" ] && [ -n "$DB_HOST" ]; then
  echo "Waiting for database at $DB_HOST:$DB_PORT..."
  until python -c "
import os, sys, socket
s = socket.socket()
s.settimeout(2)
try:
    s.connect((os.environ['DB_HOST'], int(os.environ.get('DB_PORT', '5432'))))
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    sleep 1
  done
  echo "Database is up."
fi

# Apply migrations and collect static on the web container only.
if [ "$RUN_MIGRATIONS" = "1" ]; then
  python manage.py migrate --noinput
  python manage.py collectstatic --noinput
fi

exec "$@"
