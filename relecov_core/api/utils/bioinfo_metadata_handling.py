from relecov_core.models import (
    BioinfoAnalysisField,
    BioinfoAnalysisValue,
    LineageFields,
    Sample,
)

from relecov_core.core_config import (
    ERROR_UNABLE_TO_STORE_IN_DATABASE,
)

from relecov_core.api.serializers import (
    CreateBioinfoAnalysisValueSerializer,
    CreateLineageValueSerializer,
)


def split_bioinfo_data(data, schema_obj):
    """Check if all fields in the request are defined in database"""
    split_data = {}
    split_data["bioinfo"] = {}
    split_data["lineage"] = {}
    for field, value in data.items():
        if field == "sequencing_sample_id":
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
        else:
            pass  # ignoring the values that not belongs to bioinfo
    return split_data


def get_analysis_defined(s_obj):
    return BioinfoAnalysisValue.objects.filter(
        bioinfo_analysis_fieldID__property_name="analysis_date", sample=s_obj
    ).values_list("value", flat=True)


def store_bioinfo_data(s_data, schema_obj):
    """Save the new field data in database"""
    # schema_id = schema_obj.get_schema_id()
    sample_obj = Sample.objects.filter(
        sequencing_sample_id__iexact=s_data["sample"]
    ).last()
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
            "bioinfo_analysis_fieldID": field_id,
        }

        bio_value_serializer = CreateBioinfoAnalysisValueSerializer(data=data)
        if not bio_value_serializer.is_valid():
            return {"ERROR": str(field + " " + ERROR_UNABLE_TO_STORE_IN_DATABASE)}
        bio_value_obj = bio_value_serializer.save()
        sample_obj.bio_analysis_values.add(bio_value_obj)

    # field to LineageFields table
    for field, value in s_data["lineage"].items():
        lineage_id = (
            LineageFields.objects.filter(
                schemaID=schema_obj, property_name__iexact=field
            )
            .last()
            .get_lineage_field_id()
        )
        data = {"value": value, "lineage_fieldID": lineage_id}
        lineage_value_serializer = CreateLineageValueSerializer(data=data)

        if not lineage_value_serializer.is_valid():
            return {"ERROR": str(field + " " + ERROR_UNABLE_TO_STORE_IN_DATABASE)}
        lineage_value_obj = lineage_value_serializer.save()
        sample_obj.linage_values.add(lineage_value_obj)

    return {"SUCCESS": "success"}
