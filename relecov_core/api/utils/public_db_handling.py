from relecov_core.models import PublicDatabaseFields
from relecov_core.core_config import ERROR_UNABLE_TO_STORE_IN_DATABASE

from relecov_core.api.serializers import CreatePublicDatabaseValueSerializer


def store_pub_databases_data(data, pub_db, schema_obj, sample_id):
    """Store the Public databases value in database"""
    field_objs = PublicDatabaseFields.objects.filter(
        database_type__public_type_name__iexact=pub_db, schemaID=schema_obj
    )
    for field_obj in field_objs:
        value_data = {"sampleID": sample_id}
        prop_name = field_obj.get_property_name()
        value_data["public_database_fieldID"] = field_obj.get_id()
        try:
            value_data["value"] = data[prop_name]
        except KeyError:
            value_data["value"] = ""
        value_serializer = CreatePublicDatabaseValueSerializer(data=value_data)
        if not value_serializer.is_valid():
            return {"ERROR": str(prop_name + " " + ERROR_UNABLE_TO_STORE_IN_DATABASE)}
        value_serializer.save()
    return {"SUCCESS": "success"}
