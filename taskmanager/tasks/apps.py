"""Configuration for the tasks app, including signal registration."""

from django.apps import AppConfig


class TasksConfig(AppConfig):
    """
    Configuration class for the 'tasks' application.

    Attributes:
        default_auto_field: Specifies the default primary key type for models.
        name: Name of the app.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tasks'

    def ready(self):
        """
        Import signals when the app is ready.

        This ensures that signal handlers in tasks/signals.py are registered.
        """
        import tasks.signals
