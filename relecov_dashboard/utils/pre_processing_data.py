from relecov_core.models import Sample, LineageValues

from relecov_dashboard.models import GraphicName, GraphicField, GraphicValue

from relecov_core.utils.rest_api_handling import fetch_samples_on_condition


def pre_proc_lineages_variations():
    """Collect the lineages information to store them at the pre-processed
    grpahic tables. Smoothing is performed before saving into database
    """
    field_names = {
        "field_1": "Collection date",
        "field_2": "Lineage",
        "field_3": "samples",
    }
    in_date_samples = fetch_samples_on_condition("collectionSampleDate")
    if "ERROR" in in_date_samples:
        return in_date_samples
    all_lineages = list(
        LineageValues.objects.filter(lineage_fieldID__property_name="lineage_name")
        .values_list("value", flat=True)
        .distinct()
    )

    graphic_name_obj = GraphicName.objects.create_new_graphic_name(
        "lineages_variations"
    )
    field_names["graphic_name_obj"] = graphic_name_obj
    GraphicField.objects.create_new_graphic_field(field_names)
    for date, samples in in_date_samples["DATA"].items():
        for lineage in all_lineages:
            value_data = {"value_1": date, "value_2": lineage}
            value_data["value_3"] = Sample.objects.filter(
                collecting_lab_sample_id__in=samples,
                lineage_values__value__iexact=lineage,
            ).count()
            value_data["graphic_name_obj"] = graphic_name_obj
            GraphicValue.objects.create_new_graphic_value(value_data)

    return {"SUCCESS": "Success"}
