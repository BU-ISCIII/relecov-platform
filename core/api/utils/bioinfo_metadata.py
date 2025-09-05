# Local imports
import core.models
import core.api.serializers
import core.config


def split_bioinfo_data(data, schema_obj):
    """Check if all fields in the request are defined in database"""
    split_data = {"bioinfo": {}, "lineage": {}}
    for field, value in data.items():
        if field == "unique_sample_id":
            split_data["unique_sample_id"] = value
        # if this field belongs to BioinfoAnalysisField table
        if core.models.BioinfoAnalysisField.objects.filter(
            schemaID=schema_obj, property_name__iexact=field
        ).exists():
            split_data["bioinfo"][field] = value
        elif core.models.LineageFields.objects.filter(
            schemaID=schema_obj, property_name__iexact=field
        ).exists():
            split_data["lineage"][field] = value
        else:
            pass  # ignoring the values that not belongs to bioinfo
    return split_data


def get_analysis_defined(s_obj):
    return core.models.BioinfoAnalysisValue.objects.filter(
        bioinfo_analysis_fieldID__property_name="bioinformatics_analysis_date",
        sample=s_obj,
    ).values_list("value", flat=True)


def store_bioinfo_data(s_data, schema_obj):
    """Save the new field data in database"""
    uid = s_data.get("unique_sample_id")
    if not uid:
        return {"ERROR": "unique_sample_id not found in processed payload"}
    sample_obj = core.models.Sample.objects.filter(sample_unique_id__iexact=uid).last()
    if sample_obj is None:
        return {"ERROR": f"Sample not found for unique_sample_id='{uid}'"}
    # field to BioinfoAnalysisField table
    for field, value in s_data["bioinfo"].items():
        field_id = (
            core.models.BioinfoAnalysisField.objects.filter(
                schemaID=schema_obj, property_name__iexact=field
            )
            .last()
            .get_id()
        )
        data = {
            "value": value,
            "bioinfo_analysis_fieldID": field_id,
        }

        bio_value_serializer = (
            core.api.serializers.CreateBioinfoAnalysisValueSerializer(data=data)
        )
        if not bio_value_serializer.is_valid():
            return {
                "ERROR": str(
                    field + " " + core.config.ERROR_UNABLE_TO_STORE_IN_DATABASE
                )
            }
        bio_value_obj = bio_value_serializer.save()
        sample_obj.bio_analysis_values.add(bio_value_obj)

    # field to LineageFields table
    for field, value in s_data["lineage"].items():
        lineage_id = (
            core.models.LineageFields.objects.filter(
                schemaID=schema_obj, property_name__iexact=field
            )
            .last()
            .get_lineage_field_id()
        )
        data = {"value": value, "lineage_fieldID": lineage_id}
        lineage_value_serializer = core.api.serializers.CreateLineageValueSerializer(
            data=data
        )

        if not lineage_value_serializer.is_valid():
            return {
                "ERROR": str(
                    field + " " + core.config.ERROR_UNABLE_TO_STORE_IN_DATABASE
                )
            }
        lineage_value_obj = lineage_value_serializer.save()
        sample_obj.lineage_values.add(lineage_value_obj)

    return {"SUCCESS": "success"}
