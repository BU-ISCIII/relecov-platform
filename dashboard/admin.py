# Generic imports
from django.contrib import admin

# Local imports
import dashboard.models


class GraphicJsonFileAdmin(admin.ModelAdmin):
    list_display = ["graphic_name"]


admin.site.register(dashboard.models.GraphicJsonFile, GraphicJsonFileAdmin)
