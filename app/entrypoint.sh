#!/bin/sh
set -e

# Wait for database to be ready
python manage.py wait_for_db
python manage.py migrate
python manage.py pre_create_su
python manage.py clear_orphaned_tags

# Collect static files only in production
if [ "$ENVIRONMENT" = "production" ]; then
    echo "️ Collecting static files to S3..."
    python manage.py collectstatic --noinput
    echo "✅ Static files collected successfully!"
else
    echo " Skipping collectstatic (not in production)"
fi

# Start the application
exec "$@"
