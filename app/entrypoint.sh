#!/bin/sh
set -e

# Wait for database to be ready
python manage.py wait_for_db
python manage.py migrate
python manage.py pre_create_su
python manage.py clear_orphaned_tags

# Collect static files only in production
if [ "$IS_PRODUCTION" = "1" ] || [ "$DEBUG" = "0" ]; then
    echo "️Collecting static files..."
    python manage.py collectstatic --noinput
else
    echo "Skipping collectstatic..."
fi

# Start the application
exec "$@"
