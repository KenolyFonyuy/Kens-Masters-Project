from django.apps import AppConfig


class FeedingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.feeding"
    verbose_name = "Feeding"

    def ready(self):
        from . import signals  # noqa: F401
