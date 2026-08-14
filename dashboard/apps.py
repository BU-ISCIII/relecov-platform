import logging

from django.apps import AppConfig
from django.db import connection

logger = logging.getLogger(__name__)


class RelecovDashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dashboard"

    def ready(self):
        from dashboard.models import GraphicJsonFile

        table_name = GraphicJsonFile._meta.db_table
        if table_name not in connection.introspection.table_names():
            logger.info(
                "Skipping dashboard registration because table %s does not exist",
                table_name,
            )
            return

        from dashboard.dash_apps import register_all

        register_all()
