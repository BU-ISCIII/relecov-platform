from django.db import models


class GraphicNameManager(models.Manager):
    def create_new_graphic_name(self, name):
        return self.create(graphic_name=name)
         

class GraphicName(models.Model):
    graphic_name = models.CharField(max_length=80)

    class Meta:
        db_table = "GraphicName"

    def __str__(self):
        return "%s" % (self.graphic_name)

    def get_graphic_name(self):
        return "%s" % (self.get_graphic_name)
    
    objects = GraphicNameManager()


class GraphicFieldManager(models.Manager):
    def create_new_graphic_field(self, data):
        return self.create(
            graphic=data["graphic_name_obj"],
            field_1=data["field_1"],
            field_2=data["field_2"],
            field_3=data["field_3"],
        )


class GraphicField(models.Model):
    graphic = models.ForeignKey(GraphicName, on_delete=models.CASCADE)
    field_1 = models.CharField(max_length=60, null=True, blank=True)
    field_2 = models.CharField(max_length=60, null=True, blank=True)
    field_3 = models.CharField(max_length=60, null=True, blank=True)

    class Meta:
        db_table = "GraphicField"

    def __str__(self):
        return "%s_%s" % (self.graphic, self.field_1)

    objects = GraphicFieldManager()


class GraphicValueManager(models.Manager):
    def create_new_graphic_value(self, data):
        return self.create(
            graphic=data["graphic_name_obj"],
            value_1=data["value_1"],
            value_2=data["value_2"],
            value_3=data["value_3"]
        )


class GraphicValue(models.Model):
    graphic = models.ForeignKey(GraphicName, on_delete=models.CASCADE)
    value_1 = models.CharField(max_length=60, null=True, blank=True)
    value_2 = models.CharField(max_length=60, null=True, blank=True)
    value_3 = models.CharField(max_length=60, null=True, blank=True)

    class Meta:
        db_table = "GraphicValue"

    def __str__(self):
        return "%s_%s" % (self.graphic, self.value_1)

    objects = GraphicValueManager()