from relecov_core.core_config import ERROR_INTIAL_SETTINGS_NOT_DEFINED
from relecov_core.models import SampleState, Sample

from relecov_core.utils.handling_samples import (
    increase_unique_value,
    get_user_id_from_collecting_institution,
)


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


def split_sample_data(data):
    """Split the json request into dictionnaries with the right fields"""
    split_data = {"sample": {}, "author": {}, "gisaid": {}, "ena": {}}

    for item, value in data.items():
        if "author" in item:
            split_data["author"][item] = value
            continue
        if "gisaid" in item:
            split_data["gisaid"][item] = value
            continue
        if "ena" in item:
            split_data["ena"][item] = value
            continue
        split_data["sample"][item] = value

    # add user and state to sample data
    split_data["sample"]["state"] = (
        SampleState.objects.filter(state__exact="Defined").last().get_state_id()
    )
    split_data["sample"]["user"] = get_user_id_from_collecting_institution(
        split_data["sample"]["collecting_institution"]
    )
    if Sample.objects.all().exists():
        last_unique_value = Sample.objects.all().last().get_unique_id()
        split_data["sample"]["sample_unique_id"] = increase_unique_value(
            last_unique_value
        )
    else:
        split_data["sample"]["sample_unique_id"] = "AAA-0001"
    return split_data
