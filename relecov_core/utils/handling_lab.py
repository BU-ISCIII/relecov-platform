from relecov_core.models import Profile
from relecov_core.utils.rest_api_handling import get_laboratory_data


def get_lab_contact_details(user_obj):
    lab_data = {}
    lab_name = get_lab_name(user_obj)
    if lab_name != "":
        data = get_laboratory_data(lab_name)
        if "ERROR" in data:
            return data
        lab_data["contact_email"] = data["DATA"]["labEmail"]
        lab_data["contact_telephone"] = data["DATA"]["labPhone"]
        lab_data["contact_name"] = data["DATA"]["labContactName"]
        lab_data["lab_name"] = lab_name
        return lab_data
    return ""


def get_lab_name(user_obj):
    """Get the laboratory name for the user"""
    if Profile.objects.filter(user=user_obj).exists():
        profile_obj = Profile.objects.filter(user=user_obj).last()
        return profile_obj.get_lab_name()
    else:
        return ""
