"""
Django command to wait for the database to be available
"""

import time
from django.db import connections
from psycopg2 import OperationalError as Psycopg2Error
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Django command to wait for the database to be available"""

    def handle(self, *args, **options):
        """Entry point for the management command"""
        self.stdout.write('Waiting for database...')

        while True:
            try:
                connections['default'].cursor()
                break
            except (OperationalError, Psycopg2Error):
                self.stdout.write('DB is unavailable. Waiting for 1 second...')
                time.sleep(1)
        self.stdout.write(self.style.SUCCESS('Database available!'))
