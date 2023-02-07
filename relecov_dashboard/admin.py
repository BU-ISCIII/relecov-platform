from django.contrib import admin

from relecov_dashboard.models import (
    GraphicJsonFile,
)


class GraphicJsonFileAdmin(admin.ModelAdmin):
    list_display = ["graphic_name"]


admin.site.register(GraphicJsonFile, GraphicJsonFileAdmin)
