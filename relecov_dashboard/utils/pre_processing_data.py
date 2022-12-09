from relecov_core.models import Sample, LineageValues

from relecov_dashboard.models import (
    GraphicName,
    GraphicField,
    GraphicValue,
    GraphicJsonFile,
)

from relecov_core.utils.rest_api_handling import (
    fetch_samples_on_condition,
    get_stats_data,
)


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
    graphic_name_obj = GraphicName.objects.create_new_graphic_name(
        "lineages_variations"
    )
    field_names["graphic_name_obj"] = graphic_name_obj
    GraphicField.objects.create_new_graphic_field(field_names)

    for date, samples in in_date_samples["DATA"].items():
        lineage_in_samples = (
            LineageValues.objects.filter(
                lineage_fieldID__property_name="lineage_name",
                sample__collecting_lab_sample_id__in=samples,
            )
            .values_list("value", flat=True)
            .distinct()
        )
        for lineage in lineage_in_samples:
            value_data = {"value_1": date, "value_2": str(lineage)}
            value_data["value_3"] = Sample.objects.filter(
                collecting_lab_sample_id__in=samples,
                lineage_values__value__iexact=lineage,
            ).count()
            value_data["graphic_name_obj"] = graphic_name_obj
            GraphicValue.objects.create_new_graphic_value(value_data)
    return {"SUCCESS": "Success"}


# preprocessing data for Sample processing dashboard
def pre_proc_specimen_source_pcr_1():
    """Collect the cts values when using pcr 1 and per specimen source"""
    lims_data = get_stats_data(
        {
            "sample_project_name": "Relecov",
            "project_field": "specimen_source,diagnostic_pcr_Ct_value_1",
        }
    )
    if "ERROR" in lims_data:
        return lims_data

    GraphicJsonFile.objects.create_new_graphic_json(
        {"graphic_name": "specimen_source_pcr_1", "graphic_data": lims_data}
    )

    return {"SUCCESS": "Success"}


def pre_proc_extraction_protocol_pcr_1():
    """Collect the cts values when using pcr 1 and per specimen source"""
    lims_data = get_stats_data(
        {
            "sample_project_name": "Relecov",
            "project_field": "nucleic_acid_extraction_protocol,diagnostic_pcr_Ct_value_1",
        }
    )
    if "ERROR" in lims_data:
        return lims_data

    GraphicJsonFile.objects.create_new_graphic_json(
        {"graphic_name": "extraction_protocol_pcr_1", "graphic_data": lims_data}
    )

    return {"SUCCESS": "Success"}


def pre_proc_library_kit_pcr_1():
    """Collect the cts values when using pcr 1 and per library preparation kit"""
    lims_data = get_stats_data(
        {
            "sample_project_name": "Relecov",
            "project_field": "library_preparation_kit,diagnostic_pcr_Ct_value_1",
        }
    )
    if "ERROR" in lims_data:
        return lims_data

    GraphicJsonFile.objects.create_new_graphic_json(
        {"graphic_name": "library_kit_pcr_1", "graphic_data": lims_data}
    )

    return {"SUCCESS": "Success"}
