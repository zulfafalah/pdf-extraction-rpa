"""
Database Routers for external databases.

This router ensures that Django migrations are NOT applied to external databases
like the 'providers' MySQL database.
"""


class ProvidersRouter:
    """
    A router to control database operations on models in the 'providers' database.

    Models that should use this database must have:
        class Meta:
            app_label = 'providers'  # or be in the 'providers' app
            managed = False  # Prevents Django from managing the table
    """

    route_app_labels = {"providers"}  # Add app labels that use providers database

    def db_for_read(self, model, **hints):
        """
        Route read operations for providers models to the 'providers' database.
        """
        if model._meta.app_label in self.route_app_labels:
            return "providers"
        return None

    def db_for_write(self, model, **hints):
        """
        Route write operations for providers models to the 'providers' database.
        """
        if model._meta.app_label in self.route_app_labels:
            return "providers"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if both models are in the providers database.
        """
        if (
            obj1._meta.app_label in self.route_app_labels
            or obj2._meta.app_label in self.route_app_labels
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Prevent migrations on the 'providers' database.
        """
        if db == "providers":
            # Never allow migrations on the providers database
            return False
        if app_label in self.route_app_labels:
            # Don't allow providers models to migrate to other databases
            return False
        return None
