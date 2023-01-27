from django.contrib import admin

from relecov_dashboard.models import (
    GraphicName,
    GraphicField,
    GraphicValue,
    GraphicJsonFile,
)


class GraphicNameAdmin(admin.ModelAdmin):
    list_display = ["graphic_name"]


class GraphicFieldAdmin(admin.ModelAdmin):
    list_display = ["graphic", "field_1", "field_2", "field_3"]


class GraphicValueAdmin(admin.ModelAdmin):
    list_display = ["graphic", "value_1", "value_2", "value_3"]
    search_fields = ["value_1__icontains"]


class GraphicJsonFileAdmin(admin.ModelAdmin):
    list_display = ["graphic_name"]


admin.site.register(GraphicName, GraphicNameAdmin)
admin.site.register(GraphicField, GraphicFieldAdmin)
admin.site.register(GraphicValue, GraphicValueAdmin)
admin.site.register(GraphicJsonFile, GraphicJsonFileAdmin)
