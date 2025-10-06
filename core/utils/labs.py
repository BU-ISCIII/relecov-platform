# Local imports
import core.models
import core.utils.rest_api
import core.utils.samples
import core.utils.lab_catalog


def get_lab_contact_details(user_obj):
    """ "Get the user's contact data"""
    lab_name = get_lab_name_from_user(user_obj)
    if not lab_name or len(lab_name) == 0:
        return ""

    data = core.utils.rest_api.get_laboratory_data(lab_name)
    if "ERROR" in data:
        return data["ERROR"]

    if not data["data"]:
        return ""
    lab_data = data.get("data", {}).copy()
    return lab_data


def get_all_defined_labs():
    """Get a list of laboratories that are defined in iSkyLIMS"""
    sum_data = core.utils.rest_api.get_summarize_data(None)
    if "ERROR" in sum_data:
        return sum_data
    return list(sum_data["laboratory"].keys())


def get_lab_name_from_user(user_obj):
    """Get the laboratory name for the user"""
    if core.models.Profile.objects.filter(user=user_obj).exists():
        profile_obj = core.models.Profile.objects.filter(user=user_obj).last()
        return profile_obj.get_lab_name()
    else:
        return ""


def get_collecting_insts_from_user(user_obj):
    """Get a list of collecting institutions associated to the given
    laboratory (submitting_institution)
    """
    available_samples = core.utils.samples.get_available_samples_for_user(user_obj)
    return available_samples.values_list("collecting_institution", flat=True).distinct()


def get_lab_codes_from_user(user_obj):
    """Return the set of lab_code_1 values associated with the user's profile."""

    profile = core.models.Profile.objects.filter(user=user_obj).last()
    if not profile:
        return []
    code = profile.get_lab_code()
    return [code] if code else []


def get_display_name_from_code(lab_code):
    """Resolve a human-readable name for the given lab code."""

    if not lab_code:
        return ""
    return core.utils.lab_catalog.ensure_lab_display(lab_code)


def update_contact_lab(data):
    """Update the contact information. If any field is empty it will set the
    old value. In case that all new_data are empty returns than no changes

    Expected fields:
        - lab_name
        - lab_contact_name
        - lab_phone
        - lab_email
    """
    data = {k: v for k, v in data.items() if v}
    result = core.utils.rest_api.set_laboratory_data(data)
    if "ERROR" in result:
        return result
    else:
        return "OK"
