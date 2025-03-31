# Local imports
import core.models
import core.utils.rest_api


def get_lab_contact_details(user_obj):
    lab_data = {}
    lab_name = get_lab_name_from_user(user_obj)
    if lab_name != "":
        data = core.utils.rest_api.get_laboratory_data(lab_name)
        if "ERROR" in data:
            return data["ERROR"]
        for key in ["labEmail", "labPhone", "labContactName"]:
            if key not in data["DATA"].keys():
                break
            lab_data[key] = data["DATA"][key]
        else:
            lab_data["lab_name"] = lab_name
            return lab_data
    return ""


def get_lab_name_from_user(user_obj):
    """Get the laboratory name for the user"""
    if core.models.Profile.objects.filter(user=user_obj).exists():
        profile_obj = core.models.Profile.objects.filter(user=user_obj).last()
        return profile_obj.get_lab_name()
    else:
        return ""


def update_contact_lab(old_data, new_data):
    """Update the contact information. If any field is empty it will set the
    old value. In case that all new_data are empty returns than no changes
    """
    data = {}
    for key, value in old_data.items():
        if new_data[key] == "":
            data[key] = value
        else:
            data[key] = new_data[key]
    result = core.utils.rest_api.set_laboratory_data(data)
    if "ERROR" in result:
        return result
    return "OK"
