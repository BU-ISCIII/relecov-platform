from collections import Counter
from itertools import islice
from typing import Iterable, Union

from django.core.cache import cache
from django.db.models import QuerySet

import core.config
import core.models
import core.utils.samples

SchemaLike = Union["core.models.Schema", Iterable["core.models.Schema"], QuerySet]


def _chunked(iterator, chunk_size):
    """Yield lists pulled from ``iterator`` with up to ``chunk_size`` items."""
    while True:
        chunk = list(islice(iterator, chunk_size))
        if not chunk:
            break
        yield chunk


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
            .values("sampleID")
            .distinct()
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


def get_bioinfo_analysis_fields_utilization(
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
    # -- 0. Normalise schema identifiers ---------------------------------
    if schema_qs is None:
        schema_ids = list(core.models.Schema.objects.values_list("pk", flat=True))
    elif isinstance(schema_qs, QuerySet):
        schema_ids = list(schema_qs.values_list("pk", flat=True))
    elif isinstance(schema_qs, (list, tuple, set)):
        schema_ids = [getattr(item, "pk", item) for item in schema_qs]
    else:
        schema_ids = [getattr(schema_qs, "pk", schema_qs)]

    schema_ids = sorted({sid for sid in schema_ids if sid is not None})
    if not schema_ids:
        return {}

    # -- 1. Check cache ---------------------------------------------------
    cache_key = None
    if use_cache:
        cache_key = f"bioinfo_util_{hash(tuple(schema_ids))}"
        cached = cache.get(cache_key)
        if cached:
            return cached

    sample_filter = {"schema_obj_id__in": schema_ids}

    # -- 2. Total samples -------------------------------------------------
    num_samples = core.models.Sample.objects.filter(**sample_filter).count()
    if num_samples == 0:
        return {}

    # -- 3. Chunked scan of bioinfo values -------------------------------
    FIELD_EMPTY = set(core.config.FIELD_EMPTY_VALUES)
    through_model = core.models.Sample.bio_analysis_values.through
    batch_size = 500
    fields_counter = Counter()
    touched_labels = set()

    sample_iter = (
        core.models.Sample.objects.filter(**sample_filter)
        .values_list("pk", flat=True)
        .iterator(chunk_size=batch_size)
    )

    for batch in _chunked(sample_iter, batch_size):
        if not batch:
            continue

        seen_pairs = set()
        rows = (
            through_model.objects.filter(sample_id__in=batch)
            .values_list(
                "bioinfoanalysisvalue__bioinfo_analysis_fieldID__label_name",
                "sample_id",
                "bioinfoanalysisvalue__value",
            )
            .iterator(chunk_size=batch_size)
        )

        for label, sample_id, raw_value in rows:
            if label is None:
                continue
            touched_labels.add(label)

            if raw_value is None:
                continue

            value = raw_value.strip() if isinstance(raw_value, str) else raw_value
            if value in FIELD_EMPTY:
                continue

            key = (label, sample_id)
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            fields_counter[label] += 1

    fields_value = dict(fields_counter)
    fields_norm = {k: v / num_samples for k, v in fields_value.items()}
    labels_with_value = set(fields_value)

    # -- 4. Fetch defined labels -----------------------------------------
    defined_labels = set(
        core.models.BioinfoAnalysisField.objects.filter(schemaID__pk__in=schema_ids)
        .values_list("label_name", flat=True)
        .distinct()
    )
    never_used = defined_labels - touched_labels
    always_none = touched_labels - labels_with_value

    for label in always_none | never_used:
        fields_value.setdefault(label, 0)

    result = {
        "fields_value": fields_value,
        "fields_norm": fields_norm,
        "never_used": list(never_used),
        "always_none": list(always_none),
        "num_samples": num_samples,
    }

    # -- 5. Cache for N seconds ------------------------------------------
    if cache_key:
        cache.set(cache_key, result, cache_seconds)

    return result
