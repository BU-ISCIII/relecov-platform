# Generic imports
import re
from datetime import datetime

# Local imports
import core.models
import core.utils.samples
import core.config


def get_next_sample_unique_id():
    """Return the next available ID after the highest generated sample ID."""
    generated_id_pattern = (
        rf"^{re.escape(core.config.SAMPLE_ID_PREFIX)}[A-Z]{{3}}-[0-9]{{4}}$"
    )
    last_unique_value = (
        core.models.Sample.objects.filter(sample_unique_id__regex=generated_id_pattern)
        .order_by("-sample_unique_id")
        .values_list("sample_unique_id", flat=True)
        .first()
    )

    if last_unique_value is None:
        candidate = core.config.SAMPLE_ID_PREFIX + "AAA-0001"
    else:
        candidate = core.utils.samples.increase_unique_value(last_unique_value)

    while core.models.Sample.objects.filter(
        sample_unique_id__iexact=candidate
    ).exists():
        candidate = core.utils.samples.increase_unique_value(candidate)

    return candidate


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
        split_data["sample"]["sample_unique_id"] = get_next_sample_unique_id()
    else:
        split_data["sample"]["sample_unique_id"] = (
            core.config.SAMPLE_ID_PREFIX + "AAA-0001"
        )
    return split_data
