#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

BACKUP_DIR="$SCRIPT_DIR/backups/$(date +%Y%m%d_%H%M%S)_v0_1_before_tg_tag_ordering"
mkdir -p $BACKUP_DIR

echo "Creating backup in $BACKUP_DIR"

# Your postgres container ID
POSTGRES_CONTAINER=$1
# Your app container ID
DJANGO_CONTAINER=$2
# Your database user, same as in .env
DB_USER=$3
# Your database name, same as in .env
DB_NAME=$4

# 1. Django data dump
echo "Backing up Django data..."
docker exec -t $DJANGO_CONTAINER python manage.py dumpdata > $BACKUP_DIR/django_data.json
docker exec -t $DJANGO_CONTAINER python manage.py dumpdata posts > $BACKUP_DIR/posts_data.json

# 2. PostgreSQL backup
echo "Backing up PostgreSQL database..."
docker exec -t $POSTGRES_CONTAINER pg_dump -U $DB_USER $DB_NAME > $BACKUP_DIR/database.sql
