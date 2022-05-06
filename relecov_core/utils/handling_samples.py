from relecov_core.core_config import *
import json
from relecov_core.models import *

# JExcel
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


# Upload Excel file
def prepare_sample_input_table():
    """
    Description: The function collect the species, Lab request, type of
        samples, and heading used in the input table.
        Return a dictionary with collected information.
    Functions:
        build_record_sample_form  : located at this file
    Variables:
        s_information # dictionary which collects all info
    Return:
        s_information #
    """
    # get the choices to be included in the form
    s_information = build_record_sample_form()
    s_information["heading"] = HEADING_FOR_RECORD_SAMPLES
    s_information["table_size"] = len(HEADING_FOR_RECORD_SAMPLES)
    """
    sample_objs = get_samples_in_state('Pre-defined')
    if sample_objs :
        s_information['pre_defined_samples'] = []
        s_information['pre_defined_heading'] = HEADING_FOR_COMPLETION_SAMPLES_PRE_DEFINED
        for sample_obj in sample_objs :
            s_information['pre_defined_samples'].append(sample_obj.get_info_in_defined_state())
    """
    print(s_information["heading"])
    return s_information


def build_record_sample_form():
    """
    Description:
        The function collect the stored information of  species, sample origin and sample type to use in the
        selected form.
    Input:
    Functions:
        get_species             located at this file
        get_lab_requested       located at this file
        get_sample_type         located at this file
    Variables:
        sample_information:     Dictionnary to collect the information
    Return:
        sample_information
    """

    sample_information = {}
    """
    sample_information['species'] = get_species()
    sample_information['lab_requested'] = get_lab_requested()
    sample_information['sampleType'] = get_sample_type(app_name)
    sample_information['sample_project'] = get_defined_sample_projects (app_name)
    sample_information['sample_project'].insert(0,'None')
    """
    return sample_information
