"""
Custom MySQL database backend that skips version check.

This is needed for connecting to older MariaDB/MySQL versions
that are not officially supported by Django 5.x.

WARNING: Use at your own risk. Some features may not work correctly
with older database versions.
"""

from django.db.backends.mysql.base import DatabaseWrapper as MySQLDatabaseWrapper


class DatabaseWrapper(MySQLDatabaseWrapper):
    """
    Custom MySQL database wrapper that skips version validation.
    """

    def check_database_version_supported(self):
        """
        Skip the database version check.

        The external 'providers' database runs MariaDB 10.3.29 which is
        older than Django 5.x requirements (MariaDB 10.5+).

        Since we only use this database for reading existing data
        (managed=False models), we can safely skip this check.
        """
        pass  # Skip version check
