import json
import re
from django.db import DataError
from relecov_core.models import Schema, SchemaProperties, PropertyOptions
from relecov_core.utils.generic_functions import store_file
from relecov_core.core_config import (
    SCHEMAS_UPLOAD_FOLDER,
    ERROR_INVALID_JSON,
    ERROR_INVALID_SCHEMA,
    ERROR_SCHEMA_ALREADY_LOADED,
    SCHEMA_SUCCESSFUL_LOAD,
    ERROR_SCHEMA_ID_NOT_DEFINED,
    HEADING_SCHEMA_DISPLAY,
)


def get_schema_display_data(schema_id):
    """Get the properties definde for the schema"""
    schema_obj = get_schema_obj_from_id(schema_id)
    if schema_obj is None:
        return {"ERROR": ERROR_SCHEMA_ID_NOT_DEFINED}
    schema_data = {"s_data": []}
    if SchemaProperties.objects.filter(schemaID=schema_obj).exists():
        s_prop_objs = SchemaProperties.objects.filter(schemaID=schema_obj).order_by(
            "property"
        )
        schema_data["heading"] = HEADING_SCHEMA_DISPLAY
        for s_prop_obj in s_prop_objs:
            schema_data["s_data"].append(s_prop_obj.get_property_info())
    return schema_data


def get_schemas_loaded(apps_name):
    """Return the definded schemas"""
    s_data = []
    if Schema.objects.filter(schema_apps_name__exact=apps_name).exists():
        schema_objs = Schema.objects.filter(schema_apps_name__exact=apps_name).order_by(
            "schema_name"
        )
        for schema_obj in schema_objs:
            s_data.append(schema_obj.get_schema_info())
    return s_data


def get_schema_obj_from_id(schema_id):
    """Get the schema instance from id"""
    if Schema.objects.filter(pk__exact=schema_id).exists():
        return Schema.objects.filter(pk__exact=schema_id).last()
    return None


def load_schema(json_file):
    """Store json file in the defined folder and store information in database"""
    data = {}
    try:
        data["full_schema"] = json.load(json_file)
    except json.decoder.JSONDecodeError:
        return {"ERROR": ERROR_INVALID_JSON}
    data["file_name"] = store_file(json_file, SCHEMAS_UPLOAD_FOLDER)
    return data


def check_heading_valid_json(schema_data, m_structure):
    """Check if json have at least the main structure"""
    for item in m_structure:
        try:
            schema_data[item]
        except KeyError:
            return False
    return True


def store_schema_properties(schema_obj, s_properties, required):
    """Store the properties defined in the schema"""
    for prop_key in s_properties.keys():

        data = dict(s_properties[prop_key])
        data["schemaID"] = schema_obj
        data["property"] = prop_key
        if prop_key in required:
            data["required"] = True
        if "Enums" in data:
            data["options"] = True
        try:
            new_property = SchemaProperties.objects.create_new_property(data)
        except (KeyError, DataError) as e:
            print(prop_key, " error ", e)
            # schema_obj.delete()
            # return {"ERROR": e}
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
    return {"SUCCESS": ""}


def process_schema_file(json_file, version, user, apps_name):
    """Check json file and store in database"""
    schema_data = load_schema(json_file)
    if "ERROR" in schema_data:
        return schema_data
    # store root data of json schema
    structure = ["schema", "required", "type", "properties"]
    if not check_heading_valid_json(schema_data["full_schema"], structure):
        return {"ERROR": ERROR_INVALID_SCHEMA}

    schema_name = schema_data["full_schema"]["schema"]
    if Schema.objects.filter(
        schema_name__iexact=schema_name,
        schema_version__iexact=version,
        schema_apps_name__exact=apps_name,
    ).exists():
        return {"ERROR": ERROR_SCHEMA_ALREADY_LOADED}
    data = {
        "schema_name": schema_name,
        "file_name": schema_data["file_name"],
        "schema_version": version,
        "schema_app_name": apps_name,
        "user_name": user,
    }
    new_schema = Schema.objects.create_new_schema(data)
    result = store_schema_properties(
        new_schema,
        schema_data["full_schema"]["properties"],
        schema_data["full_schema"]["required"],
    )
    if "ERROR" in result:
        return result
    return {"SUCCESS": SCHEMA_SUCCESSFUL_LOAD}
