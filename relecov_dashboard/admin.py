from django.contrib import admin

from relecov_dashboard.models import GraphicName, GraphicField, GraphicValue


class GraphicNameAdmin(admin.ModelAdmin):
    list_display = ["graphic_name"]


class GraphicFieldAdmin(admin.ModelAdmin):
    list_display = ["graphic", "field_1", "field_2", "field_3"]


class GraphicValueAdmin(admin.ModelAdmin):
    list_display = ["graphic", "value_1", "value_2", "value_3"]


admin.site.register(GraphicName, GraphicNameAdmin)
admin.site.register(GraphicField, GraphicFieldAdmin)
admin.site.register(GraphicValue, GraphicValueAdmin)