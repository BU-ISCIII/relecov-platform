from os import stat
from django.contrib.auth.models import User
from relecov_core.core_config import (
    HEADING_FOR_RECORD_SAMPLES,
    HEADING_FOR_SAMPLE_TABLE,
)
import json

from relecov_core.models import (
    Document,
    SampleState,
    SchemaProperties,
    PropertyOptions,
    Schema,
    Sample,
)


def fetch_batch_options():
    data = []
    # check schema
    schema_obj = Schema.objects.filter(
        schema_name="RELECOV", schema_default=True
    ).last()
    # classification="Bioinformatics and QC metrics"
    properties_objs = SchemaProperties.objects.filter(
        fill_mode="batch",
        schemaID=schema_obj,
        classification="Bioinformatics and QC metrics",
    )
    # classification="Contributor Acknowledgement"
    """
    properties_objs2 = SchemaProperties.objects.filter(
        fill_mode="batch",
        schemaID=schema_obj,
        classification="Contributor Acknowledgement",
    )
    """
    print(properties_objs)
    for properties_obj in properties_objs:
        data_dict = {}
        if properties_obj.has_options():
            data_dict["Options"] = list(
                PropertyOptions.objects.filter(propertyID_id=properties_obj)
                .values_list("enums", flat=True)
                .distinct()
            )
        data_dict["Label"] = properties_obj.get_label()
        data_dict["Property"] = properties_obj.get_property()
        data_dict["Format"] = properties_obj.get_format()

        data.append(data_dict)
    """
    for properties_obj in properties_objs2:
        data_dict = {}
        if properties_obj.has_options():
            data_dict["Options"] = list(
                PropertyOptions.objects.filter(propertyID_id=properties_obj)
                .values_list("enums", flat=True)
                .distinct()
            )
        data_dict["Label"] = properties_obj.get_label()
        data_dict["Property"] = properties_obj.get_property()
        data_dict["Format"] = properties_obj.get_format()

        data.append(data_dict)
    """
    return data


def fetch_sample_options():
    data = []
    schema_obj = Schema.objects.filter(
        schema_name="RELECOV", schema_default=True
    ).last()
    properties_objs = SchemaProperties.objects.filter(
        fill_mode="sample", schemaID=schema_obj
    )
    for properties_obj in properties_objs:
        data_dict = {}
        if properties_obj.has_options():
            data_dict["Options"] = list(
                PropertyOptions.objects.filter(propertyID_id=properties_obj)
                .values_list("enums", flat=True)
                .distinct()
            )
        data_dict["Label"] = properties_obj.get_label()
        data_dict["Property"] = properties_obj.get_property()
        data_dict["Format"] = properties_obj.get_format()
        # print(properties_obj)

        data.append(data_dict)
        # print(data_dict)
    return data


def create_metadata_form():
    sample_recorded = {}
    sample_recorded["heading"] = [x[0] for x in HEADING_FOR_RECORD_SAMPLES]
    sample_recorded["batch"] = fetch_batch_options()
    sample_recorded["samples"] = fetch_sample_options()

    return sample_recorded


def get_dropdown_options():
    properties = get_properties_dict()
    options = get_properties_options(properties)
    print(options)
    return options


def get_properties_dict():
    properties = (
        SchemaProperties.objects.filter(fill_mode="batch")
        .values_list("id", "property")
        .distinct()
    )
    properties_dict = dict(properties)

    return properties_dict


def get_properties_options(properties):
    properties_dict = {}
    for property in properties:
        options = (
            PropertyOptions.objects.filter(propertyID_id=property)
            .values_list("enums", flat=True)
            .distinct()
        )
        options_dict = list(options)
        properties_dict[property] = options_dict
    return options_dict


def analyze_input_samples(request):
    sample_recorded = {}
    headings = [x[0] for x in HEADING_FOR_RECORD_SAMPLES]
    data_sample = {}
    wrong_rows = []
    na_json_data = json.loads(request.POST["table_data"])

    for row in na_json_data:
        print(row)

        if row[0] == "":
            continue

        for field in range(len(row)):
            if row[field] == "":
                wrong_rows.append(row)
                break

        headings_sample = HEADING_FOR_SAMPLE_TABLE.values()
        print(headings_sample)

        state = SampleState(
            state="1",
            display_string="display_string",
            description="description",
        )
        state.save()

        metadata_file = Document(
            title="title", file_path="file_path", uploadedFile="uploadedFile.xls"
        )
        metadata_file.save()

        sample = Sample(
            state=state,
            user=User.objects.create_user("user04", "email@email.com", "0xfa0xff"),
            metadata_file=metadata_file,
            collecting_lab_sample_id=row[0],
            sequencing_sample_id="",
            biosample_accession_ENA=row[5],
            virus_name=row[6],
            gisaid_id=row[14],
            sequencing_date="",
        )
        sample.save()
        """
        for idx in range(len(heading)):
            if heading[idx] in HEADING_FOR_SAMPLE_TABLE:
                data_sample[HEADING_FOR_SAMPLE_TABLE[heading[idx]]] = row[idx]
                print(row[idx])
        print(heading)
        """
        """
        s_prop_objs = SchemaProperties.objects.filter(schemaID=schema_obj).order_by(
            "property"
        )
        schema_data["heading"] = HEADING_SCHEMA_DISPLAY
        for s_prop_obj in s_prop_objs:
            schema_data["s_data"].append(s_prop_obj.get_property_info())
        for heading in headings:
            data_sample
        for idx in range(len(heading)):
            if heading[idx] in HEADING_FOR_SAMPLE_TABLE:
                data_sample[HEADING_FOR_SAMPLE_TABLE[heading[idx]]] = row[idx]
                # print(row[idx])
        print(heading)
        
        print(data_sample)
        """
        print(wrong_rows)
        if len(wrong_rows) < 1:
            sample_recorded["process"] = "Success"
            sample_recorded["batch"] = fetch_batch_options()
        else:
            sample_recorded["process"] = "Error"
            sample_recorded["wrong_rows"] = wrong_rows
            # sample_recorded["heading"] = heading
            sample_recorded["sample"] = fetch_sample_options()
    # print(sample_recorded["process"])

    return sample_recorded


def prepare_sample_input_table():
    pass


def build_record_sample_form():
    pass
