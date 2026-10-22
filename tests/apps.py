from django.apps import AppConfig


class CoreTestConfig(AppConfig):
    """Load core models without registering Dash applications at startup."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"


class DashboardTestConfig(AppConfig):
    """Load dashboard models without querying graphic caches at startup."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "dashboard"
