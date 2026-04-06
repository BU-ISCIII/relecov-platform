from django.apps import AppConfig


class RelecovDashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dashboard"

    def ready(self):
        from dashboard.dash_apps import register_all

        register_all()
