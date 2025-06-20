# Local imports
import core.models
import core.api.serializers
import core.config
import core.utils.samples


def split_metadata_values(data, schema_obj):
    """Check if all fields in the request are defined in database"""
    split_data = {}
    for field, value in data.items():
        try:
            split_data["sample"] = value
        except KeyError:
            return "ERROR"
    return split_data


def get_analysis_defined(s_obj):
    return core.models.MetadataValues.objects.filter(
        schema_property__property="analysis_date", sample=s_obj
    ).values_list("value", flat=True)


# TODO: Avoid crashing unless the required properties are missing. If the properties are not present in the schema, then waring and ignore.
def store_metadata_values(s_data, schema_obj, analysis_date):
    """Save the new metadata data in database"""
    sample_obj = core.models.Sample.objects.filter(
        sequencing_sample_id__iexact=s_data["sequencing_sample_id"]
    ).last()

    required_props = core.models.SchemaProperties.objects.filter(
        schemaID=schema_obj, required=True
    ).values_list("property", flat=True)

    missing_required = [prop for prop in required_props if prop not in s_data]
    if missing_required:
        return {"ERROR": f"Missing required properties: {', '.join(missing_required)}"}

    all_schema_props = core.models.SchemaProperties.objects.filter(
        schemaID=schema_obj
    ).values_list("property", flat=True)

    unexpected_props = [
        prop
        for prop in s_data
        if prop not in all_schema_props and prop != "sequencing_sample_id"
    ]
    if unexpected_props:
        print(
            f"WARNING: These properties are not defined in the schema and will be ignored: {', '.join(unexpected_props)}"
        )

    for field, value in s_data.items():
        if "schema_" in field or field == "sequencing_sample_id":
            continue

        property_name = core.models.SchemaProperties.objects.filter(
            schemaID=schema_obj, property__iexact=field
        ).last()

        try:
            data = {
                "value": value,
                "sample": sample_obj.id,
                "schema_property": property_name.id,
                "analysis_date": analysis_date,
            }
        except AttributeError:
            # FIXME: When field is not defined in db, then it returns error...
            print(field)
            return {
                "ERROR": f"{core.config.ERROR_FIELD_NOT_DEFINED, field}",
            }
        meta_value_serializer = core.api.serializers.CreateMetadataValueSerializer(
            data=data
        )
        if not meta_value_serializer.is_valid():
            return {"ERROR": f"{field} {core.config.ERROR_UNABLE_TO_STORE_IN_DATABASE}"}

        meta_value_serializer.save()

    return {"SUCCESS": "success"}
