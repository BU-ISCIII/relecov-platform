"""
- receive file bioinfo_metadata.json (InMemoryUploadedFile) -> fetch_bioinfo_data()
- save this file into relecov_platform/documents/bioinfo_metadata -> fetch_bioinfo_data()
- parse file ->  parse_bioinfo_file()
- get a list of samples from parsed json file -> get_list_of_samples_from_parsed_json()
- insert each sample into database:
    - extract each sample, (iterate by sample)

"""

import json
import os

from django.conf import settings


# import re

from relecov_core.models import (
    BioInfoProcessValue,
    BioinfoProcessField,
    # Classification,
    # Lineage,
    Sample,
    # MetadataVisualization,
    # PropertyOptions,
    Schema,
    SchemaProperties,
)

from relecov_core.utils.generic_functions import store_file
from relecov_core.core_config import BIOINFO_METADATA_UPLOAD_FOLDER


def fetch_bioinfo_data(received_file, data):
    file_name = store_file(
        user_file=received_file, folder=BIOINFO_METADATA_UPLOAD_FOLDER
    )
    bioinfo_metadata_file = os.path.join(settings.BASE_DIR, "documents", file_name)
    parsed_file = parse_bioinfo_file(received_file=bioinfo_metadata_file)
    list_of_samples = get_list_of_samples_from_parsed_json(parsed_file=parsed_file)
    insert_data_into_db(parsed_file=parsed_file, list_of_samples=list_of_samples)


def parse_bioinfo_file(received_file):
    with open(received_file) as f:
        parse_json = json.load(f)
    return parse_json


def get_list_of_samples_from_parsed_json(parsed_file):
    list_of_samples = list(parsed_file.keys())
    return list_of_samples


def insert_data_into_db(parsed_file, list_of_samples):
    list_of_no_exists = []
    default_schema = Schema.objects.get(schema_default=1)

    for sample in list_of_samples:
        print(sample)
        data_in_sample = parsed_file[sample]
        for prop_obj in data_in_sample:
            print(prop_obj)

            if SchemaProperties.objects.filter(
                schemaID=default_schema.get_schema_id(), property__iexact=prop_obj
            ).exists():
                print(
                    "field {} , exists in Schema {}".format(
                        prop_obj, default_schema.get_schema_id()
                    )
                )
                if BioinfoProcessField.objects.filter(
                    schemaID=default_schema.get_schema_id(),
                    property_name__iexact=prop_obj,
                ).exists():
                    print(
                        "field {} , exists in BioinfoProcessField, schemaID {}".format(
                            prop_obj, default_schema.get_schema_id()
                        )
                    )
                    BioInfoProcessValue.objects.create(
                        value=parsed_file[sample][prop_obj],
                        bioinfo_process_fieldID=BioinfoProcessField.objects.get(
                            schemaID=default_schema.get_schema_id(),
                            property_name__iexact=prop_obj,
                        ),
                        sampleID_id=Sample.objects.get(sequencing_sample_id=sample),
                    ).save()

                else:
                    print(" Doesn't exist in BioinfoProcessField: " + str(property))
                    list_of_no_exists.append(property)

            else:
                print(
                    "Error... property: "
                    + str(property)
                    + " ,doesn't exists in Schema: "
                    + default_schema.get_schema_id()
                )
