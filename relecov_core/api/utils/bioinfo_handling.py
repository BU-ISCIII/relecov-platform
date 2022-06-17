import json
import re
from relecov_core.models import (
    BioInfoProcessValue,
    BioinfoProcessField,
    Classification,
    Sample,
    # MetadataVisualization,
    # PropertyOptions,
    Schema,
    SchemaProperties,
)
from relecov_core.utils.generic_functions import store_file
from relecov_core.core_config import (
    # SCHEMAS_UPLOAD_FOLDER,
    BIOINFO_UPLOAD_FOLDER,
    ERROR_INVALID_JSON,
    # ERROR_INVALID_SCHEMA,
    # ERROR_SCHEMA_ALREADY_LOADED,
    # SCHEMA_SUCCESSFUL_LOAD,
    # ERROR_SCHEMA_ID_NOT_DEFINED,
    # ERROR_SCHEMA_NOT_DEFINED,
    # HEADING_SCHEMA_DISPLAY,
    # MAIN_SCHEMA_STRUCTURE,
    # NO_SELECTED_LABEL_WAS_DONE,
)

# from django.db import models


def fetch_bioinfo_data(data):
    list_of_no_exists = []
    default_schema = Schema.objects.get(schema_default=1)
    number_of_sample = int(data["microbiology_lab_sample_id"])
    variant_fields = data["variant"]

    for variant_field in variant_fields:
        print(variant_field)
        print(data["variant"][variant_field])

        if SchemaProperties.objects.filter(
            schemaID=default_schema.get_schema_id(), property__iexact=variant_field
        ).exists():
            print(
                "field {} , exists in Schema {}".format(
                    variant_field, default_schema.get_schema_id()
                )
            )
            if BioinfoProcessField.objects.filter(
                schemaID=default_schema.get_schema_id(),
                property_name__iexact=variant_field,
            ).exists():
                print(
                    "field {} , exists in BioinfoProcessField, schemaID {}".format(
                        variant_field, default_schema.get_schema_id()
                    )
                )
                BioInfoProcessValue.objects.create(
                    value=data["variant"][variant_field],
                    bioinfo_process_fieldID=BioinfoProcessField.objects.get(
                        schemaID=default_schema.get_schema_id(),
                        property_name__iexact=variant_field,
                    ),
                    sampleID_id=Sample.objects.get(
                        sequencing_sample_id=number_of_sample
                    ),
                ).save()
        """
        if SchemaProperties.objects.filter(schemaID=default_schema.get_schema_id(), property__iexact=property).exists():
            print("property: " +str(property) + " ,exists in Schema: " + default_schema.get_schema_id())

            if BioinfoProcessField.objects.filter(schemaID=default_schema.get_schema_id(),property_name__iexact=property).exists():
                print(" Exists in BioinfoProcessField: " + str(property))
                
                bioinfo_process_field = BioinfoProcessField.objects.get(
                schemaID=default_schema.get_schema_id(),
                property_name__iexact=property
                )

                bioinfo_process_values = BioInfoProcessValue.objects.create(
                    value=data[property],
                    bioinfo_process_fieldID=BioinfoProcessField.objects.get(
                    property_name__iexact=property
                    ),
                    sampleID_id=Sample.objects.get(
                        sequencing_sample_id=number_of_sample,
                    ),
                )
                bioinfo_process_values.save()
                    
            else:
                
                    print(" Doesn't exist in BioinfoProcessField: " + str(property))
                    list_of_no_exists.append(property)
                
                    
        else:
            print("Error... property: " +str(property) + " ,doesn't exists in Schema: " + default_schema.get_schema_id())
        
    print(len(list_of_no_exists))
    print(list_of_no_exists)
        """


"""
def fetch_bioinfo_data(data):
    list_of_no_exists = []
    number_of_sample = int(data["microbiology_lab_sample_id"])
    default_schema = Schema.objects.get(schema_default = 1)
    
    for property in data:
        if SchemaProperties.objects.filter(schemaID=default_schema.get_schema_id(), property__iexact=property).exists():
            print("property: " +str(property) + " ,exists in Schema: " + default_schema.get_schema_id())

            if BioinfoProcessField.objects.filter(schemaID=default_schema.get_schema_id(),property_name__iexact=property).exists():
                print(" Exists in BioinfoProcessField: " + str(property))
                
                bioinfo_process_field = BioinfoProcessField.objects.get(
                schemaID=default_schema.get_schema_id(),   
                property_name__iexact=property
                )

                bioinfo_process_values = BioInfoProcessValue.objects.create(
                    value=data[property],
                    bioinfo_process_fieldID=BioinfoProcessField.objects.get(
                    property_name__iexact=property
                    ),
                    sampleID_id=Sample.objects.get(
                        sequencing_sample_id=number_of_sample,
                    ),
                )
                bioinfo_process_values.save()
                    
            else:
                
                    print(" Doesn't exist in BioinfoProcessField: " + str(property))
                    list_of_no_exists.append(property)
                
                    
        else:
            print("Error... property: " +str(property) + " ,doesn't exists in Schema: " + default_schema.get_schema_id())
        
    print(len(list_of_no_exists))
    print(list_of_no_exists)
"""


def load_bioinfo_file(json_file):
    """Store json file in the defined folder and store information in database"""
    data = {}
    try:
        data["full_bioinfo"] = json.load(json_file)
    except json.decoder.JSONDecodeError:
        return {"ERROR": ERROR_INVALID_JSON}
    data["file_name"] = store_file(json_file, BIOINFO_UPLOAD_FOLDER)
    return data


def store_bioinfo_fields(schema_obj, s_properties):
    """Store the fields to be used for saving analysis information"""
    for prop_key in s_properties.keys():
        data = dict(s_properties[prop_key])
        if "classification" in data:
            match = re.search(r"(\w+) fields", data["classification"])
            if not match:
                continue
            classification = match.group(1).strip()
            # create new entr in Classification table in not exists
            if Classification.objects.filter(
                class_name__iexact=classification
            ).exists():
                class_obj = Classification.objects.filter(
                    class_name__iexact=classification
                ).last()
            else:
                class_obj = Classification.objects.create_new_classification(
                    classification
                )
            fields = {}
            fields["classificationID"] = class_obj
            fields["property_name"] = prop_key
            fields["label_name"] = data["label"]
            n_field = BioinfoProcessField.objects.create_new_field(fields)
            n_field.schemaID.add(schema_obj)

    return {"SUCCESS": ""}


def process_bioinfo_file(json_file, user, apps_name):
    """Check json file and store in database"""
    # list_of_samples = []
    list_of_samples_values = []
    list_of_samples_properties = []
    bioinfo_data = load_bioinfo_file(json_file)
    # list_of_samples = bioinfo_data["full_bioinfo"].keys()
    print(list_of_samples_values)
    for sample in bioinfo_data["full_bioinfo"]:
        list_of_samples_values = bioinfo_data["full_bioinfo"][sample].values()
        list_of_samples_properties = bioinfo_data["full_bioinfo"][sample].keys()
        print(list_of_samples_properties)

        for property in list_of_samples_properties:

            schema_id = Schema.objects.get(schema_default=1)

            instance = BioinfoProcessField.objects.create(
                property_name=property,
                label_name="labela",
                classificationID=Classification.objects.get(class_name="Sequencing"),
            )
            instance.schemaID.add(schema_id)
            instance.save()
        break
    """
    return {"SUCCESS": SCHEMA_SUCCESSFUL_LOAD}
    """
