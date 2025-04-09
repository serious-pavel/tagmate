"""
Test Django management commands
"""
from unittest.mock import patch, MagicMock
from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import TestCase
from psycopg2 import OperationalError as Psycopg2Error


@patch('django.db.utils.ConnectionHandler.__getitem__')
class ConnectivityCommandTests(TestCase):
    """Test the management commands"""

    def test_wait_for_db_ready(self, mocked_getitem):
        """Test waiting for db when database is ready"""
        mocked_conn = MagicMock()
        mocked_getitem.return_value = mocked_conn

        call_command('wait_for_db')

        # Check if the connection was accessed
        mocked_getitem.assert_called_with('default')
        mocked_conn.cursor.assert_called_once()

    @patch('time.sleep', return_value=None)  # Mock sleep to avoid delays
    def test_wait_for_db_delay(self, mocked_sleep, mocked_getitem):
        """Test waiting for db delay when getting OperationalError"""
        mocked_conn = MagicMock()
        # Simulate database errors before success
        mocked_conn.cursor.side_effect = ([Psycopg2Error] * 2 +
                                          [OperationalError] * 3 +
                                          [MagicMock()])
        mocked_getitem.return_value = mocked_conn  # Simulate DB connection

        call_command('wait_for_db')

        # Ensure it retried 6 times
        self.assertEqual(mocked_conn.cursor.call_count, 6)
