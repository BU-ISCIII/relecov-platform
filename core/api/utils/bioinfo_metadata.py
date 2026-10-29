# Local imports
import core.models
import core.api.serializers
from django.db import transaction


def split_bioinfo_data(data, schema_obj):
    """
    Split incoming payload into bioinfo and lineage dicts.
    Optimized to avoid per-field DB lookups by precomputing field maps.
    """
    # Build maps of property_name -> field_id for this schema (case-insensitive)
    bio_map = {
        name.lower(): fid
        for name, fid in core.models.BioinfoAnalysisField.objects.filter(
            schemaID=schema_obj
        ).values_list("property_name", "id")
    }
    lin_map = {
        name.lower(): fid
        for name, fid in core.models.LineageFields.objects.filter(
            schemaID=schema_obj
        ).values_list("property_name", "id")
    }

    split_data = {"bioinfo": {}, "lineage": {}}
    # Preserve unique_sample_id for later association
    if "unique_sample_id" in data:
        split_data["unique_sample_id"] = data["unique_sample_id"]

    for field, value in data.items():
        fkey = str(field).lower()
        if fkey in bio_map:
            split_data["bioinfo"][field] = value
        elif fkey in lin_map:
            split_data["lineage"][field] = value
        else:
            # ignore non-bioinfo/lineage keys
            continue

    # Attach maps so store_bioinfo_data can reuse them without extra queries
    split_data["_bio_map"] = bio_map
    split_data["_lin_map"] = lin_map
    return split_data


def get_analysis_defined(s_obj):
    return core.models.BioinfoAnalysisValue.objects.filter(
        bioinfo_analysis_fieldID__property_name="bioinformatics_analysis_date",
        sample=s_obj,
    ).values_list("value", flat=True)


def store_bioinfo_data(s_data, schema_obj):
    """
    Save bioinfo and lineage data ensuring values are only linked to the
    target sample, and raise an error if the analysis for this sample is
    already defined (same bioinformatics_analysis_date).
    """
    uid = s_data.get("unique_sample_id")
    if not uid:
        return {"ERROR": "unique_sample_id not found in processed payload"}

    sample_obj = core.models.Sample.objects.filter(sample_unique_id__iexact=uid).last()
    if sample_obj is None:
        return {"ERROR": f"Sample not found for unique_sample_id='{uid}'"}

    # 1) Defensive duplicate check by analysis date (even if already checked in view)
    #    Find the incoming analysis date if present and fail if already linked to this sample.
    incoming_date = None
    for k, v in s_data.get("bioinfo", {}).items():
        if str(k).lower() == "bioinformatics_analysis_date":
            incoming_date = v
            break
    if incoming_date is not None:
        already = core.models.BioinfoAnalysisValue.objects.filter(
            bioinfo_analysis_fieldID__property_name__iexact="bioinformatics_analysis_date",
            sample=sample_obj,
            value=incoming_date,
        ).exists()
        if already:
            return {"ERROR": "Analysis already defined for this sample and date"}

    # 2) Create values per-field and attach instances to the sample (no bulk ids)
    #
    # We wrap the whole creation/linking in a transaction to ensure atomicity:
    # - If any serializer validation or save fails midway, none of the previous
    #   BioinfoAnalysisValue/LineageValues nor their M2M links to this Sample are
    #   persisted. This prevents partially written analysis data or mismatched
    #   links that could corrupt sample associations.
    # - It also guarantees consistency between the created value rows and the
    #   corresponding m2m join rows for this specific sample.
    with transaction.atomic():
        # Bioinfo fields
        for field, value in s_data.get("bioinfo", {}).items():
            field_obj = core.models.BioinfoAnalysisField.objects.filter(
                schemaID=schema_obj, property_name__iexact=field
            ).last()
            if field_obj is None:
                continue
            data = {"value": value, "bioinfo_analysis_fieldID": field_obj.pk}
            ser = core.api.serializers.CreateBioinfoAnalysisValueSerializer(data=data)
            if not ser.is_valid():
                return {"ERROR": ser.errors}
            val_obj = ser.save()
            sample_obj.bio_analysis_values.add(val_obj)

        # Lineage fields
        for field, value in s_data.get("lineage", {}).items():
            l_field_obj = core.models.LineageFields.objects.filter(
                schemaID=schema_obj, property_name__iexact=field
            ).last()
            if l_field_obj is None:
                continue
            data = {"value": value, "lineage_fieldID": l_field_obj.pk}
            l_ser = core.api.serializers.CreateLineageValueSerializer(data=data)
            if not l_ser.is_valid():
                return {"ERROR": l_ser.errors}
            l_val_obj = l_ser.save()
            sample_obj.lineage_values.add(l_val_obj)

    return {"SUCCESS": "success"}
