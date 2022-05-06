#from datetime import datetime# not used
from relecov_core.core_config import HEADING_FOR_SAMPLE_TABLE, HEADING_FOR_AUTHOR_TABLE


def split_sample_data(data):
    """Split the json request into dictionnaries with the right fields"""
    split_data = {"sample": {}, "autor": {}}
    sample_fields = list(HEADING_FOR_SAMPLE_TABLE.values())
    author_fields = list(HEADING_FOR_AUTHOR_TABLE.values())
    for item, value in data.items():
        if item in sample_fields:
            split_data["sample"][item] = value
            continue
        if item in author_fields:
            split_data["author"][item] = value
            continue

    return split_data


def include_instances_in_sample():
    return
