import pandas as pd

from relecov_dashboard.models import GraphicName, GraphicField, GraphicValue


def get_graphic_data(graphic_name):
    """Collect the pre-processed data from database"""
    if GraphicName.objects.filter(graphic_name__iexact=graphic_name).exists():
        graphic_name_obj = GraphicName.objects.filter(
            graphic_name__iexact=graphic_name
        ).last()
        fields = (
            GraphicField.objects.filter(graphic=graphic_name_obj).values_list(
                "field_1", "field_2", "field_3"
            )[0]
        )
        values = list(
            GraphicValue.objects.filter(graphic=graphic_name_obj).values_list(
                "value_1", "value_2", "value_3"
            )
        )
        return pd.DataFrame(values, columns=fields)

    return None
