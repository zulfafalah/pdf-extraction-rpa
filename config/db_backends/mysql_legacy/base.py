"""
Custom MySQL database backend that skips version check.

This is needed for connecting to older MariaDB/MySQL versions
that are not officially supported by Django 5.x.

WARNING: Use at your own risk. Some features may not work correctly
with older database versions.
"""

from django.db.backends.mysql.base import DatabaseWrapper as MySQLDatabaseWrapper
from django.db.backends.mysql.features import DatabaseFeatures as MySQLDatabaseFeatures


class DatabaseFeatures(MySQLDatabaseFeatures):
    """
    Custom database features for legacy MariaDB.

    Disables features not supported by MariaDB 10.3.x
    """

    # MariaDB 10.3 doesn't support RETURNING clause
    can_return_columns_from_insert = False
    can_return_rows_from_bulk_insert = False


class DatabaseWrapper(MySQLDatabaseWrapper):
    """
    Custom MySQL database wrapper that skips version validation.
    """

    # Use custom features class
    features_class = DatabaseFeatures

    def check_database_version_supported(self):
        """
        Skip the database version check.

        The external 'providers' database runs MariaDB 10.3.29 which is
        older than Django 5.x requirements (MariaDB 10.5+).

        Since we only use this database for reading existing data
        (managed=False models), we can safely skip this check.
        """
        pass  # Skip version check
