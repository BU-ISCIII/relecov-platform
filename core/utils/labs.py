# Local imports
import core.models
import core.utils.rest_api


def get_lab_contact_details(user_obj):
    """ "Get the user's contact data"""
    lab_name = get_lab_name_from_user(user_obj)
    if not lab_name or len(lab_name) == 0:
        return ""

    data = core.utils.rest_api.get_laboratory_data(lab_name)
    if "ERROR" in data:
        return data["ERROR"]

    if not data["DATA"]:
        return ""
    lab_data = data.get("DATA", {}).copy()
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


def get_collecting_insts_from_lab(lab_name):
    """Get a list of collecting institutions associated to the given
    laboratory (submitting_institution)
    """
    return (
        core.models.Sample.objects.filter(submitting_institution__iexact=lab_name)
        .values_list("collecting_institution", flat=True)
        .distinct()
    )


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
