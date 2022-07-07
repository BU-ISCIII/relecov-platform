import json
# import re
"""
from relecov_core.models import (
    BioInfoProcessValue,
    BioinfoProcessField,
    Classification,
    # Lineage,
    Sample,
    # MetadataVisualization,
    # PropertyOptions,
    Schema,
    SchemaProperties,
)
"""

# from relecov_core.utils.generic_functions import store_file
"""
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
"""
# from relecov_core.models import BioinfoMetadataFile
# from django.core.files.uploadedfile import InMemoryUploadedFile

"""
- receive file bioinfo_metadata.json
- parse file
- extract each sample, iterate by sample
- insert each sample into database
-
"""


def fetch_bioinfo_data(file_received, data):
    print(data["data"].read())
    # my_file = InMemoryUploadedFile(file=file_received,field_name="file1",name=None,content_type=file_received.read(),size=None, charset="utf-8")
    # BioinfoMetadataFile.objects.create(title="file")

    with open(file_received) as f:
        parse_json = json.loads(f)
    print(parse_json)


def parse_bioinfo_file():
    pass
