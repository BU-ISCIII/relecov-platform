from relecov_core.core_config import *
import json
from relecov_core.models import *


def get_input_samples(request):
    """
    Description:
        The function will get the samples data that user filled in the form.
        defined_samples are the samples that either has no sample project or for
            the sample projects that no requires additional data
        pre_definde_samples are the ones that requires additional Information
        For already defined samples, no action are done on them and  they are included in not_valid_samples.
        it will return a dictionary which contains the processed samples.
    Input:
        request

    Constants:
        HEADING_FOR_DISPLAY_RECORDED_SAMPLES
        HEADING_FOR_RECORD_SAMPLE_IN_DATABASE

    Return:
        sample_recorded # Dictionnary with all samples cases.
    """
    sample_recorded = {}
    sample_recorded["heading"] = [x[0] for x in HEADING_FOR_RECORD_SAMPLES]

    return sample_recorded


def analyze_input_samples(request):
    sample_recorded = {}
    heading = [x[0] for x in HEADING_FOR_RECORD_SAMPLES]
    data_sample = {}
    data_author = {}
    wrong_rows = []
    row_counter = 0
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
