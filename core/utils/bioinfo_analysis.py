from django.db.models import Count, QuerySet
from django.core.cache import cache
from typing import Iterable, Union

import core.config
import core.models
import core.utils.samples
import core.utils.schema

SchemaLike = Union["core.models.Schema", Iterable["core.models.Schema"], QuerySet]

def get_bio_analysis_stats_from_lab(
    lab_name=None, institution_type="submitting_institution"
):
    """Get the number of samples that are analized and compare with the number
    of recieved samples. If no lab name is given it matches all labs
    """
    bio_stats = {}
    lab_query = {f"{institution_type}__iexact": lab_name}
    if lab_name is None:
        # get stats from all lab
        bioqry = core.models.DateUpdateState.objects.filter(
            stateID__state__iexact="Bioinfo"
        )
        bio_stats["analized"] = bioqry.values("sampleID").distinct().count()
        bio_stats["received"] = core.models.Sample.objects.count()
    else:
        lab_samples = core.models.Sample.objects.filter(**lab_query)
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


def get_bioinfo_analyis_fields_utilization(
    schema_qs: SchemaLike | None = None,
    *,
    use_cache: bool = True,
    cache_seconds: int = 300,
):
    """
    Return utilisation stats for Bioinfo-analysis fields across the selected
    schemas (all by default). Executes **one** heavy query + one light query.
    Results can be cached for `cache_seconds`.
    """
    # -- 0. Pick or normalise schemas ------------------------------------
    if schema_qs is None:
        schema_qs = core.models.Schema.objects.all()
    elif isinstance(schema_qs, QuerySet):
        pass
    else:
        schema_qs = schema_qs if isinstance(schema_qs, (list, tuple)) else [schema_qs]

    # -- 1. Check cache ---------------------------------------------------
    if use_cache:
        cache_key = f"bioinfo_util_{hash(tuple(x.pk for x in schema_qs))}"
        cached = cache.get(cache_key)
        if cached:
            return cached

    # -- 2. Total samples -------------------------------------------------
    num_samples = (
        core.models.Sample.objects.filter(schema_obj__in=schema_qs)
        .only("id")  # lighter count(*)
        .count()
    )
    if num_samples == 0:
        return {}

    # -- 3. One grouped query: filled counts ------------------------------
    FIELD_EMPTY = core.config.FIELD_EMPTY_VALUES
    rows = (
        core.models.BioinfoAnalysisValue.objects.filter(
            bioinfo_analysis_fieldID__schemaID__in=schema_qs,
            value__isnull=False,
        )
        .exclude(value__in=FIELD_EMPTY)
        .values("bioinfo_analysis_fieldID__label_name")
        .annotate(filled=Count("sample", distinct=True))
    )

    fields_value = {
        r["bioinfo_analysis_fieldID__label_name"]: r["filled"] for r in rows
    }
    fields_norm = {k: v / num_samples for k, v in fields_value.items()}
    labels_with_value = set(fields_value)

    # -- 4. Single light query to fetch ALL labels ------------------------
    defined_labels = set(
        core.models.BioinfoAnalysisField.objects.filter(
            schemaID__in=schema_qs
        ).values_list("label_name", flat=True)
    )
    never_used = defined_labels - labels_with_value

    result = {
        "fields_value": fields_value,
        "fields_norm": fields_norm,
        "never_used": list(never_used),
        "always_none": list(never_used),  # backward-compat
        "num_samples": num_samples,
    }

    # -- 5. Cache for N seconds ------------------------------------------
    if use_cache:
        cache.set(cache_key, result, cache_seconds)

    return result
