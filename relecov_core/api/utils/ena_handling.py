from relecov_core.models import PublicDatabaseFields
from relecov_core.core_config import ERROR_UNABLE_TO_STORE_IN_DATABASE

from relecov_core.api.serializers import CreatePublicDatabaseValueSerializer


def store_ena_data(data, schema_obj, sample_id):
    """Store the ena fields in database"""
    ena_field_objs = PublicDatabaseFields.objects.filter(
        database_type__iexact="ena", schemaID=schema_obj
    )
    for ena_field_obj in ena_field_objs:
        value_data = {"sampleID": sample_id}
        prop_name = ena_field_obj.get_property_name()
        value_data["public_database_fieldID"] = ena_field_obj.get_id()
        try:
            value_data["value"] = data[prop_name]
        except KeyError:
            value_data["value"] = ""
        value_serializer = CreatePublicDatabaseValueSerializer(data=value_data)
        if not value_serializer.is_valid():
            return {"ERROR": str(prop_name + " " + ERROR_UNABLE_TO_STORE_IN_DATABASE)}
    return {"SUCCESS": "success"}
