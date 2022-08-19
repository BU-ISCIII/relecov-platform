from relecov_core.models import (
    BioinfoAnalysisField,
    LineageFields,
    # BioinfoAnalysisFieldManager,
    # BioInfoAnalysisValueManager,
    Sample,
    Schema,
)

from relecov_core.core_config import (
    ERROR_SCHEMA_NOT_DEFINED,
    ERROR_FIELD_NOT_DEFINED,
    ERROR_SAMPLE_NOT_DEFINED,
    ERROR_SAMPLE_NAME_NOT_INCLUDED,
    ERROR_SAMPLE_NOT_IN_DEFINED_STATE,
    ERROR_UNABLE_TO_STORE_IN_DATABASE,
)

from relecov_core.api.serializers import (
    # CreateBioInfoAnalysisFieldSerializer,
    CreateBioInfoAnalysisValueSerializer,
    CreateLineageValueSerializer,
)


def check_valid_data(data, schema_id):
    """Check if all fields in the request are defined in database"""
    for field in data:

        if field == "sample_name":
            continue

        # if this field belongs to BioinfoAnalysisField table
        if (
            BioinfoAnalysisField.objects.filter(
                schemaID=schema_id, property_name__iexact=field
            ).exists()
            and not LineageFields.objects.filter(
                schemaID=schema_id, property_name__iexact=field
            ).exists()
        ):
            continue

        # if this field belongs to LineageFields table
        if (
            not BioinfoAnalysisField.objects.filter(
                schemaID=schema_id, property_name__iexact=field
            ).exists()
            or LineageFields.objects.filter(
                schemaID=schema_id, property_name__iexact=field
            ).exists()
        ):
            continue

        else:
            return {"ERROR": str(field + " " + ERROR_FIELD_NOT_DEFINED)}

    return True


def store_field(field, value, sample_obj, schema_id):
    # import pdb

    """Save the new field data in database"""
    
    # field to BioinfoAnalysisField table
    if BioinfoAnalysisField.objects.filter(
            schemaID=schema_id, property_name__iexact=field
            ).exists():
        data = {"value": value, "sampleID_id": sample_obj.get_sample_id()}
        data["bioinfo_analysis_fieldID"] = BioinfoAnalysisField.objects.filter(
            schemaID=schema_id, property_name__iexact=field
        ).last().get_id()

        bio_value_serializer = CreateBioInfoAnalysisValueSerializer(data=data)
        
        if not bio_value_serializer.is_valid():
            return False
        
        bio_value_serializer.save()
        # bio_value_serializer.add(schema_id)
    
    # field to LineageFields table
    if LineageFields.objects.filter(
        schemaID__pk=schema_id, property_name__iexact=field
    ).exists():
        data = {"value": value, "sampleID_id": sample_obj.get_sample_id()}
        data["lineage_fieldID"] = (
            LineageFields.objects.filter(
                schemaID=schema_id, property_name__iexact=field
            )
            .last()
            .get_lineage_field_id()
        )
        data["lineage_infoID"] = None

        print(data)
        print(field)

        lineage_value_serializer = CreateLineageValueSerializer(data=data)

        if not lineage_value_serializer.is_valid():
            print("False")
            return False

        lineage_value_serializer.save()

    return True


def fetch_bioinfo_data(data):

    if "sample_name" not in data:
        return {"ERROR": ERROR_SAMPLE_NAME_NOT_INCLUDED}
    sample_obj = Sample.objects.filter(
        sequencing_sample_id__iexact=data["sample_name"]
    ).last()
    if not Sample.objects.filter(sequencing_sample_id__iexact=data["sample_name"]):
        return {"ERROR": str(data["sample_name"] + " " + ERROR_SAMPLE_NOT_DEFINED)}
    if sample_obj.get_state() != "Defined":
        return {"ERROR": ERROR_SAMPLE_NOT_IN_DEFINED_STATE}

    if not Schema.objects.filter(
        schema_apps_name="relecov_core", schema_default=True
    ).exists():
        return {"ERROR": ERROR_SCHEMA_NOT_DEFINED}
    schema_obj = Schema.objects.filter(
        schema_apps_name="relecov_core", schema_default=True
    ).last()

    valid_data = check_valid_data(data, schema_obj)
    print("valid_data" + str(valid_data))
    if isinstance(valid_data, dict):
        return valid_data

    for field, value in data.items():
        if field == "sample_name":
            continue

        if not store_field(field, data[field], sample_obj, schema_obj.get_schema_id()):
            return {"ERROR": ERROR_UNABLE_TO_STORE_IN_DATABASE}

    sample_obj.update_state("Bioinfo")

    return data
