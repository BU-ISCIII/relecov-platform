from relecov_core.models import (
    BioinfoAnalysisField,
    BioinfoAnalysisValue,
    DateUpdateState,
    Sample,
)

from relecov_core.utils.handling_samples import (
    get_sample_obj_from_id,
    get_samples_count_per_schema,
)

from relecov_core.utils.schema_handling import get_default_schema


def get_bio_analysis_stats_from_lab(lab_name=None):
    """Get the number of samples that are analized and compare with the number
    of recieved samples. If no lab name is given it matches all labs
    """
    bio_stats = {}
    if lab_name is None:
        # get stats from all lab
        bio_stats["analized"] = (
            DateUpdateState.objects.filter(stateID__state__iexact="Bioinfo")
            .values("sampleID")
            .distinct()
            .count()
        )
        bio_stats["received"] = Sample.objects.all().count()
    else:
        sample_objs = Sample.objects.filter(collecting_institution__iexact=lab_name)
        bio_stats["analized"] = (
            DateUpdateState.objects.filter(
                stateID__state__iexact="Bioinfo", sampleID__in=sample_objs
            )
            .values("sampleID")
            .distinct()
            .count()
        )
        bio_stats["received"] = len(sample_objs)
    return bio_stats


def get_bioinfo_analysis_data_from_sample(sample_id):
    """Get the bioinfo analysis for the sample"""
    sample_obj = get_sample_obj_from_id(sample_id)
    if not sample_obj:
        return None
    # Get the schema ID for filtering Fields
    schema_obj = sample_obj.get_schema_obj()
    a_data = []
    if not BioinfoAnalysisField.objects.filter(schemaID=schema_obj).exists():
        return None
    a_fields = BioinfoAnalysisField.objects.filter(schemaID=schema_obj)
    for a_field in a_fields:
        if BioinfoAnalysisValue.objects.filter(
            bioinfo_analysis_fieldID=a_field, sample=sample_obj
        ).exists():
            value = (
                BioinfoAnalysisValue.objects.filter(
                    bioinfo_analysis_fieldID=a_field, sample=sample_obj
                )
                .last()
                .get_value()
            )
        else:
            value = ""
        a_data.append([a_field.get_label(), value])
    return a_data


def get_bioinfo_analyis_fields_utilization(schema_obj=None):
    """Get the level of utilization for the bioinfo analysis fields.
    If schema is not given, the function get the latest default schema
    """
    b_data = {}
    if schema_obj is None:
        schema_obj = get_default_schema()

    # get field names
    if not BioinfoAnalysisField.objects.filter(schemaID=schema_obj).exists():
        return b_data

    num_samples_in_sch = get_samples_count_per_schema(schema_obj.get_schema_name())
    if num_samples_in_sch == 0:
        return b_data
    b_data = {
        "never_used": [],
        "always_none": [],
        "fields_norm": {},
        "fields_value": {},
    }
    b_field_objs = BioinfoAnalysisField.objects.filter(schemaID=schema_obj)
    for b_field_obj in b_field_objs:
        f_name = b_field_obj.get_label()
        if not BioinfoAnalysisValue.objects.filter(
            bioinfo_analysis_fieldID=b_field_obj
        ).exists():
            b_data["never_used"].append(f_name)
            b_data["fields_value"][f_name] = 0
            continue
        # b_data[schema_name][f_name] = [count]
        count_not_empty = (
            BioinfoAnalysisValue.objects.filter(bioinfo_analysis_fieldID=b_field_obj)
            .exclude(value__in=["None", ""])
            .count()
        )
        b_data["fields_value"][f_name] = count_not_empty
        if count_not_empty == 0:
            b_data["always_none"].append(f_name)
            continue

        try:
            b_data["fields_norm"][f_name] = count_not_empty / num_samples_in_sch
        except ZeroDivisionError:
            b_data["fields_norm"][f_name] = 0
    b_data["num_fields"] = len(b_field_objs)

    return b_data
