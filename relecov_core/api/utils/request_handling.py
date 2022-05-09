from relecov_core.core_config import (
    HEADING_FOR_SAMPLE_TABLE,
    HEADING_FOR_AUTHOR_TABLE,
    HEADING_FOR_ANALYSIS_TABLE,
    HEADING_FOR_QCSTATS_TABLE,
    HEADING_FOR_LINEAGE_TABLE,
    ERROR_INTIAL_SETTINGS_NOT_DEFINED,
)
from relecov_core.models import SampleState

# from datetime import datetime# not used


def split_sample_data(data):
    """Split the json request into dictionnaries with the right fields"""
    split_data = {
        "sample": {},
        "autor": {},
        "qstats": {},
        "analysis": {},
        "lineage": {},
    }
    sample_fields = list(HEADING_FOR_SAMPLE_TABLE.values())
    author_fields = list(HEADING_FOR_AUTHOR_TABLE.values())
    qstats_fields = list(HEADING_FOR_QCSTATS_TABLE.values())
    analysis_fields = list(HEADING_FOR_ANALYSIS_TABLE.values())
    lineage_fields = list(HEADING_FOR_LINEAGE_TABLE.values())

    for item, value in data.items():
        if item in sample_fields:
            split_data["sample"][item] = value
            continue
        if item in author_fields:
            split_data["author"][item] = value
            continue
        if item in qstats_fields:
            split_data["qstats"][item] = value
            continue
        if item in analysis_fields:
            split_data["analysis"][item] = value
            continue
        if item in lineage_fields:
            split_data["lineage"][item] = value
            continue
        print("Not match ", item)
    # import pdb; pdb.set_trace()
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
