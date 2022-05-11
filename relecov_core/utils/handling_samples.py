from relecov_core.core_config import (
    HEADING_FOR_AUTHOR_TABLE,
    HEADING_FOR_RECORD_SAMPLES,
)
import json

from relecov_core.models import (
    SchemaProperties,
    PropertyOptions,
    Schema,
)


def fetch_batch_options():
    data = []
    # check schema
    schema_obj = Schema.objects.filter(
        schema_name="RELECOV", schema_default=True
    ).last()
    properties_objs = SchemaProperties.objects.filter(
        fill_mode="batch", schemaID=schema_obj
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

        data.append(data_dict)
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
        print(properties_obj)

        data.append(data_dict)
        print(data_dict)
    return data


def create_metadata_form():
    sample_recorded = {}
    sample_recorded["heading"] = [x[0] for x in HEADING_FOR_RECORD_SAMPLES]
    sample_recorded["batch"] = fetch_batch_options()
    sample_recorded["samples"] = fetch_sample_options()

    return sample_recorded


def analyze_input_samples(request):
    sample_recorded = {}
    heading = [x[0] for x in HEADING_FOR_RECORD_SAMPLES]
    data_author = {}
    wrong_rows = []
    na_json_data = json.loads(request.POST["table_data"])

    for row in na_json_data:

        if row[0] == "":
            continue

        for field in range(len(row)):
            if row[field] == "":
                wrong_rows.append(row)
                break

        for idx in range(len(heading)):
            if heading[idx] in HEADING_FOR_AUTHOR_TABLE:
                data_author[HEADING_FOR_AUTHOR_TABLE[heading[idx]]] = row[idx]

        print(data_author)
        print(wrong_rows)
        if len(wrong_rows) < 1:
            sample_recorded["process"] = "Success"
        else:
            sample_recorded["process"] = "Error"
            sample_recorded["wrong_rows"] = wrong_rows
            sample_recorded["heading"] = heading
    print(sample_recorded["process"])

    return sample_recorded


def prepare_sample_input_table():
    pass


def build_record_sample_form():
    pass
