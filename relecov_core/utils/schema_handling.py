import json
import re
import os
from django.db import DataError
from django.conf import settings
from relecov_core.models import (
    BioinfoProcessField,
    Classification,
    MetadataVisualization,
    PropertyOptions,
    Schema,
    SchemaProperties,
)
from relecov_core.utils.generic_functions import (
    store_file,
    get_configuration_value
)
from relecov_core.core_config import (
    SCHEMAS_UPLOAD_FOLDER,
    ERROR_INVALID_JSON,
    ERROR_INVALID_SCHEMA,
    ERROR_SCHEMA_ALREADY_LOADED,
    SCHEMA_SUCCESSFUL_LOAD,
    ERROR_SCHEMA_ID_NOT_DEFINED,
    ERROR_SCHEMA_NOT_DEFINED,
    HEADING_SCHEMA_DISPLAY,
    MAIN_SCHEMA_STRUCTURE,
    NO_SELECTED_LABEL_WAS_DONE,
)


def fetch_info_meta_visualization(schema_obj):
    """Check if metadata visualization is already defined. If exists collect
    the fields selected and split in 2 the ones for samples and the one for
    batch
    """
    if not MetadataVisualization.objects.all().exists():
        return None
    m_fields = {"sample": [], "batch": []}
    m_v_sample_objs = MetadataVisualization.objects.filter(
        fill_mode__exact="sample"
    ).order_by("order")
    for m_v_sample_obj in m_v_sample_objs:
        m_fields["sample"].append(
            [m_v_sample_obj.get_label(), m_v_sample_obj.get_order()]
        )
    m_v_batch_objs = MetadataVisualization.objects.filter(
        fill_mode__exact="batch"
    ).order_by("order")
    for m_v_batch_obj in m_v_batch_objs:
        m_fields["batch"].append([m_v_batch_obj.get_label(), m_v_batch_obj.get_order()])
    return m_fields


def get_fields_if_template():
    """If config setting USE_TEMPLATE_FOR_METADATA_FORM is TRUE, read the
    file template "template_for_metadata_form.txt located at conf folder.
    Return a list with the labels or None if setting is false or file does not
    exists
    """
    if get_configuration_value("USE_TEMPLATE_FOR_METADATA_FORM") == "TRUE":
        temp_file_path = os.path.join(settings.BASE_DIR, "conf", "template_for_metadata_form.txt")
        try:
            with open(temp_file_path, "r") as fh:
                lines = fh.readlines()
        except OSError:
            return False
        f_list = []
        for line in lines:
            line = line.strip()
            f_list.append(line)
        return f_list
    return False


def get_fields_from_schema(schema_obj):
    """Get the labels and the property name from the schema.
    Based on the configuration , use the template to show the order selection
    and checked the used check checkbox
    """
    f_list = get_fields_if_template()
    data = {}
    schema_list = []
    data["schema_id"] = schema_obj.get_schema_id()
    prop_objs = SchemaProperties.objects.filter(schemaID=schema_obj).order_by("label")
    for prop_obj in prop_objs:
        label = prop_obj.get_label()
        if f_list and label in f_list:
            schema_list.append([prop_obj.get_property_name(), label, f_list.index(label), "true"])
        else:
            schema_list.append([prop_obj.get_property_name(), label])
    data["fields"] = schema_list

    return data


def get_latest_schema(schema_name, apps_name):
    """Get the latest schema that is defined in database"""
    if Schema.objects.filter(
        schema_name__iexact=schema_name,
        schema_apps_name__exact=apps_name,
        schema_default=True,
    ).exists():
        return Schema.objects.filter(
            schema_name__iexact=schema_name,
            schema_apps_name__exact=apps_name,
            schema_default=True,
        ).last()
    return {"ERROR": ERROR_SCHEMA_NOT_DEFINED}


def get_schema_display_data(schema_id):
    """Get the properties define for the schema"""
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


def del_metadata_visualization():
    """Delete previous metadata visualization if already exists"""
    if MetadataVisualization.objects.all().exists():
        m_vis_objs = MetadataVisualization.objects.all()
        for m_vis_obj in m_vis_objs:
            m_vis_obj.delete()
    return None


def store_fields_metadata_visualization(data):
    """Store the selected fields to display in metadata form"""
    # Delete existing visualization before loading new one
    del_metadata_visualization()
    schema_obj = get_schema_obj_from_id(data["schemaID"])
    fields = ["property_name", "label_name", "order", "in_use", "fill_mode"]
    entry_num = 0
    rows = json.loads(data["table_data"])
    for row in rows:
        if row[2] == "":
            continue
        m_data = {"schema_id": schema_obj}
        for idx in range(len(fields)):
            m_data[fields[idx]] = row[idx]
        MetadataVisualization.objects.create_metadata_visualization(m_data)
        entry_num += 1
    if entry_num == 0:
        return {"ERROR": NO_SELECTED_LABEL_WAS_DONE}
    return {"SUCCESS": entry_num}


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


def remove_existing_default_schema(schema_name, apps_name):
    """Remove the tag for default schema for the given schema name"""
    if Schema.objects.filter(
        schema_name__iexact=schema_name, schema_apps_name=apps_name, schema_default=True
    ).exists():
        schema_obj = Schema.objects.filter(
            schema_name__iexact=schema_name,
            schema_apps_name=apps_name,
            schema_default=True,
        ).last()
        schema_obj.update_default(False)
    return


def process_schema_file(json_file, version, default, user, apps_name):
    """Check json file and store in database"""
    schema_data = load_schema(json_file)
    if "ERROR" in schema_data:
        return schema_data
    # store root data of json schema
    if not check_heading_valid_json(schema_data["full_schema"], MAIN_SCHEMA_STRUCTURE):
        return {"ERROR": ERROR_INVALID_SCHEMA}
    schema_name = schema_data["full_schema"]["schema"]
    if default == "on":
        remove_existing_default_schema(schema_name, apps_name)
        default = True
    else:
        default = False
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
        "schema_default": default,
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
    s_fields = store_bioinfo_fields(
        new_schema, schema_data["full_schema"]["properties"]
    )
    if "ERROR" in s_fields:
        return s_fields
    return {"SUCCESS": SCHEMA_SUCCESSFUL_LOAD}
