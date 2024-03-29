# blog/apps.py

from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blog'

    def ready(self):
        pass
        # Import and connect signals here
        from blog import signals  # Import signals
