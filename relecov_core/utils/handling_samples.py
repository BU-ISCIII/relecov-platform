from relecov_core.core_config import (
    HEADING_FOR_AUTHOR_TABLE,
    HEADING_FOR_RECORD_SAMPLES
)
import json
# from relecov_core.models import *


def get_input_samples():
    sample_recorded = {}
    sample_recorded["heading"] = [x[0] for x in HEADING_FOR_RECORD_SAMPLES]

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
