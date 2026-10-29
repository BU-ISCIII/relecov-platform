# Generic imports
from django.apps import AppConfig


class RelecovCoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        from core.dash_apps import register_all

        register_all()
