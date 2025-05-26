from django.db.models import Prefetch

import core.config
import core.models
import core.utils.samples
import core.utils.schema


def get_bio_analysis_stats_from_lab(lab_name=None):
    """Get the number of samples that are analized and compare with the number
    of recieved samples. If no lab name is given it matches all labs
    """
    bio_stats = {}
    if lab_name is None:
        # get stats from all lab
        bioqry = core.models.DateUpdateState.objects.filter(
            stateID__state__iexact="Bioinfo"
        )
        bio_stats["analized"] = bioqry.values("sampleID").distinct().count()
        bio_stats["received"] = core.models.Sample.objects.count()
    else:
        lab_samples = core.models.Sample.objects.filter(
            submitting_institution__iexact=lab_name
        )
        bio_stats["analized"] = (
            core.models.DateUpdateState.objects.select_related("sampleID")
            .filter(sampleID__pk__in=lab_samples, stateID__state__iexact="Bioinfo")
            .count()
        )
        bio_stats["received"] = (
            lab_samples.values("sequencing_sample_id").distinct().count()
        )
    return bio_stats


def get_bioinfo_analysis_data_from_sample(sample_id):
    """Get the bioinfo analysis for the sample"""
    sample_obj = core.utils.samples.get_sample_obj_from_id(sample_id)
    if not sample_obj:
        return None
    # Get the schema ID for filtering Fields
    schema_obj = sample_obj.get_schema_obj()
    bio_anlys_data = []
    bioan_fields = core.models.BioinfoAnalysisField.objects.filter(schemaID=schema_obj)
    if not bioan_fields:
        return None
    for bio_field in bioan_fields:
        samples_bio = core.models.BioinfoAnalysisValue.objects.filter(
            bioinfo_analysis_fieldID=bio_field, sample=sample_obj
        )
        if samples_bio.exists():
            value = samples_bio.last().get_value()
        else:
            value = ""
        bio_anlys_data.append([bio_field.get_label(), value])
    return bio_anlys_data


def get_bioinfo_analyis_fields_utilization(schema_obj=None):
    """Get the level of utilization for the bioinfo analysis fields.
    If schema is not given, the function get the latest default schema
    """
    b_data = {}
    if schema_obj is None:
        schema_obj = core.utils.schema.get_default_schema()

    # get field names
    b_field_objs = core.models.BioinfoAnalysisField.objects.filter(schemaID=schema_obj)
    if not b_field_objs.exists():
        return b_data

    num_samples_in_sch = core.utils.samples.get_samples_count_per_schema(schema_obj)
    if num_samples_in_sch == 0:
        return b_data
    b_data = {
        "never_used": [],
        "always_none": [],
        "fields_norm": {},
        "fields_value": {},
    }
    for b_field_obj in b_field_objs:
        f_name = b_field_obj.get_label()

        b_field_obj_info = core.models.BioinfoAnalysisValue.objects.filter(
            bioinfo_analysis_fieldID=b_field_obj, value__isnull=False
        ).exclude(value__in=core.config.FIELD_EMPTY_VALUES)

        # Prefetch with filtered queryset to avoid multiple queries
        samples = core.models.Sample.objects.prefetch_related(
            Prefetch(
                "bio_analysis_values",
                queryset=b_field_obj_info,
                to_attr="filtered_bio_values",
            )
        )

        # Count the number of samples with non-empty values
        count_not_empty = sum(1 for sample in samples if sample.filtered_bio_values)

        if not b_field_obj_info.exists():
            b_data["never_used"].append(f_name)
            b_data["fields_value"][f_name] = 0
            continue

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
