from relecov_core.core_config import (
    FIELDS_ON_SAMPLE_TABLE,
    FIELDS_ON_AUTHOR_TABLE,
    FIELDS_ON_GISAID_TABLE,
    FIELDS_ON_ENA_TABLE,
    ERROR_INTIAL_SETTINGS_NOT_DEFINED,
    ERROR_MISSING_SAMPLE_DATA,
)
from relecov_core.models import SampleState, Sample


def check_if_sample_exists(sequencing_sample_id):
    """Check if sequencing_sample_id is already defined in database"""
    if Sample.objects.filter(sequencing_sample_id__iexact=sequencing_sample_id).exists():
        return True
    return False


def split_sample_data(data):
    """Split the json request into dictionnaries with the right fields"""
    split_data = {
        "sample": {},
        "autor": {},
        "gisaid": {},
        "ena": {}
    }

    for item, value in data.items():
        if item in FIELDS_ON_SAMPLE_TABLE:
            split_data["sample"][item] = value
            continue
        if item in FIELDS_ON_AUTHOR_TABLE:
            split_data["author"][item] = value
            continue
        if item in FIELDS_ON_GISAID_TABLE:
            split_data["gisaid"][item] = value
            continue
        if item in FIELDS_ON_ENA_TABLE:
            split_data["ena"][item] = value
            continue
        print("Not match ", item)
    # add user and state to sample data
    split_data["sample"]["state"] = (
        SampleState.objects.filter(state__exact="Defined").last().get_state_id()
    )
    # import pdb; pdb.set_trace()
    if len(split_data["sample"]) < len(FIELDS_ON_SAMPLE_TABLE):
        return {"ERROR": ERROR_MISSING_SAMPLE_DATA}
    return split_data


def prepare_fields_in_sample(s_data):
    """Add sample state and set to None GISAID and ENA if not set"""
    if not SampleState.objects.filter(state__exact="Defined").exists():
        return {"ERROR": ERROR_INTIAL_SETTINGS_NOT_DEFINED}
    s_data["state"] = (
        SampleState.objects.filter(state__exact="Defined").last().get_state_id()
    )
    if "biosample_accession_ENA" not in s_data:
        s_data["biosample_accession_ENA"] = None
    if "virus_name" not in s_data:
        s_data["virus_name"] = None
    if "gisaid_id" not in s_data:
        s_data["gisaid_id"] = None
    return s_data
