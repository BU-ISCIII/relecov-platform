import json

from relecov_core.utils.generic_functions import store_file
from relecov_core.core_config import SCHEMAS_UPLOAD_FOLDER, ERROR_INVALID_JSON


def load_schema(json_file):
    """Store json file in the defined folder and store information in database"""
    data = {}
    try:
        data["schema_data"] = json.load(json_file)
    except json.decoder.JSONDecodeError:
        return {"ERROR": ERROR_INVALID_JSON}
    data["file_name"] = store_file(json_file, SCHEMAS_UPLOAD_FOLDER)
    return data


def process_schema_file(json_file):
    """ Check json fiel and store in database"""
    file_name = load_schema(json_file)
    if "ERROR" in file_name:
        return file_name
    # store root data of json schema
    import pdb; pdb.set_trace()
