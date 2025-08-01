# Generic imports
import json
import re
import os
from django.db import DataError
from django.conf import settings

# Local imports
import core.models
import core.serializers
import core.utils.generic_functions
import core.config


def get_fields_if_template():
    """If config setting USE_TEMPLATE_FOR_METADATA_FORM is TRUE, read the
    file template "template_for_metadata_form.txt located at conf folder.
    Return a list with the labels or None if setting is false or file does not
    exists
    """
    if (
        core.utils.generic_functions.get_configuration_value(
            "USE_TEMPLATE_FOR_METADATA_FORM"
        )
        == "TRUE"
    ):
        temp_file_path = os.path.join(
            settings.BASE_DIR, "conf", "template_for_metadata_form.txt"
        )
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
    prop_objs = core.models.SchemaProperties.objects.filter(
        schemaID=schema_obj
    ).order_by("label")
    for prop_obj in prop_objs:
        label = prop_obj.get_label()
        fill_mode = prop_obj.get_fill_mode()
        values = [prop_obj.get_property_name(), label, "", "false", fill_mode]
        if f_list and label in f_list:
            values[3] = "true"
            values[2] = f_list.index(label)
        schema_list.append(values)

    data["fields"] = schema_list

    return data


def get_latest_schema(schema_name, apps_name):
    """Get the latest schema that is defined in database"""
    if core.models.Schema.objects.filter(
        schema_name__icontains=schema_name,
        schema_apps_name__exact=apps_name,
        schema_default=True,
    ).exists():
        return core.models.Schema.objects.filter(
            schema_name__icontains=schema_name,
            schema_apps_name__exact=apps_name,
            schema_default=True,
        ).last()
    return {"ERROR": core.config.ERROR_SCHEMA_NOT_DEFINED}


def get_schema_display_data(schema_id):
    """Get the properties define for the schema"""
    schema_obj = get_schema_obj_from_id(schema_id)
    if schema_obj is None:
        return {"ERROR": core.config.ERROR_SCHEMA_ID_NOT_DEFINED}
    schema_data = {"s_data": []}
    if core.models.SchemaProperties.objects.filter(schemaID=schema_obj).exists():
        s_prop_objs = core.models.SchemaProperties.objects.filter(
            schemaID=schema_obj
        ).order_by("property")
        schema_data["heading"] = core.config.HEADING_SCHEMA_DISPLAY
        for s_prop_obj in s_prop_objs:
            schema_data["s_data"].append(s_prop_obj.get_property_info())
    return schema_data


def get_schemas_loaded(apps_name):
    """Return the definded schemas"""
    s_data = []
    if core.models.Schema.objects.filter(schema_apps_name__exact=apps_name).exists():
        schema_objs = core.models.Schema.objects.filter(
            schema_apps_name__exact=apps_name
        ).order_by("schema_name")
        for schema_obj in schema_objs:
            s_data.append(schema_obj.get_schema_info())
    return s_data


def get_schema_obj_from_id(schema_id):
    """Get the schema instance from id"""
    if core.models.Schema.objects.filter(pk__exact=schema_id).exists():
        return core.models.Schema.objects.filter(pk__exact=schema_id).last()
    return None


def load_schema(json_file):
    """Store json file in the defined folder and store information in database"""
    data = {}
    try:
        data["full_schema"] = json.load(json_file)
    except json.decoder.JSONDecodeError:
        return {"ERROR": core.config.ERROR_INVALID_JSON}
    data["file_name"] = core.utils.generic_functions.store_file(
        json_file, core.config.SCHEMAS_UPLOAD_FOLDER
    )
    return data


def check_heading_valid_json(schema_data, m_structure):
    """Check if json have at least the main structure"""
    for item in m_structure:
        try:
            schema_data[item]
        except KeyError:
            return False
    return True


def get_default_schema():
    """Return the default schema used for relecov"""
    if core.models.Schema.objects.filter(schema_default=True).exists():
        return core.models.Schema.objects.filter(schema_default=True).last()
    return None


def get_schema_properties(schema):
    """Fetch the list of the properties"""
    s_prop_dict = {}
    if core.models.SchemaProperties.objects.filter(schemaID=schema).exists():
        s_prop_objs = core.models.SchemaProperties.objects.filter(schemaID=schema)
        for s_prop_obj in s_prop_objs:
            p_name = s_prop_obj.get_property_name()
            s_prop_dict[p_name] = {}
            s_prop_dict[p_name]["classification"] = s_prop_obj.get_classification()
            s_prop_dict[p_name]["ontology"] = s_prop_obj.get_ontology()
    return s_prop_dict


def store_schema_properties(schema_obj, s_properties, required):
    """Store the properties defined in the schema"""
    for prop_key in s_properties.keys():
        data = dict(s_properties[prop_key])
        data["schemaID"] = schema_obj
        data["property"] = prop_key
        if prop_key in required:
            data["required"] = True
        if "enum" in data:
            data["options"] = True
        try:
            new_property = core.models.SchemaProperties.objects.create_new_property(
                data
            )
        except (KeyError, DataError) as e:
            print(prop_key, " error ", e)
            return {"ERROR": e}
            # schema_obj.delete()
        if "options" in data:
            for item in s_properties[prop_key]["enum"]:
                enum = re.search(r"(.+) \[(.*)\]", item)
                if enum:
                    e_data = {"enum": enum.group(1), "ontology": enum.group(2)}
                else:
                    e_data = {"enum": item, "ontology": None}
                e_data["propertyID"] = new_property
                try:
                    core.models.PropertyOptions.objects.create_property_options(e_data)
                except (KeyError, DataError) as e:
                    print(prop_key, " enum ", e)
                    # schema_obj.delete()
                    # return {"ERROR": e}
    return {"SUCCESS": ""}


def store_lineage_fields(schema_obj, s_properties):
    """Store the fields to be used for lineage analysis information"""
    for prop_key in s_properties.keys():
        data = dict(s_properties[prop_key])
        if "classification" in data and data["classification"] == "Lineage fields":
            fields = {}
            fields["property_name"] = prop_key
            fields["label_name"] = data["label"]
            l_field = core.models.LineageFields.objects.create_new_field(fields)
            l_field.schemaID.add(schema_obj)
    return {"SUCCESS": ""}


def store_public_data_fields(schema_obj, s_properties):
    """Store the fiells to be usde for public database information"""
    for prop_key in s_properties.keys():
        data = dict(s_properties[prop_key])
        if "classification" in data and data["classification"] == "Public databases":
            fields = {}
            fields["property_name"] = prop_key
            fields["label_name"] = data["label"]
            # find out the public database type
            database_types = core.models.PublicDatabaseType.objects.values_list(
                "public_type_name", flat=True
            ).distinct()
            for database_type in database_types:
                if database_type in prop_key:
                    break
            p_database_type_obj = core.models.PublicDatabaseType.objects.filter(
                public_type_name__exact=database_type
            ).last()
            fields["database_type"] = p_database_type_obj
            p_field = core.models.PublicDatabaseFields.objects.create_new_field(fields)
            p_field.schemaID.add(schema_obj)


def process_schema_file(json_file, default, user, apps_name):
    """Check JSON file and store it in the database, handling default schemas correctly."""
    schema_data = load_schema(json_file)

    # Check if there are erros when loading the schema
    if "ERROR" in schema_data:
        return schema_data

    if not check_heading_valid_json(
        schema_data["full_schema"], core.config.MAIN_SCHEMA_STRUCTURE
    ):
        return {"ERROR": core.config.ERROR_INVALID_SCHEMA}

    schema_name = schema_data["full_schema"]["title"]
    version = schema_data["full_schema"]["version"]

    # Return Error when a schema with the same name and version already exists
    if core.models.Schema.objects.filter(
        schema_name__iexact=schema_name,
        schema_version__iexact=version,
        schema_apps_name__exact=apps_name,
    ).exists():
        return {"ERROR": core.config.ERROR_SCHEMA_ALREADY_LOADED}

    # Prepare data for storing it in database
    data = {
        "schema_name": schema_name,
        "file_name": schema_data["file_name"],
        "schema_version": version,
        "schema_default": True if default == "on" else False,
        "schema_app_name": apps_name,
        "user_name": user,
    }

    # Create the new schema
    new_schema = core.models.Schema.objects.create_new_schema(data)

    result = store_schema_properties(
        new_schema,
        schema_data["full_schema"]["properties"],
        schema_data["full_schema"]["required"],
    )

    # Return Error if they appeared when storing schema properties
    if "ERROR" in result:
        return result

    # Store additional schema-related fields
    store_lineage_fields(new_schema, schema_data["full_schema"]["properties"])
    store_public_data_fields(new_schema, schema_data["full_schema"]["properties"])

    return {"SUCCESS": core.config.SCHEMA_SUCCESSFUL_LOAD}
