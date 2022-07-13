from relecov_core.models import (
    # BioinfoProcessField,
    Sample,
    Schema
)
from relecov_core.core_config import (
    ERROR_SCHEMA_NOT_DEFINED,
    ERROR_FIELD_NOT_DEFINED,
    ERROR_SAMPLE_NOT_DEFINED,
    ERROR_SAMPLE_NAME_NOT_INCLUDED,
    ERROR_SAMPLE_NOT_IN_DEFINED_STATE,
    ERROR_UNABLE_TO_STORE_IN_DATABASE
)
# from relecov_core.api.serializers import CreateBioInfoProcessValueSerializer


def check_valid_data(data, schema_id):
    """Check if all fields in the request are defined in database"""
    for field in data:
        if field == "sample_name":
            continue
        if not BioinfoProcessField.objects.filter(
            schemaID=schema_id, property_name__iexact=field
        ).exists():
            return {"ERROR" : str(field + " " + ERROR_FIELD_NOT_DEFINED)}
    return True


def store_field(field, value, sample_obj, schema_id):
    """Save the new field data in database"""
    data = {"value": value, "sampleID_id": sample_obj}
    data["bioinfo_process_fieldID"] = BioinfoProcessField.objects.filter(
        schemaID=schema_id,
        property_name__iexact=field).last()

    bio_value_serializer = CreateBioInfoProcessValueSerializer(data=data)
    if not bio_value_serializer.is_valid():
        return False
    bio_value_serializer.save()
    return True


def fetch_bioinfo_data(data):
    if "sample_name" not in data:
        return {"ERROR": ERROR_SAMPLE_NAME_NOT_INCLUDED}
    sample_obj = Sample.objects.filter(sequencing_sample_id__iexact=data["sample_name"]).last()
    if not Sample.objects.filter(sequencing_sample_id__iexact=data["sample_name"]):
        return {"ERROR": str(data["sample_name"] + " " + ERROR_SAMPLE_NOT_DEFINED)}
    if sample_obj.get_state() != "Defined":
        return {"ERROR": ERROR_SAMPLE_NOT_IN_DEFINED_STATE}

    if not Schema.objects.filter(schema_apps_name="relecov_core", schema_default=True).exists():
        return {"ERROR": ERROR_SCHEMA_NOT_DEFINED}
    schema_obj = Schema.objects.filter(schema_apps_name="relecov_core", schema_default=True).last()

    valid_data = check_valid_data(data, schema_obj)
    if isinstance(valid_data, dict):
        return valid_data

    for field, value in data.items():
        if field == "sample_name":
            continue
        import pdb; pdb.set_trace()
        if not store_field(field, data[field], sample_obj, schema_obj):
            return {"ERROR": ERROR_UNABLE_TO_STORE_IN_DATABASE}
        import pdb; pdb.set_trace()
    sample_obj.update_state("Bioinfo")

    return
