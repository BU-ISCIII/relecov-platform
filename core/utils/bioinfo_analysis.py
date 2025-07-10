from django.db.models import Prefetch, Count

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
    """
    Return utilisation stats for Bioinfo-analysis fields of the given schema,
    using ONE grouped query (no N+1) so the call is fast even with many samples.
    """
    # ── 0. Default scheme ────────────────────────────────────────────────
    if schema_obj is None:
        schema_obj = core.utils.schema.get_default_schema()
    if not schema_obj:
        return {}

    # ── 1. Scheme bioinfo fields ────────────────────────────────────────
    field_qs = core.models.BioinfoAnalysisField.objects.filter(
        schemaID=schema_obj
    ).only("id", "label_name")
    if not field_qs.exists():
        return {}

    # ── 2. Total number of samples of the scheme ──────────────────────────────────
    num_samples = core.utils.samples.get_samples_count_per_schema(schema_obj)
    if num_samples == 0:
        return {}

    # ── 3. ONE query: how many samples have value per field ─────────────
    FIELD_EMPTY = core.config.FIELD_EMPTY_VALUES
    rows = (
        core.models.BioinfoAnalysisValue.objects.filter(
            bioinfo_analysis_fieldID__in=field_qs,
            value__isnull=False,
        )
        .exclude(value__in=FIELD_EMPTY)
        .values("bioinfo_analysis_fieldID")
        .annotate(filled=Count("sample", distinct=True))
    )
    filled_map = {r["bioinfo_analysis_fieldID"]: r["filled"] for r in rows}

    # ── 4. In-memory metrics ───────────────────────────────────────────────
    data = {
        "never_used": [],
        "always_none": [],
        "fields_norm": {},
        "fields_value": {},
        "num_fields": field_qs.count(),
    }

    for field in field_qs:
        label = field.get_label()
        filled = filled_map.get(field.id, 0)
        data["fields_value"][label] = filled

        if filled == 0:
            data["never_used"].append(label)
            data["always_none"].append(label)
        else:
            data["fields_norm"][label] = filled / num_samples

    return data
