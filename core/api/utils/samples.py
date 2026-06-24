# Generic imports
from datetime import datetime

# Local imports
import core.models
import core.utils.samples
import core.config


def split_sample_data(data):
    """Split the json request into dictionnaries with the right fields"""
    ALIASES = {
        "collecting_institution_code_1": "lab_code_1",
        "unique_sample_id": "sample_unique_id",
    }
    split_data = {"sample": {}, "author": {}, "gisaid": {}, "ena": {}}

    normalized_items = {ALIASES.get(item, item): value for item, value in data.items()}

    for item, value in normalized_items.items():
        if "author" in item:
            split_data["author"][item] = value
            continue
        if "gisaid" in item:
            split_data["gisaid"][item] = value
            continue
        if "ena" in item:
            split_data["ena"][item] = value
            continue
        if "date" in item:
            try:
                # Check if value is in date format with - separation
                value = datetime.strptime(value, "%Y-%m-%d")
            except (ValueError, TypeError):
                try:
                    # Check if no separation is in date format
                    value = datetime.strptime(value, "%Y%m%d")
                except (ValueError, TypeError):
                    # Value is not a date. Set to None to allow that serialzer
                    # store it in database.
                    value = None
        split_data["sample"][item] = value

    # add user and state to sample data
    split_data["sample"]["state"] = (
        core.models.SampleState.objects.filter(state__exact="Defined")
        .last()
        .get_state_id()
    )
    split_data["sample"]["user"] = (
        core.utils.samples.get_user_id_from_submitting_institution(
            split_data["sample"]["submitting_institution"]
        )
    )
    requested_unique_id = str(
        split_data["sample"].get("sample_unique_id") or ""
    ).strip()
    if requested_unique_id:
        split_data["sample"]["sample_unique_id"] = requested_unique_id
    elif core.models.Sample.objects.all().exists():
        last_unique_value = core.models.Sample.objects.all().last().get_unique_id()
        split_data["sample"]["sample_unique_id"] = (
            core.utils.samples.increase_unique_value(last_unique_value)
        )
    else:
        split_data["sample"]["sample_unique_id"] = (
            core.config.SAMPLE_ID_PREFIX + "AAA-0001"
        )
    return split_data
