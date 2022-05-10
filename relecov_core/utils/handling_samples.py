from relecov_core.core_config import (
    HEADING_FOR_AUTHOR_TABLE,
    HEADING_FOR_RECORD_SAMPLES,
)
import json

from relecov_core.models import(
    SchemaProperties,
    PropertyOptions,
)


def get_input_samples():
    sample_recorded = {}
    sample_recorded["heading"] = [x[0] for x in HEADING_FOR_RECORD_SAMPLES]
    dropdown_options = get_dropdown_options()
    sample_recorded["dropdown"] = dropdown_options
    
    return sample_recorded


def get_dropdown_options():
    properties = get_properties_dict()
    options = get_properties_options(properties)
    print(options)
    return options


def get_properties_dict():
    properties = SchemaProperties.objects.filter(fill_mode = "batch").values_list('id', 'property').distinct()
    properties_dict = dict(properties)
    
    return properties_dict


def get_properties_options(properties):
    properties_dict = {}
    for property in properties:
        options = PropertyOptions.objects.filter(propertyID_id = property).values_list('enums', flat=True).distinct()
        options_dict = list(options)
        properties_dict[property] = options_dict
    return options_dict


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
