from django.db import models


class GraphicName(models.Model):
    graphic_name = models.CharField(max_length=80)

    class Meta:
        db_table = "GraphicName"

    def __str__(self):
        return "%s" % (self.graphic_name)

    def get_graphic_name(self):
        return "%s" % (self.get_graphic_name)


class GraphicField(models.Model):
    graphic = models.ForeignKey(GraphicName, on_delete=models.CASCADE)
    field_1 = models.CharField(max_length=60, null=True, blank=True)
    field_2 = models.CharField(max_length=60, null=True, blank=True)
    field_3 = models.CharField(max_length=60, null=True, blank=True)

    class Meta:
        db_table = "GraphicField"

    def __str__(self):
        return "%s_%s" % (self.graphic, self.field_1)


class GraphicValue(models.Model):
    graphic = models.ForeignKey(GraphicName, on_delete=models.CASCADE)
    value_1 = models.CharField(max_length=60, null=True, blank=True)
    value_2 = models.CharField(max_length=60, null=True, blank=True)
    value_3 = models.CharField(max_length=60, null=True, blank=True)

    class Meta:
        db_table = "GraphicValue"

    def __str__(self):
        return "%s_%s" % (self.graphic, self.value_1)