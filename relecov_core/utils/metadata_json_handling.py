import json
import re
from django.db import DataError
from relecov_core.models import (
    Metadata,
    MetadataProperties,
)
from relecov_core.utils.generic_functions import store_file
from relecov_core.core_config import (
    METADATA_JSON_SUCCESSFUL_LOAD,
    METADATA_JSON_UPLOAD_FOLDER,
    SCHEMAS_UPLOAD_FOLDER,
    ERROR_INVALID_JSON,
    ERROR_INVALID_SCHEMA,
    ERROR_SCHEMA_ALREADY_LOADED,
    SCHEMA_SUCCESSFUL_LOAD,
    ERROR_SCHEMA_ID_NOT_DEFINED,
    HEADING_SCHEMA_DISPLAY,
)


def get_metadata_json_data(metadata_id):
    """Get the properties define for the schema"""
    metadata_obj = get_metadata_obj_from_id(metadata_id)
    if metadata_obj is None:
        return {"ERROR": ERROR_SCHEMA_ID_NOT_DEFINED}
    metadata_data = {"s_data": []}
    if MetadataProperties.objects.filter(metadataID=metadata_obj).exists():
        s_prop_objs = MetadataProperties.objects.filter(
            metadataID=metadata_obj
        ).order_by("property")
        metadata_data["heading"] = HEADING_SCHEMA_DISPLAY
        for s_prop_obj in s_prop_objs:
            metadata_data["s_data"].append(s_prop_obj.get_property_info())
    return metadata_data


def get_metadata_json_loaded(apps_name):
    """Return the definded metadata"""
    s_data = []
    if Metadata.objects.filter(metadata_apps_name__exact=apps_name).exists():
        metadata_objs = Metadata.objects.filter(
            metadata_apps_name__exact=apps_name
        ).order_by("metadata_name")
        for metadata_obj in metadata_objs:
            s_data.append(metadata_obj.get_metadata_info())
    return s_data


def get_metadata_obj_from_id(metadata_id):
    """Get the metadata instance from id"""
    if Metadata.objects.filter(pk__exact=metadata_id).exists():
        return Metadata.objects.filter(pk__exact=metadata_id).last()
    return None


def load_metadata_json(json_file):
    """Store json file in the defined folder and store information in database"""
    data = {}
    try:
        data["full_metadata_json"] = json.load(json_file)
    except json.decoder.JSONDecodeError:
        return {"ERROR": ERROR_INVALID_JSON}
    data["file_name"] = store_file(json_file, METADATA_JSON_UPLOAD_FOLDER)
    return data


def check_heading_valid_json(metadata_data, m_structure):
    """Check if json have at least the main structure"""
    for item in m_structure:
        try:
            metadata_data[item]
        except KeyError:
            return False
    return True


def store_metadata_properties(metadata_obj, s_properties):  # , required
    """Store the properties defined in the metadata"""
    for prop_key in s_properties.keys():
        print(prop_key)

        data = dict(s_properties[prop_key])
        data["metadataID"] = metadata_obj
        data["property"] = prop_key
        """
        if prop_key in required:
            data["required"] = True
        if "Enums" in data:
            data["options"] = True
        """
        try:
            new_property = MetadataProperties.objects.create_new_property(data)
        except (KeyError, DataError) as e:
            print(prop_key, " error ", e)
            # schema_obj.delete()
            # return {"ERROR": e}
        """
        if "options" in data:
            for item in s_properties[prop_key]["Enums"]:
                enum = re.search(r"(.+) \[(.*)\]", item)
                if enum:
                    e_data = {"enums": enum.group(1), "ontology": enum.group(2)}
                else:
                    e_data = {"enums": item, "ontology": None}
                e_data["propertyID"] = new_property
                try:
                    PropertyOptions.objects.create_property_options(e_data)
                except (KeyError, DataError) as e:
                    print(prop_key, " enum ", e)
                    # schema_obj.delete()
                    # return {"ERROR": e}
        """

    return {"SUCCESS": ""}


def remove_existing_default_metadata(metadata_name, apps_name):
    """Remove the tag for default schema for the given schema name"""
    if Metadata.objects.filter(
        metadata_name__iexact=metadata_name,
        metadata_apps_name=apps_name,
        metadata_default=True,
    ).exists():
        metadata_obj = Metadata.objects.filter(
            metadata_name__iexact=metadata_name,
            metadata_apps_name=apps_name,
            metadata_default=True,
        ).last()
        metadata_obj.update_default(False)
    return


def process_metadata_json_file(json_file, version, default, user, apps_name):
    """Check json file and store in database"""
    metadata_data = load_metadata_json(json_file)
    # print(metadata_data)

    if "ERROR" in metadata_data:
        return metadata_data

    # store root data of json schema

    structure = [
        "properties",
    ]
    if not check_heading_valid_json(metadata_data["full_metadata_json"], structure):
        return {"ERROR": ERROR_INVALID_SCHEMA}

    metadata_name = metadata_data["full_metadata_json"]["project"]

    if default == "on":
        remove_existing_default_metadata(metadata_name, apps_name)
        default = True
    else:
        default = False

    if Metadata.objects.filter(
        metadata_name__iexact=metadata_name,
        metadata_version__iexact=version,
        metadata_apps_name__exact=apps_name,
    ).exists():
        return {"ERROR": ERROR_SCHEMA_ALREADY_LOADED}

    data = {
        "file_name": metadata_data["file_name"],
        "user_name": user,
        "metadata_name": metadata_name,
        "metadata_version": version,
        "metadata_default": default,
        "metadata_app_name": apps_name,
        "user_name": user,
    }
    new_metadata = Metadata.objects.create_new_metadata(data)
    # print(new_metadata)

    result = store_metadata_properties(
        new_metadata,
        metadata_data["full_metadata_json"]["properties"],
        # metadata_data["full_metadata_json"]["required"],
    )
    if "ERROR" in result:
        return result

    return {"SUCCESS": METADATA_JSON_SUCCESSFUL_LOAD}
