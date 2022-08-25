from relecov_core.models import BioinfoAnalysisField, LineageFields, Sample

from relecov_core.core_config import (
    ERROR_FIELD_NOT_DEFINED,
    ERROR_UNABLE_TO_STORE_IN_DATABASE,
)

from relecov_core.api.serializers import (
    CreateBioInfoAnalysisValueSerializer,
    CreateLineageValueSerializer,
)


def split_bioinfo_data(data, schema_obj):
    """Check if all fields in the request are defined in database"""
    split_data = {}
    split_data["bioinfo"] = {}
    split_data["lineage"] = {}
    for field, value in data.items():
        if field == "sample_name":
            split_data["sample"] = value
        # if this field belongs to BioinfoAnalysisField table
        if BioinfoAnalysisField.objects.filter(
            schemaID=schema_obj, property_name__iexact=field
        ).exists():
            split_data["bioinfo"][field] = value
        elif LineageFields.objects.filter(
            schemaID=schema_obj, property_name__iexact=field
        ).exists():
            split_data["lineage"][field] = value
        elif "schema" in field:
            pass
        else:
            return {"ERROR": str(field + " " + ERROR_FIELD_NOT_DEFINED)}
    return split_data


def store_bioinfo_data(s_data, schema_obj):
    """Save the new field data in database"""
    # schema_id = schema_obj.get_schema_id()
    sample_id = (
        Sample.objects.filter(sequencing_sample_id__iexact=s_data["sample"])
        .last()
        .get_sample_id()
    )
    # field to BioinfoAnalysisField table
    for field, value in s_data["bioinfo"].items():
        field_id = (
            BioinfoAnalysisField.objects.filter(
                schemaID=schema_obj, property_name__iexact=field
            )
            .last()
            .get_id()
        )
        data = {
            "value": value,
            "sampleID_id": sample_id,
            "bioinfo_analysis_fieldID": field_id,
        }

        bio_value_serializer = CreateBioInfoAnalysisValueSerializer(data=data)
        if not bio_value_serializer.is_valid():
            return {"ERROR": str(field + " " + ERROR_UNABLE_TO_STORE_IN_DATABASE)}
        bio_value_serializer.save()

    # field to LineageFields table
    for field, value in s_data["lineage"].items():
        lineage_id = (
            LineageFields.objects.filter(
                schemaID=schema_obj, property_name__iexact=field
            )
            .last()
            .get_lineage_field_id()
        )
        data = {"value": value, "sampleID_id": sample_id, "lineage_fieldID": lineage_id}

        lineage_value_serializer = CreateLineageValueSerializer(data=data)

        if not lineage_value_serializer.is_valid():
            return {"ERROR": str(field + " " + ERROR_UNABLE_TO_STORE_IN_DATABASE)}
        lineage_value_serializer.save()

    return {"SUCCESS": "success"}
