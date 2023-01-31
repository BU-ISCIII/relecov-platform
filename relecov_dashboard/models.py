from django.db import models


class GraphicJsonFileManager(models.Manager):
    def create_new_graphic_json(self, data):
        return self.create(
            graphic_name=data["graphic_name"], graphic_data=data["graphic_data"]
        )


class GraphicJsonFile(models.Model):
    graphic_name = models.CharField(max_length=60)
    graphic_data = models.JSONField()
    creation_date = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = "GraphicJsonFile"

    def __str__(self):
        return "%s" % (self.graphic_name)

    def get_json_data(self):
        return self.graphic_data

    objects = GraphicJsonFileManager()
